import type { ICoachProviderPort } from "../../chat/application/ports";
import { CoachProviderError } from "../../chat/domain/errors";

export { CoachProviderError };

export interface OpenAiCoachProviderOptions {
  apiKey?: string;
  fetchFn?: typeof fetch;
}

export class OpenAiCoachProvider implements ICoachProviderPort {
  private readonly apiKey: string;
  private readonly fetchFn: typeof fetch;

  constructor(options: OpenAiCoachProviderOptions = {}) {
    this.apiKey = options.apiKey || process.env.OPENAI_API_KEY || "";
    this.fetchFn = options.fetchFn || fetch;
  }

  async generateCoachResponse(
    contextPrompt: string,
    recentMessages: { role: string; content: string }[]
  ): Promise<string> {
    if (!this.apiKey) {
      throw new CoachProviderError(
        "El servicio del entrenador no está disponible en este momento. Intenta de nuevo más tarde.",
        503,
        "MISSING_API_KEY"
      );
    }

    const payload = {
      model: "gpt-6-luna",
      reasoning_effort: "high",
      messages: [
        { role: "system", content: contextPrompt },
        ...recentMessages.map((m) => ({
          role: m.role as "user" | "assistant" | "system",
          content: m.content,
        })),
      ],
    };

    let res: Response;
    try {
      res = await this.fetchFn("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        cache: "no-store",
      });
    } catch (networkErr) {
      throw new CoachProviderError(
        `Error de red al conectar con el proveedor: ${networkErr instanceof Error ? networkErr.message : String(networkErr)}`,
        502,
        "NETWORK_ERROR"
      );
    }

    if (!res.ok) {
      let errorMessage = `OpenAI respondió con código ${res.status}`;
      try {
        const errorBody = (await res.json()) as { error?: { message?: string } };
        if (errorBody?.error?.message) {
          errorMessage = errorBody.error.message;
        }
      } catch {
        // Non-JSON response
      }

      throw new CoachProviderError(errorMessage, res.status, `OPENAI_HTTP_${res.status}`);
    }

    let data: { choices?: { message?: { content?: string } }[] };
    try {
      data = (await res.json()) as typeof data;
    } catch {
      throw new CoachProviderError("Respuesta no válida del proveedor de inferencia", 502, "INVALID_RESPONSE_JSON");
    }

    const reply = data.choices?.[0]?.message?.content?.trim();
    if (!reply) {
      throw new CoachProviderError("El proveedor de inferencia no devolvió contenido", 502, "EMPTY_CHOICE");
    }

    return reply;
  }
}
