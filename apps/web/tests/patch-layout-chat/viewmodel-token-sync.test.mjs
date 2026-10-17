import test from "node:test";
import assert from "node:assert";
import { useCoachConversationLogic } from "../../hooks/useCoachConversation.ts";

function createMockFetch(handlers = {}) {
  return async function mockFetch(url, options = {}) {
    const urlStr = typeof url === "string" ? url : url.toString();
    const method = options.method || "GET";

    if (handlers[`${method} ${urlStr}`]) {
      return handlers[`${method} ${urlStr}`](urlStr, options);
    }

    for (const key of Object.keys(handlers)) {
      const [hMethod, ...patternParts] = key.split(" ");
      const pattern = patternParts.join(" ");
      if (hMethod === method && new RegExp(pattern).test(urlStr)) {
        return handlers[key](urlStr, options);
      }
    }

    return new Response(JSON.stringify({ ok: false, error: "Not found in mock" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  };
}

test("REQ-005 / P05: Sincronización reactiva de accessToken en CoachConversationViewModel y recarga con cabecera Bearer", async () => {
  let capturedHeaders = null;
  let callCount = 0;

  const mockFetch = createMockFetch({
    "GET /api/conversations": async (_url, options) => {
      callCount++;
      capturedHeaders = options.headers || {};
      return new Response(
        JSON.stringify({
          ok: true,
          conversations: [
            { id: "conv-remote-1", title: "Conversación remota", revision: 1, updatedAt: "2026-10-17T12:00:00Z" },
          ],
          total: 1,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
  });

  const vm = useCoachConversationLogic({
    accessToken: null,
    customFetch: mockFetch,
  });

  // Verify setAccessToken method exists
  assert.strictEqual(
    typeof vm.setAccessToken,
    "function",
    "CoachConversationViewModel debe implementar setAccessToken(token: string | null)"
  );

  // 1. Initial call with null token: no Authorization header
  await vm.loadConversations();
  assert.strictEqual(callCount, 1);
  assert.strictEqual(capturedHeaders["Authorization"], undefined, "Con token null no debe enviarse Authorization");
  assert.strictEqual(vm.conversations.length, 1);

  // 2. Reactive update with valid JWT token
  vm.setAccessToken("jwt-token-valido-123");
  await vm.loadConversations();
  assert.strictEqual(callCount, 2);
  assert.strictEqual(
    capturedHeaders["Authorization"],
    "Bearer jwt-token-valido-123",
    "Tras setAccessToken, peticiones deben incluir 'Bearer jwt-token-valido-123'"
  );

  // 3. Reset to null
  vm.setAccessToken(null);
  await vm.loadConversations();
  assert.strictEqual(callCount, 3);
  assert.strictEqual(capturedHeaders["Authorization"], undefined, "Tras volver a null, se retira cabecera Authorization");
});

test("REQ-006 / P06: Captura resiliente de respuestas no exitosas (401 y 500) y caídas de red en loadConversations() sin crash", async () => {
  // Caso A: HTTP 401 Unauthorized
  const mockFetch401 = createMockFetch({
    "GET /api/conversations": async () => {
      return new Response(
        JSON.stringify({ ok: false, error: "No autorizado" }),
        { status: 401, headers: { "Content-Type": "application/json" } }
      );
    },
  });

  const vm401 = useCoachConversationLogic({
    accessToken: null,
    customFetch: mockFetch401,
  });

  await assert.doesNotReject(
    async () => {
      await vm401.loadConversations();
    },
    "loadConversations no debe lanzar excepción ante HTTP 401"
  );
  assert.strictEqual(vm401.isLoading, false, "isLoading debe finalizar en false ante 401");
  assert.strictEqual(vm401.error, null, "error debe permanecer null en 401 para permitir fallback local no-bloqueante");

  // Caso B: HTTP 500 Internal Server Error
  const mockFetch500 = createMockFetch({
    "GET /api/conversations": async () => {
      return new Response(
        JSON.stringify({ ok: false, error: "Error interno del servidor de base de datos" }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    },
  });

  const vm500 = useCoachConversationLogic({
    accessToken: "token-expirado",
    customFetch: mockFetch500,
  });

  await assert.doesNotReject(
    async () => {
      await vm500.loadConversations();
    },
    "loadConversations no debe lanzar excepción ante HTTP 500"
  );
  assert.strictEqual(vm500.isLoading, false, "isLoading debe finalizar en false ante 500");
  assert.match(
    vm500.error || "",
    /Error interno del servidor|500/,
    "error debe capturar el mensaje amigable de error del servidor"
  );

  // Caso C: Fallo de red (Network disconnection)
  const mockFetchNetworkErr = async () => {
    throw new Error("Failed to fetch: Connection refused");
  };

  const vmNet = useCoachConversationLogic({
    customFetch: mockFetchNetworkErr,
  });

  await assert.doesNotReject(
    async () => {
      await vmNet.loadConversations();
    },
    "loadConversations no debe lanzar excepción ante fallo de red"
  );
  assert.strictEqual(vmNet.isLoading, false, "isLoading debe finalizar en false ante fallo de red");
  assert.match(vmNet.error || "", /Connection refused/, "error debe registrar el mensaje de red");
});
