import { SupabaseIdentityService } from "@/lib/infra/auth/supabaseIdentityService";
import { SupabaseConversationRepository } from "@/lib/infra/chat/supabaseConversationRepository";
import { SupabaseHealthContext } from "@/lib/infra/health/supabaseHealthContext";
import { OpenAiCoachProvider } from "@/lib/infra/coach/openAiCoachProvider";
import { SendMessageUseCase } from "@/lib/chat/application/sendMessageUseCase";
import {
  ConcurrencyConflictError,
  HealthProfileNotLinkedError,
  NotFoundError,
  OperationLeaseActiveError,
  UnauthorizedError,
  ValidationError,
  CoachProviderError,
} from "@/lib/chat/domain/errors";
import { logTechnicalEvent } from "@/lib/infra/logging";

export const dynamic = "force-dynamic";

const NO_STORE_HEADERS = {
  "Cache-Control": "no-store",
};

export async function GET() {
  return Response.json(
    {
      ok: true,
      model: "gpt-6-luna",
      reasoning_effort: "high",
    },
    { headers: NO_STORE_HEADERS }
  );
}

export async function POST(request: Request) {
  const start = Date.now();

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    console.error("Missing OPENAI_API_KEY in environment");
    return Response.json(
      {
        ok: false,
        error: "El servicio del entrenador no está disponible en este momento. Intenta de nuevo más tarde.",
      },
      { status: 503, headers: NO_STORE_HEADERS }
    );
  }

  const authHeader = request.headers.get("Authorization");
  const identityService = new SupabaseIdentityService();
  let ownerId: string;
  try {
    const auth = await identityService.authenticateUser(authHeader);
    ownerId = auth.userId;
  } catch (err) {
    const durationMs = Date.now() - start;
    logTechnicalEvent({
      statusCode: 401,
      durationMs,
      result: "unauthorized",
      code: err instanceof UnauthorizedError ? err.code : "UNAUTHORIZED",
    });
    return Response.json(
      { ok: false, error: "Sesión no válida o no autenticada" },
      { status: 401, headers: NO_STORE_HEADERS }
    );
  }

  let payload: Record<string, unknown> = {};
  try {
    payload = (await request.json()) as Record<string, unknown>;
  } catch {
    return Response.json(
      { ok: false, error: "JSON inválido" },
      { status: 400, headers: NO_STORE_HEADERS }
    );
  }

  // Extracción y mapeo de campos con soporte retrocompatible
  let content = typeof payload.content === "string" ? payload.content : "";
  if (!content && Array.isArray(payload.messages) && payload.messages.length > 0) {
    const last = payload.messages[payload.messages.length - 1];
    if (last && typeof last.content === "string") {
      content = last.content;
    }
  }

  const conversationId =
    typeof payload.conversation_id === "string"
      ? payload.conversation_id
      : typeof payload.conversationId === "string"
        ? payload.conversationId
        : "";

  const operationId =
    typeof payload.operation_id === "string"
      ? payload.operation_id
      : typeof payload.operationId === "string"
        ? payload.operationId
        : "";

  const expectedRevision =
    typeof payload.expected_revision === "number"
      ? payload.expected_revision
      : typeof payload.expectedRevision === "number"
        ? payload.expectedRevision
        : 1;

  if (!content.trim()) {
    return Response.json(
      { ok: false, error: "Falta el mensaje" },
      { status: 400, headers: NO_STORE_HEADERS }
    );
  }

  if (content.length > 4000) {
    return Response.json(
      { ok: false, error: "El mensaje supera el límite máximo permitido de 4000 caracteres" },
      { status: 400, headers: NO_STORE_HEADERS }
    );
  }

  if (!conversationId) {
    return Response.json(
      { ok: false, error: "Falta el identificador de conversación" },
      { status: 400, headers: NO_STORE_HEADERS }
    );
  }

  if (!operationId) {
    return Response.json(
      { ok: false, error: "Falta el identificador de operación" },
      { status: 400, headers: NO_STORE_HEADERS }
    );
  }

  const repo = new SupabaseConversationRepository();
  const healthPort = new SupabaseHealthContext();
  const coachPort = new OpenAiCoachProvider({ apiKey });

  const useCase = new SendMessageUseCase({
    conversationRepository: repo,
    healthContextPort: healthPort,
    coachProviderPort: coachPort,
  });

  try {
    const result = await useCase.execute({
      ownerId,
      conversationId,
      content,
      operationId,
      expectedRevision,
    });

    const durationMs = Date.now() - start;
    logTechnicalEvent({
      operationId,
      conversationId,
      statusCode: 200,
      durationMs,
      result: "success",
    });

    return Response.json(
      {
        ok: true,
        message: result.assistantMessage,
        revision: result.conversation.revision,
        cached: result.cached,
        reply: result.assistantMessage.content,
        model: "gpt-6-luna",
      },
      { status: 200, headers: NO_STORE_HEADERS }
    );
  } catch (err) {
    const durationMs = Date.now() - start;

    if (err instanceof HealthProfileNotLinkedError) {
      logTechnicalEvent({
        operationId,
        conversationId,
        statusCode: 403,
        durationMs,
        result: "forbidden",
        code: err.code,
      });
      return Response.json(
        { ok: false, error: err.message },
        { status: 403, headers: NO_STORE_HEADERS }
      );
    }

    if (err instanceof ConcurrencyConflictError || err instanceof OperationLeaseActiveError) {
      logTechnicalEvent({
        operationId,
        conversationId,
        statusCode: 409,
        durationMs,
        result: "conflict",
        code: err.code,
      });
      return Response.json(
        { ok: false, error: err.message, code: err.code },
        { status: 409, headers: NO_STORE_HEADERS }
      );
    }

    if (err instanceof NotFoundError) {
      logTechnicalEvent({
        operationId,
        conversationId,
        statusCode: 404,
        durationMs,
        result: "not_found",
        code: err.code,
      });
      return Response.json(
        { ok: false, error: err.message },
        { status: 404, headers: NO_STORE_HEADERS }
      );
    }

    if (err instanceof ValidationError) {
      logTechnicalEvent({
        operationId,
        conversationId,
        statusCode: 400,
        durationMs,
        result: "error",
        code: err.code,
      });
      return Response.json(
        { ok: false, error: err.message },
        { status: 400, headers: NO_STORE_HEADERS }
      );
    }

    if (err instanceof CoachProviderError) {
      logTechnicalEvent({
        operationId,
        conversationId,
        statusCode: err.statusCode,
        durationMs,
        result: "error",
        code: err.code,
      });
      return Response.json(
        { ok: false, error: err.message },
        { status: err.statusCode >= 500 ? 502 : err.statusCode, headers: NO_STORE_HEADERS }
      );
    }

    const errorMsg = err instanceof Error ? err.message : "Error inesperado en el servidor";
    logTechnicalEvent({
      operationId,
      conversationId,
      statusCode: 500,
      durationMs,
      result: "error",
      code: "INTERNAL_ERROR",
    });

    return Response.json(
      { ok: false, error: errorMsg },
      { status: 500, headers: NO_STORE_HEADERS }
    );
  }
}
