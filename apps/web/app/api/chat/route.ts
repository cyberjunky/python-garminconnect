import { NextResponse } from "next/server";
import { conditionPrompt, loadCondition } from "@/lib/condition";
import { pickModel, serverModelCatalog } from "@/lib/openaiModels";

export const dynamic = "force-dynamic";

type IncomingMessage = { role?: string; content?: string };

const MAX_MESSAGES = 12;
const MAX_CHARS = 4000;

function sanitize(messages: IncomingMessage[]) {
  return messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({
      role: message.role as "user" | "assistant",
      content: String(message.content || "").slice(0, MAX_CHARS),
    }))
    .filter((message) => message.content.trim().length > 0)
    .slice(-MAX_MESSAGES);
}

export async function GET() {
  const configured = Boolean(process.env.OPENAI_API_KEY);
  const { models, defaultModel } = await serverModelCatalog();
  return NextResponse.json({
    ok: true,
    configured,
    models,
    defaultModel,
    modelsFromAccount: configured && models.length > 4,
  });
}

const FIXED_TEMP_MODELS = /^(o\d|gpt-5|gpt-6|chatgpt-)/i;

async function executeOpenAiChatCompletion(
  apiKey: string,
  model: string,
  messages: { role: "system" | "user" | "assistant"; content: string }[]
) {
  const initialUseTemp = !FIXED_TEMP_MODELS.test(model);

  const sendRequest = async (useTemp: boolean) => {
    const payload: {
      model: string;
      messages: { role: string; content: string }[];
      temperature?: number;
    } = {
      model,
      messages,
    };
    if (useTemp) {
      payload.temperature = 0.4;
    }

    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    let body: {
      error?: { message?: string };
      choices?: { message?: { content?: string } }[];
    } = {};
    try {
      body = (await res.json()) as typeof body;
    } catch {
      // non-JSON body
    }

    return { res, body, usedTemp: useTemp };
  };

  let outcome = await sendRequest(initialUseTemp);

  // Reintento automático resiliente si falla por incompatibilidad de temperature
  if (!outcome.res.ok && outcome.usedTemp) {
    const errorDetails = `${outcome.body.error?.message || ""} ${outcome.res.statusText || ""}`;
    if (/temperature/i.test(errorDetails)) {
      outcome = await sendRequest(false);
    }
  }

  return outcome;
}

export async function POST(request: Request) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    console.error("Missing OPENAI_API_KEY in environment");
    return NextResponse.json(
      { ok: false, error: "El servicio del entrenador no está disponible en este momento. Intenta de nuevo más tarde." },
      { status: 503 }
    );
  }

  let payload: { messages?: IncomingMessage[]; model?: string };
  try {
    payload = (await request.json()) as { messages?: IncomingMessage[]; model?: string };
  } catch {
    return NextResponse.json({ ok: false, error: "JSON inválido" }, { status: 400 });
  }

  const messages = sanitize(payload.messages || []);
  if (messages.length === 0 || messages[messages.length - 1].role !== "user") {
    return NextResponse.json({ ok: false, error: "Falta el mensaje" }, { status: 400 });
  }

  let system: string;
  try {
    const condition = await loadCondition();
    system = conditionPrompt(condition);
  } catch (err) {
    const error = err instanceof Error ? err.message : "No se pudo leer la condición";
    return NextResponse.json({ ok: false, error }, { status: 502 });
  }

  const catalog = await serverModelCatalog();
  const model = pickModel(payload.model, catalog.models, catalog.defaultModel);
  try {
    const chatMessages: { role: "system" | "user" | "assistant"; content: string }[] = [
      { role: "system", content: system },
      ...messages,
    ];
    const outcome = await executeOpenAiChatCompletion(apiKey, model, chatMessages);
    if (!outcome.res.ok) {
      return NextResponse.json(
        { ok: false, error: outcome.body.error?.message || `OpenAI respondió ${outcome.res.status}` },
        { status: 502 }
      );
    }
    const reply = outcome.body.choices?.[0]?.message?.content?.trim();
    if (!reply) {
      return NextResponse.json({ ok: false, error: "OpenAI no devolvió texto" }, { status: 502 });
    }
    return NextResponse.json({ ok: true, reply, model });
  } catch (err) {
    const error = err instanceof Error ? err.message : "No se pudo consultar OpenAI";
    return NextResponse.json({ ok: false, error }, { status: 502 });
  }
}
