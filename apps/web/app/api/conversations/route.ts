import { SupabaseIdentityService } from "@/lib/infra/auth/supabaseIdentityService";
import { SupabaseConversationRepository } from "@/lib/infra/chat/supabaseConversationRepository";
import { ListConversationsUseCase } from "@/lib/chat/application/listConversationsUseCase";
import { CreateConversationUseCase } from "@/lib/chat/application/createConversationUseCase";
import { UnauthorizedError } from "@/lib/chat/domain/errors";
import { logTechnicalEvent } from "@/lib/infra/logging";

export const dynamic = "force-dynamic";

const NO_STORE_HEADERS = {
  "Cache-Control": "no-store",
};

export async function GET(request: Request) {
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

  const { searchParams } = new URL(request.url);
  const limitParam = searchParams.get("limit");
  const offsetParam = searchParams.get("offset");

  const limit = limitParam ? parseInt(limitParam, 10) : 20;
  const offset = offsetParam ? parseInt(offsetParam, 10) : 0;

  const repo = new SupabaseConversationRepository();
  const useCase = new ListConversationsUseCase(repo);

  try {
    const result = await useCase.execute({ ownerId, limit, offset });
    const durationMs = Date.now() - start;
    logTechnicalEvent({
      statusCode: 200,
      durationMs,
      result: "success",
    });
    return Response.json(
      { ok: true, conversations: result.conversations, total: result.total },
      { status: 200, headers: NO_STORE_HEADERS }
    );
  } catch (err) {
    const durationMs = Date.now() - start;
    const errorMsg = err instanceof Error ? err.message : "Error al listar conversaciones";
    logTechnicalEvent({
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

export async function POST(request: Request) {
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

  let body: { title?: string } = {};
  try {
    body = (await request.json()) as { title?: string };
  } catch {
    // Body vacío o no-JSON usa título por defecto
  }

  const repo = new SupabaseConversationRepository();
  const useCase = new CreateConversationUseCase(repo);

  try {
    const conversation = await useCase.execute({ ownerId, title: body.title });
    const durationMs = Date.now() - start;
    logTechnicalEvent({
      conversationId: conversation.id,
      statusCode: 201,
      durationMs,
      result: "success",
    });
    return Response.json(
      { ok: true, conversation },
      { status: 201, headers: NO_STORE_HEADERS }
    );
  } catch (err) {
    const durationMs = Date.now() - start;
    const errorMsg = err instanceof Error ? err.message : "Error al crear conversación";
    logTechnicalEvent({
      statusCode: 400,
      durationMs,
      result: "error",
      code: "BAD_REQUEST",
    });
    return Response.json(
      { ok: false, error: errorMsg },
      { status: 400, headers: NO_STORE_HEADERS }
    );
  }
}
