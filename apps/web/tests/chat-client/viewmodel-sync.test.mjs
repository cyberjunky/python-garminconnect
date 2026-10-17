import test from "node:test";
import assert from "node:assert";
import { useCoachConversationLogic } from "../../hooks/useCoachConversation.ts";

// Helper mock para simular respuestas de API
function createMockFetch(handlers = {}) {
  return async function mockFetch(url, options = {}) {
    const urlStr = typeof url === "string" ? url : url.toString();
    const method = options.method || "GET";

    if (handlers[`${method} ${urlStr}`]) {
      return handlers[`${method} ${urlStr}`](urlStr, options);
    }

    // Handlers con patrones regex
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

test("REQ-006 & REQ-008 / P06 & P08: Envío exitoso guarda mensaje, muestra estado 'Guardado' y agrega respuesta del coach", async () => {
  let chatPayload = null;
  const mockFetch = createMockFetch({
    "POST /api/chat": async (_url, options) => {
      chatPayload = JSON.parse(options.body);
      return new Response(
        JSON.stringify({
          ok: true,
          message: {
            id: "msg-asst-1",
            conversationId: "conv-1",
            ownerId: "user-1",
            sequence: 2,
            role: "assistant",
            content: "Respuesta del coach sobre entrenamiento",
            createdAt: new Date().toISOString(),
          },
          revision: 2,
          reply: "Respuesta del coach sobre entrenamiento",
          model: "gpt-6-luna",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
  });

  const vm = useCoachConversationLogic({
    conversationId: "conv-1",
    initialRevision: 1,
    accessToken: "test-token",
    customFetch: mockFetch,
  });

  vm.setDraft("¿Cuál es mi plan de hoy?");
  const sent = await vm.sendMessage();

  assert.strictEqual(sent, true, "sendMessage debe retornar true en caso de éxito");
  assert.strictEqual(vm.saveStatus, "saved", "El estado de guardado debe ser 'saved'");
  assert.strictEqual(vm.messages.length, 2, "Debe haber 2 mensajes (usuario + asistente)");
  assert.strictEqual(vm.messages[0].role, "user");
  assert.strictEqual(vm.messages[0].status, "saved", "Mensaje de usuario debe tener status 'saved'");
  assert.strictEqual(vm.messages[1].role, "assistant");
  assert.strictEqual(vm.messages[1].status, "saved");
  assert.strictEqual(vm.draft, "", "El borrador debe haberse limpiado tras el envío exitoso");
  assert.strictEqual(vm.conversation?.revision, 2, "La revisión de la conversación debe avanzar a 2");

  assert.ok(chatPayload.operationId, "Debe enviar operationId opaco");
  assert.strictEqual(chatPayload.conversationId, "conv-1");
  assert.strictEqual(chatPayload.expectedRevision, 1);
});

test("REQ-008 / P08: Fallo de red o 500 no marca 'Guardado', preserva mensaje y permite reintento", async () => {
  const mockFetch = createMockFetch({
    "POST /api/chat": async () => {
      return new Response(
        JSON.stringify({ ok: false, error: "Fallo de conexión con el servidor" }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    },
  });

  const vm = useCoachConversationLogic({
    conversationId: "conv-1",
    initialRevision: 1,
    accessToken: "test-token",
    customFetch: mockFetch,
  });

  vm.setDraft("Pregunta de prueba");
  const sent = await vm.sendMessage();

  assert.strictEqual(sent, false, "sendMessage debe retornar false ante fallo");
  assert.strictEqual(vm.saveStatus, "error", "Estado de guardado debe ser 'error'");
  assert.notStrictEqual(vm.saveStatus, "saved", "No debe anunciarse como 'saved' ante fallo");
  assert.strictEqual(vm.messages.length, 1, "Mensaje de usuario debe permanecer en la lista");
  assert.strictEqual(vm.messages[0].status, "error", "Mensaje de usuario debe reflejar estado de error");
  assert.ok(vm.error, "Debe contener mensaje de error visible");
});

test("REQ-009 / P09: Reintento utiliza el mismo operationId (idempotencia)", async () => {
  const capturedOperationIds = [];

  const mockFetch = createMockFetch({
    "POST /api/chat": async (_url, options) => {
      const payload = JSON.parse(options.body);
      capturedOperationIds.push(payload.operationId);

      if (capturedOperationIds.length === 1) {
        // Primer intento falla
        return new Response(
          JSON.stringify({ ok: false, error: "Timeout en proveedor" }),
          { status: 504, headers: { "Content-Type": "application/json" } }
        );
      }

      // Segundo intento tiene éxito
      return new Response(
        JSON.stringify({
          ok: true,
          message: {
            id: "msg-asst-2",
            conversationId: "conv-1",
            sequence: 2,
            role: "assistant",
            content: "Respuesta al reintento",
            createdAt: new Date().toISOString(),
          },
          revision: 2,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
  });

  const vm = useCoachConversationLogic({
    conversationId: "conv-1",
    initialRevision: 1,
    accessToken: "test-token",
    customFetch: mockFetch,
  });

  vm.setDraft("Pregunta para reintentar");
  await vm.sendMessage();

  assert.strictEqual(vm.saveStatus, "error");
  const firstOpId = capturedOperationIds[0];
  assert.ok(firstOpId, "Debe haberse generado un operationId");

  // Ejecutamos reintento
  const retrySuccess = await vm.retryLastMessage();

  assert.strictEqual(retrySuccess, true);
  assert.strictEqual(capturedOperationIds.length, 2, "Debe haberse realizado un segundo llamado");
  assert.strictEqual(
    capturedOperationIds[1],
    firstOpId,
    "El reintento debe reutilizar exactamente el mismo operationId para garantizar idempotencia (REQ-009)"
  );
  assert.strictEqual(vm.saveStatus, "saved");
});

test("REQ-010 / P10: Conflicto 409 refresca historial, actualiza revisión y conserva borrador/mensaje", async () => {
  let refreshedMessages = false;

  const mockFetch = createMockFetch({
    "POST /api/chat": async () => {
      return new Response(
        JSON.stringify({
          ok: false,
          code: "CONCURRENCY_CONFLICT",
          error: "Conflicto de concurrencia: revisión esperada 1, actual 3",
        }),
        { status: 409, headers: { "Content-Type": "application/json" } }
      );
    },
    "GET /api/conversations/conv-1/messages": async () => {
      refreshedMessages = true;
      return new Response(
        JSON.stringify({
          ok: true,
          messages: [
            { id: "m1", sequence: 1, role: "user", content: "Mensaje de otro cliente" },
            { id: "m2", sequence: 2, role: "assistant", content: "Respuesta de otro cliente" },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
    "GET /api/conversations": async () => {
      return new Response(
        JSON.stringify({
          ok: true,
          conversations: [{ id: "conv-1", revision: 3, title: "Chat con nueva revisión" }],
          total: 1,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
  });

  const vm = useCoachConversationLogic({
    conversationId: "conv-1",
    initialRevision: 1,
    accessToken: "test-token",
    customFetch: mockFetch,
  });

  vm.setDraft("Mi mensaje concurrente");
  const result = await vm.sendMessage();

  assert.strictEqual(result, false, "Envío debe retornar false ante 409");
  assert.strictEqual(vm.saveStatus, "conflict", "saveStatus debe marcar 'conflict'");
  assert.strictEqual(vm.hasConflict, true, "hasConflict debe ser true");
  assert.ok(refreshedMessages, "Ante 409 debe refrescar mensajes del servidor");
  assert.strictEqual(vm.conversation?.revision, 3, "La revisión debe actualizarse a la del servidor");
  assert.strictEqual(vm.pendingRetryContent, "Mi mensaje concurrente", "El contenido del mensaje debe preservarse para reenvío");
});

test("REQ-007 / P07: Paginación carga siguientes páginas sin descartar conversaciones existentes ni truncar a 4", async () => {
  const allConversations = Array.from({ length: 35 }, (_, i) => ({
    id: `conv-${i + 1}`,
    title: `Conversación ${i + 1}`,
    revision: 1,
    updatedAt: new Date(Date.now() - i * 1000).toISOString(),
  }));

  const mockFetch = createMockFetch({
    "GET /api/conversations\\?limit=20&offset=0": async () => {
      return new Response(
        JSON.stringify({
          ok: true,
          conversations: allConversations.slice(0, 20),
          total: 35,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
    "GET /api/conversations\\?limit=20&offset=20": async () => {
      return new Response(
        JSON.stringify({
          ok: true,
          conversations: allConversations.slice(20, 35),
          total: 35,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
  });

  const vm = useCoachConversationLogic({
    accessToken: "test-token",
    customFetch: mockFetch,
  });

  await vm.loadConversations({ offset: 0, limit: 20 });
  assert.strictEqual(vm.conversations.length, 20, "Primera página debe tener 20 elementos");
  assert.strictEqual(vm.totalConversations, 35);

  // Cargar segunda página
  await vm.loadNextPage();
  assert.strictEqual(
    vm.conversations.length,
    35,
    "Al cargar la siguiente página debe tener los 35 elementos acumulados sin descartar los 20 anteriores (REQ-007)"
  );
  assert.ok(
    vm.conversations.length > 4,
    "El historial sincronizado no debe estar recortado a 4 como el legado"
  );
});
