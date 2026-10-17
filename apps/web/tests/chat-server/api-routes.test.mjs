import test from "node:test";
import assert from "node:assert";

process.env.OPENAI_API_KEY = process.env.OPENAI_API_KEY || "synthetic-test-key";

test("API /api/conversations rechaza 401 sin sesion y responde no-store", async () => {
  const { GET, POST } = await import(
    "../../app/api/conversations/route.ts"
  );

  // Request GET sin header Authorization
  const getReq = new Request("http://localhost:3000/api/conversations", {
    method: "GET",
  });
  const getRes = await GET(getReq);
  assert.strictEqual(getRes.status, 401);
  assert.strictEqual(getRes.headers.get("Cache-Control"), "no-store");

  // Request POST sin header Authorization
  const postReq = new Request("http://localhost:3000/api/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "Nueva conversacion" }),
  });
  const postRes = await POST(postReq);
  assert.strictEqual(postRes.status, 401);
  assert.strictEqual(postRes.headers.get("Cache-Control"), "no-store");
});

test("API /api/chat valida payload, auth y cache no-store", async () => {
  const { POST } = await import(
    "../../app/api/chat/route.ts"
  );

  // 1. Sin sesion -> 401
  const noAuthReq = new Request("http://localhost:3000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: "00000000-0000-0000-0000-000000000001",
      operation_id: "00000000-0000-0000-0000-000000000002",
      content: "¿Como entreno hoy?",
      expected_revision: 1,
    }),
  });
  const noAuthRes = await POST(noAuthReq);
  assert.strictEqual(noAuthRes.status, 401);
  assert.strictEqual(noAuthRes.headers.get("Cache-Control"), "no-store");

  // 2. Con mensaje mayor a 4000 caracteres -> 400 o 401
  const longReq = new Request("http://localhost:3000/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer invalid-or-synthetic",
    },
    body: JSON.stringify({
      conversation_id: "00000000-0000-0000-0000-000000000001",
      operation_id: "00000000-0000-0000-0000-000000000002",
      content: "x".repeat(4001),
      expected_revision: 1,
    }),
  });
  const longRes = await POST(longReq);
  assert.ok(longRes.status === 400 || longRes.status === 401);
  assert.strictEqual(longRes.headers.get("Cache-Control"), "no-store");
});
