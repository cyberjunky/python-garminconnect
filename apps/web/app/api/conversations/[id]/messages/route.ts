import { SupabaseIdentityService } from "@/lib/infra/auth/supabaseIdentityService";
import { SupabaseConversationRepository } from "@/lib/infra/chat/supabaseConversationRepository";
import { GetMessagesUseCase } from "@/lib/chat/application/getMessagesUseCase";
import { NotFoundError, UnauthorizedError } from "@/lib/chat/domain/errors";
import { logTechnicalEvent } from "@/lib/infra/logging";

export const dynamic = "force-dynamic";

const NO_STORE_HEADERS = {
  "Cache-Control": "no-store",
};

export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> }
) {
  const start = Date.now();
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

  const { id: conversationId } = await context.params;

  const repo = new SupabaseConversationRepository();
  const useCase = new GetMessagesUseCase(repo);

  try {
    const messages = await useCase.execute({ ownerId, conversationId });
    const durationMs = Date.now() - start;
    logTechnicalEvent({
      conversationId,
      statusCode: 200,
      durationMs,
      result: "success",
    });
    return Response.json(
      { ok: true, messages },
      { status: 200, headers: NO_STORE_HEADERS }
    );
  } catch (err) {
    const durationMs = Date.now() - start;
    if (err instanceof NotFoundError) {
      logTechnicalEvent({
        conversationId,
        statusCode: 404,
        durationMs,
        result: "not_found",
        code: "NOT_FOUND",
      });
      return Response.json(
        { ok: false, error: "Conversación no encontrada" },
        { status: 404, headers: NO_STORE_HEADERS }
      );
    }

    const errorMsg = err instanceof Error ? err.message : "Error al obtener mensajes";
    logTechnicalEvent({
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
