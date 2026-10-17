import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  mergeConversations,
  upsertChat,
  loadChats,
  saveChats,
  COACH_STORAGE_KEY,
  getSurvivingLegacyChats,
} from "../../lib/coachStorage.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");
const coachChatPath = path.join(webRoot, "components", "CoachChat.tsx");
const coachChatScreenPath = path.join(webRoot, "components", "CoachChatScreen.tsx");

// Mock de localStorage
function createMockStorage(initial = {}) {
  const store = new Map(Object.entries(initial));
  return {
    getItem(key) {
      return store.has(key) ? store.get(key) : null;
    },
    setItem(key, value) {
      store.set(key, String(value));
    },
    removeItem(key) {
      store.delete(key);
    },
    clear() {
      store.clear();
    },
    get size() {
      return store.size;
    },
  };
}

test("REQ-007 / P07: Función pura mergeConversations unifica, deduplica por ID y ordena descendentemente por fecha", () => {
  assert.strictEqual(
    typeof mergeConversations,
    "function",
    "coachStorage.ts debe exportar la función mergeConversations(remote, local)"
  );

  const remote = [
    { id: "c-1", title: "Rutina carrera Z2", updatedAt: "2026-10-17T10:00:00Z" },
    { id: "c-2", title: "Nutrición pre-competencia", updatedAt: "2026-10-16T15:00:00Z" },
  ];

  const local = [
    {
      id: "c-1", // Duplicado de remote
      title: "Rutina carrera Z2 (local)",
      updatedAt: "2026-10-17T09:30:00Z",
      messages: [{ role: "user", content: "mensaje" }],
    },
    {
      id: "c-3", // Superviviente local único
      title: "Plan de natación aguas abiertas",
      updatedAt: "2026-10-17T11:30:00Z", // Más reciente que c-1
      messages: [{ role: "user", content: "mensaje natación" }],
    },
    {
      id: "c-4", // Superviviente local sin título explícito
      title: "",
      updatedAt: "2026-10-15T08:00:00Z",
      messages: [{ role: "user", content: "pregunta" }],
    },
  ];

  const merged = mergeConversations(remote, local);

  // Deduplicación: exactamente 4 items (c-3, c-1, c-2, c-4)
  assert.strictEqual(merged.length, 4, "Debe haber exactamente 4 conversaciones unificadas");

  // Orden cronológico descendente: c-3 (11:30) -> c-1 (10:00) -> c-2 (16-15:00) -> c-4 (15-08:00)
  assert.strictEqual(merged[0].id, "c-3", "Primera debe ser la más reciente (c-3 local)");
  assert.strictEqual(merged[0].isLocal, true);
  assert.strictEqual(merged[0].title, "Plan de natación aguas abiertas");

  assert.strictEqual(merged[1].id, "c-1", "Segunda debe ser c-1 remoto prevaleciente");
  assert.strictEqual(merged[1].isLocal, false);
  assert.strictEqual(merged[1].title, "Rutina carrera Z2");

  assert.strictEqual(merged[2].id, "c-2", "Tercera debe ser c-2 remoto");
  assert.strictEqual(merged[2].isLocal, false);

  assert.strictEqual(merged[3].id, "c-4", "Cuarta debe ser c-4 local");
  assert.strictEqual(merged[3].isLocal, true);
  assert.ok(merged[3].title.length > 0, "c-4 debe tener un título amigable por defecto");

  // Verificación de integración en archivos de componentes
  const coachChatContent = fs.readFileSync(coachChatPath, "utf-8");
  assert.match(
    coachChatContent,
    /mergeConversations/,
    "CoachChat.tsx debe utilizar mergeConversations para unificar historial en Inicio"
  );
  assert.match(
    coachChatContent,
    /getSurvivingLegacyChats/,
    "CoachChat.tsx debe leer conversaciones locales supervivientes con getSurvivingLegacyChats"
  );

  const coachChatScreenContent = fs.readFileSync(coachChatScreenPath, "utf-8");
  assert.match(
    coachChatScreenContent,
    /mergeConversations/,
    "CoachChatScreen.tsx debe utilizar mergeConversations para la lista lateral de historial"
  );
});

test("REQ-008 / P08: Respaldo inmediato en localStorage con upsertChat al enviar y recibir mensajes", () => {
  const mockStorage = createMockStorage();
  const originalWindow = globalThis.window;

  // Mock global window and localStorage
  globalThis.window = {
    localStorage: mockStorage,
  };

  try {
    const testChat = {
      id: "conv-backup-1",
      title: "Consulta sobre intervalos",
      updatedAt: new Date().toISOString(),
      messages: [
        { role: "user", content: "Recomiéndame ritmo para 400m" },
        { role: "assistant", content: "Mantén ritmo de 1:28 a 1:30" },
      ],
    };

    upsertChat(testChat);

    const storedRaw = mockStorage.getItem(COACH_STORAGE_KEY);
    assert.ok(storedRaw, "localStorage['fitness-coach-chats'] debe contener datos tras upsertChat");

    const parsed = JSON.parse(storedRaw);
    assert.ok(Array.isArray(parsed));
    assert.strictEqual(parsed.length, 1);
    assert.strictEqual(parsed[0].id, "conv-backup-1");
    assert.strictEqual(parsed[0].title, "Consulta sobre intervalos");
    assert.strictEqual(parsed[0].messages.length, 2);

    // Verificación de código en CoachChatScreen.tsx
    const coachChatScreenContent = fs.readFileSync(coachChatScreenPath, "utf-8");
    assert.match(
      coachChatScreenContent,
      /upsertChat/,
      "CoachChatScreen.tsx debe invocar upsertChat para persistencia inmediata de respaldo"
    );
  } finally {
    globalThis.window = originalWindow;
  }
});
