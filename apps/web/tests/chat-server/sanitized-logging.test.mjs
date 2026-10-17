import test from "node:test";
import assert from "node:assert";

test("REQ-019 / P19: Logging tecnico registra solo metadatos opacos sin salud, emails, tokens ni texto", async () => {
  const { formatTechnicalLog, sanitizeForLogging } = await import(
    "../../lib/infra/logging.ts"
  );

  const sensitiveInput = {
    operationId: "op-12345-abcde",
    conversationId: "conv-98765-zyxwv",
    statusCode: 200,
    durationMs: 412,
    result: "success",
    // Datos sensibles que podrian colarse accidentalmente:
    userEmail: "atleta@example.com",
    token: "example-synthetic-bearer-token", // synthetic mock fixture token
    messageContent: "¿Por que mi HRV bajo a 32ms y mi sueno fue de 4 horas?",
    healthSnapshot: {
      hrv: 32,
      sleepH: 4.2,
      sleepScore: 45,
      vo2max: 52.4,
      acwr: 1.45,
      bbChange: -8,
      readinessZone: "ROJO",
    },
  };

  const sanitized = sanitizeForLogging(sensitiveInput);
  const formatted = formatTechnicalLog(sanitized);

  // Campos tecnicos permitidos presentes:
  assert.strictEqual(sanitized.operationId, "op-12345-abcde");
  assert.strictEqual(sanitized.conversationId, "conv-98765-zyxwv");
  assert.strictEqual(sanitized.statusCode, 200);
  assert.strictEqual(sanitized.durationMs, 412);
  assert.strictEqual(sanitized.result, "success");

  // NINGUN dato sensible presente en el objeto sanitizado ni en el string formateado:
  const logString = typeof formatted === "string" ? formatted : JSON.stringify(formatted);

  assert.strictEqual("userEmail" in sanitized, false);
  assert.strictEqual("token" in sanitized, false);
  assert.strictEqual("messageContent" in sanitized, false);
  assert.strictEqual("healthSnapshot" in sanitized, false);

  assert.doesNotMatch(logString, /atleta@example\.com/);
  assert.doesNotMatch(logString, /secretpayload/);
  assert.doesNotMatch(logString, /HRV|hrv|sueno|sleep|vo2max|acwr|Body Battery/i);
  assert.doesNotMatch(logString, /ROJO|VERDE|AMARILLO/);
  assert.doesNotMatch(logString, /Por que mi HRV bajo/);
});
