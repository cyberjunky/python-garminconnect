import test from "node:test";
import assert from "node:assert";

// We import directly from the TypeScript source via tsx or node loader, or test domain contracts
test("REQ-006 / P06: Mensaje nuevo maximo 4000 caracteres, rechaza excedente sin truncar", async () => {
  const { validateMessageContent, ValidationError, MAX_MESSAGE_CHARS } = await import(
    "../../lib/chat/domain/validation.ts"
  );

  assert.strictEqual(MAX_MESSAGE_CHARS, 4000);

  // Exactamente 4000 caracteres es valido
  const validExact = "a".repeat(4000);
  assert.strictEqual(validateMessageContent(validExact), validExact);

  // 1 caracter es valido
  assert.strictEqual(validateMessageContent("Hola"), "Hola");

  // Vacio o solo espacios rechaza
  assert.throws(
    () => validateMessageContent(""),
    (err) => err instanceof ValidationError && err.code === "EMPTY_MESSAGE"
  );
  assert.throws(
    () => validateMessageContent("    \n\t  "),
    (err) => err instanceof ValidationError && err.code === "EMPTY_MESSAGE"
  );

  // 4001 caracteres rechaza expresamente sin truncar en silencio
  const exceeding = "b".repeat(4001);
  assert.throws(
    () => validateMessageContent(exceeding),
    (err) => {
      assert.ok(err instanceof ValidationError);
      assert.strictEqual(err.code === "MESSAGE_TOO_LONG", true);
      assert.match(err.message, /4000/);
      return true;
    }
  );
});

test("REQ-018 / P18: selectContextWindow extrae los ultimos 12 mensajes sin alterar la coleccion completa", async () => {
  const { selectContextWindow, MAX_CONTEXT_MESSAGES } = await import(
    "../../lib/chat/domain/windowing.ts"
  );

  assert.strictEqual(MAX_CONTEXT_MESSAGES, 12);

  // 20 mensajes sintéticos en orden
  const fullHistory = Array.from({ length: 20 }, (_, i) => ({
    id: `msg-${i + 1}`,
    conversationId: "conv-1",
    ownerId: "user-1",
    sequence: i + 1,
    role: i % 2 === 0 ? "user" : "assistant",
    content: `Mensaje numero ${i + 1}`,
    createdAt: new Date(Date.now() + i * 1000).toISOString(),
  }));

  const windowPayload = selectContextWindow(fullHistory);

  // Debe contener exactamente los ultimos 12 mensajes (del 9 al 20)
  assert.strictEqual(windowPayload.length, 12);
  assert.strictEqual(windowPayload[0].sequence, 9);
  assert.strictEqual(windowPayload[11].sequence, 20);

  // La historia completa permanece inalterada con sus 20 mensajes
  assert.strictEqual(fullHistory.length, 20);
});

test("REQ-009 / REQ-010 / P09 / P10: Reglas de estado de operacion y lease de concurrencia", async () => {
  const { isOperationLeaseActive, canClaimOperation, OPERATION_LEASE_MS } = await import(
    "../../lib/chat/domain/operation.ts"
  );

  assert.strictEqual(OPERATION_LEASE_MS, 30_000);

  const now = new Date("2026-10-17T14:00:00.000Z");

  // Operacion completada no tiene lease activo y ya devolvio resultado
  const completedOp = {
    ownerId: "user-1",
    operationId: "op-1",
    conversationId: "conv-1",
    status: "completed",
    resultMessageId: "msg-res",
    leaseUntil: new Date("2026-10-17T14:00:30.000Z").toISOString(),
    createdAt: now.toISOString(),
  };
  assert.strictEqual(isOperationLeaseActive(completedOp, now), false);

  // Operacion in_progress con lease vigente
  const inProgressActive = {
    ...completedOp,
    status: "in_progress",
    leaseUntil: new Date("2026-10-17T14:00:25.000Z").toISOString(),
  };
  assert.strictEqual(isOperationLeaseActive(inProgressActive, now), true);
  // No puede reclamarse concurrentemente mientras lease este activo
  assert.strictEqual(canClaimOperation(inProgressActive, now), false);

  // Operacion in_progress con lease expirado
  const inProgressExpired = {
    ...completedOp,
    status: "in_progress",
    leaseUntil: new Date("2026-10-17T13:59:50.000Z").toISOString(),
  };
  assert.strictEqual(isOperationLeaseActive(inProgressExpired, now), false);
  // Lease expirado puede reclamarse para reintento o rescate
  assert.strictEqual(canClaimOperation(inProgressExpired, now), true);
});
