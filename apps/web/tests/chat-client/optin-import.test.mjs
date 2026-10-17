import test from "node:test";
import assert from "node:assert";
import {
  COACH_STORAGE_KEY,
  getSurvivingLegacyChats,
  computeChatDigest,
  executeOptInImport,
} from "../../lib/coachStorage.ts";

function createMockLocalStorage(initialData = {}) {
  const store = new Map(Object.entries(initialData));
  return {
    getItem: (key) => store.get(key) ?? null,
    setItem: (key, val) => store.set(key, String(val)),
    removeItem: (key) => store.delete(key),
    clear: () => store.clear(),
    getRawCopy: (key) => store.get(key) ?? null,
  };
}

test("REQ-011 / P11: getSurvivingLegacyChats lee todas las conversaciones sin recortar a 4", () => {
  const tenChats = Array.from({ length: 10 }, (_, i) => ({
    id: `legacy-${i + 1}`,
    title: `Chat legado ${i + 1}`,
    updatedAt: new Date().toISOString(),
    messages: [{ role: "user", content: `Mensaje ${i + 1}` }],
  }));

  const mockStorage = createMockLocalStorage({
    [COACH_STORAGE_KEY]: JSON.stringify(tenChats),
  });

  const surviving = getSurvivingLegacyChats(mockStorage);
  assert.strictEqual(
    surviving.length,
    10,
    "getSurvivingLegacyChats debe devolver las 10 conversaciones sin recortar al límite 4 de loadChats()"
  );
});

test("REQ-011 / P11: computeChatDigest genera hash determinista reproducible según contenido", () => {
  const chatA = {
    id: "chat-1",
    messages: [
      { role: "user", content: "Hola entrenador" },
      { role: "assistant", content: "¡Hola! ¿Cómo te sientes?" },
    ],
  };

  const chatB = {
    id: "chat-2",
    messages: [
      { role: "user", content: "Hola entrenador" },
      { role: "assistant", content: "¡Hola! ¿Cómo te sientes?" },
    ],
  };

  const chatDiff = {
    id: "chat-1",
    messages: [
      { role: "user", content: "Mensaje modificado" },
    ],
  };

  const digestA = computeChatDigest(chatA);
  const digestB = computeChatDigest(chatB);
  const digestDiff = computeChatDigest(chatDiff);

  assert.strictEqual(digestA, digestB, "Mismo contenido debe generar exactamente el mismo digest");
  assert.notStrictEqual(digestA, digestDiff, "Contenido diferente debe generar digest diferente");
  assert.strictEqual(typeof digestA, "string");
  assert.ok(digestA.length >= 32, "El digest debe ser un hash criptográfico adecuado");
});

test("REQ-011 / P11: executeOptInImport exige confirmación explícita de cuenta y preserva localStorage byte a byte", async () => {
  const legacyChats = [
    {
      id: "leg-1",
      title: "Chat legado 1",
      updatedAt: "2026-10-10T10:00:00Z",
      messages: [{ role: "user", content: "Pregunta 1" }],
    },
    {
      id: "leg-2",
      title: "Chat legado 2",
      updatedAt: "2026-10-11T10:00:00Z",
      messages: [{ role: "user", content: "Pregunta 2" }],
    },
  ];

  const rawJson = JSON.stringify(legacyChats);
  const mockStorage = createMockLocalStorage({
    [COACH_STORAGE_KEY]: rawJson,
  });

  // Intento 1: Sin confirmación debe abortar
  await assert.rejects(
    async () => {
      await executeOptInImport({
        targetUserId: "user-target-123",
        targetAccountLabel: "usuario@ejemplo.com",
        confirmed: false,
        storage: mockStorage,
      });
    },
    /confirmaci/i,
    "Debe rechazar la importación si confirmed es false"
  );

  // Verificar que localStorage no ha cambiado ni un byte
  assert.strictEqual(
    mockStorage.getItem(COACH_STORAGE_KEY),
    rawJson,
    "localStorage no debe modificarse ante rechazo"
  );

  // Intento 2: Con confirmación explícita
  let createdCount = 0;
  const mockFetch = async (url, options) => {
    if (url.includes("/api/conversations") && options.method === "POST") {
      createdCount++;
      return new Response(
        JSON.stringify({
          ok: true,
          conversation: { id: `server-conv-${createdCount}`, revision: 1 },
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  };

  const report = await executeOptInImport({
    targetUserId: "user-target-123",
    targetAccountLabel: "usuario@ejemplo.com",
    confirmed: true,
    storage: mockStorage,
    customFetch: mockFetch,
    existingDigests: new Set(),
  });

  assert.strictEqual(report.total, 2);
  assert.strictEqual(report.imported, 2);
  assert.strictEqual(report.errors, 0);

  // Criterio no negociable: original en localStorage BYTE A BYTE EXACTO
  assert.strictEqual(
    mockStorage.getItem(COACH_STORAGE_KEY),
    rawJson,
    "localStorage original debe permanecer 100% íntegro e inalterado byte a byte tras la importación (REQ-011)"
  );
});

test("REQ-011 / P11: Mismo digest no duplica (idempotencia de snapshot)", async () => {
  const legacyChats = [
    {
      id: "leg-dup",
      title: "Chat ya importado",
      messages: [{ role: "user", content: "Mismo mensaje" }],
    },
  ];

  const digest = computeChatDigest(legacyChats[0]);
  const mockStorage = createMockLocalStorage({
    [COACH_STORAGE_KEY]: JSON.stringify(legacyChats),
  });

  let serverCall = false;
  const mockFetch = async () => {
    serverCall = true;
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  };

  // Pasamos el digest existente
  const report = await executeOptInImport({
    targetUserId: "user-target-123",
    targetAccountLabel: "usuario@ejemplo.com",
    confirmed: true,
    storage: mockStorage,
    customFetch: mockFetch,
    existingDigests: new Set([digest]),
  });

  assert.strictEqual(report.total, 1);
  assert.strictEqual(report.skipped, 1, "Debe omitir el chat que ya tiene el mismo digest");
  assert.strictEqual(report.imported, 0);
  assert.strictEqual(serverCall, false, "No debe realizar llamadas al servidor para snapshots ya importados");
});

test("REQ-012 / P12: Interrupción a mitad de lote emite informe por entrada y permite reanudar", async () => {
  const legacyChats = [
    { id: "c1", title: "Chat 1", messages: [{ role: "user", content: "Pregunta 1" }] },
    { id: "c2", title: "Chat 2", messages: [{ role: "user", content: "Pregunta 2" }] },
    { id: "c3", title: "Chat 3", messages: [{ role: "user", content: "Pregunta 3" }] },
  ];

  const mockStorage = createMockLocalStorage({
    [COACH_STORAGE_KEY]: JSON.stringify(legacyChats),
  });

  let callCount = 0;
  const mockFetch = async (url, options) => {
    if (url.includes("/api/conversations") && options.method === "POST") {
      callCount++;
      if (callCount === 2) {
        // Falla en el segundo elemento
        return new Response(
          JSON.stringify({ ok: false, error: "Network timeout" }),
          { status: 504, headers: { "Content-Type": "application/json" } }
        );
      }
      return new Response(
        JSON.stringify({ ok: true, conversation: { id: `conv-${callCount}` } }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      );
    }
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  };

  const report = await executeOptInImport({
    targetUserId: "user-target-123",
    targetAccountLabel: "usuario@ejemplo.com",
    confirmed: true,
    storage: mockStorage,
    customFetch: mockFetch,
  });

  assert.strictEqual(report.total, 3);
  assert.strictEqual(report.imported, 2, "Deben haberse importado c1 y c3");
  assert.strictEqual(report.errors, 1, "Debe haberse registrado 1 error en c2");
  assert.strictEqual(report.results.length, 3, "Debe haber resultado para cada entrada sin omisión silenciosa");
  assert.strictEqual(report.results[1].status, "error");
  assert.ok(report.results[1].error);
});

test("REQ-012 / P12: JSON inválido o corrupto en localStorage no lanza excepción y preserva fuente", async () => {
  const corruptedRaw = "[[{corrupt-json--!!";
  const mockStorage = createMockLocalStorage({
    [COACH_STORAGE_KEY]: corruptedRaw,
  });

  const surviving = getSurvivingLegacyChats(mockStorage);
  assert.deepStrictEqual(surviving, [], "JSON corrupto debe resultar en lista vacía de forma segura");

  const report = await executeOptInImport({
    targetUserId: "user-target-123",
    targetAccountLabel: "usuario@ejemplo.com",
    confirmed: true,
    storage: mockStorage,
  });

  assert.strictEqual(report.total, 0);
  assert.strictEqual(
    mockStorage.getItem(COACH_STORAGE_KEY),
    corruptedRaw,
    "La fuente corrupta no debe ser borrada ni alterada automáticamente (REQ-012)"
  );
});
