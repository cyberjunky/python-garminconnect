export type ChatMessage = { role: "user" | "assistant"; content: string };

export type StoredChat = {
  id: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
};

export const COACH_STORAGE_KEY = "fitness-coach-chats";
export const MAX_CHATS = 4;
const PENDING_PREFIX = "fitness-coach-pending:";

// Implementación pura de SHA-256 sin dependencias externas
function sha256Sync(ascii: string): string {
  function rightRotate(value: number, amount: number): number {
    return (value >>> amount) | (value << (32 - amount));
  }

  const maxWord = Math.pow(2, 32);
  const words: number[] = [];
  const asciiBitLength = ascii.length * 8;

  // Constantes de redondeo fraccionario
  const hash = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
  ];

  const k = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
  ];

  for (let i = 0; i < ascii.length; i++) {
    const charCode = ascii.charCodeAt(i);
    words[i >> 2] |= (charCode & 0xff) << ((3 - (i % 4)) * 8);
  }

  words[asciiBitLength >> 5] |= 0x80 << ((3 - ((asciiBitLength >> 3) % 4)) * 8);
  words[(((asciiBitLength + 64) >> 9) << 4) + 15] = asciiBitLength;

  const w = new Array<number>(64);
  for (let i = 0; i < words.length; i += 16) {
    let [a, b, c, d, e, f, g, h] = hash;

    for (let j = 0; j < 64; j++) {
      if (j < 16) {
        w[j] = words[i + j] | 0;
      } else {
        const gamma0 = rightRotate(w[j - 15], 7) ^ rightRotate(w[j - 15], 18) ^ (w[j - 15] >>> 3);
        const gamma1 = rightRotate(w[j - 2], 17) ^ rightRotate(w[j - 2], 19) ^ (w[j - 2] >>> 10);
        w[j] = (((w[j - 16] + gamma0) | 0) + ((w[j - 7] + gamma1) | 0)) | 0;
      }

      const s1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
      const ch = (e & f) ^ (~e & g);
      const temp1 = (((((h + s1) | 0) + ch) | 0) + ((k[j] + w[j]) | 0)) | 0;
      const s0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (s0 + maj) | 0;

      h = g;
      g = f;
      f = e;
      e = (d + temp1) | 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) | 0;
    }

    hash[0] = (hash[0] + a) | 0;
    hash[1] = (hash[1] + b) | 0;
    hash[2] = (hash[2] + c) | 0;
    hash[3] = (hash[3] + d) | 0;
    hash[4] = (hash[4] + e) | 0;
    hash[5] = (hash[5] + f) | 0;
    hash[6] = (hash[6] + g) | 0;
    hash[7] = (hash[7] + h) | 0;
  }

  let hex = "";
  for (let i = 0; i < 8; i++) {
    for (let j = 3; j >= 0; j--) {
      const byte = (hash[i] >> (j * 8)) & 255;
      hex += (byte < 16 ? "0" : "") + byte.toString(16);
    }
  }
  return hex;
}

export function computeChatDigest(chat: { id?: string; messages?: { role: string; content: string }[] }): string {
  const messages = chat.messages || [];
  const canonical = messages
    .map((m) => `${m.role}:${m.content}`)
    .join("\n");
  return sha256Sync(canonical);
}

export function getSurvivingLegacyChats(
  storage?: { getItem: (key: string) => string | null }
): StoredChat[] {
  const store = storage || (typeof window !== "undefined" ? window.localStorage : null);
  if (!store) return [];
  try {
    const raw = store.getItem(COACH_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (item): item is StoredChat =>
        Boolean(item) &&
        typeof item === "object" &&
        typeof item.id === "string" &&
        Array.isArray(item.messages)
    );
  } catch {
    return [];
  }
}

export interface OptInImportOptions {
  targetUserId: string;
  targetAccountLabel?: string;
  confirmed: boolean;
  storage?: { getItem: (key: string) => string | null };
  customFetch?: typeof fetch;
  authToken?: string;
  existingDigests?: Set<string>;
}

export interface OptInImportResult {
  sourceId: string;
  digest: string;
  status: "imported" | "skipped" | "error";
  error?: string;
  conversationId?: string;
}

export interface OptInImportReport {
  total: number;
  imported: number;
  skipped: number;
  errors: number;
  results: OptInImportResult[];
}

export async function executeOptInImport(options: OptInImportOptions): Promise<OptInImportReport> {
  if (!options.confirmed) {
    throw new Error("Se requiere confirmación explícita de la cuenta destino para iniciar la importación");
  }

  const store = options.storage || (typeof window !== "undefined" ? window.localStorage : null);
  if (!store) {
    return { total: 0, imported: 0, skipped: 0, errors: 0, results: [] };
  }

  // Comprobar raw inicial para garantizar que NO se modifica ni borra el almacenamiento local (REQ-011)
  const initialRaw = store.getItem(COACH_STORAGE_KEY);

  const surviving = getSurvivingLegacyChats(store);
  const total = surviving.length;
  const results: OptInImportResult[] = [];
  let imported = 0;
  let skipped = 0;
  let errors = 0;

  const existingDigests = options.existingDigests || new Set<string>();
  const fetchFn = options.customFetch || (typeof fetch !== "undefined" ? fetch : null);

  for (const chat of surviving) {
    const digest = computeChatDigest(chat);

    // Si ya existe snapshot idéntico con el mismo digest, no duplicar (REQ-011)
    if (existingDigests.has(digest)) {
      results.push({
        sourceId: chat.id,
        digest,
        status: "skipped",
      });
      skipped++;
      continue;
    }

    if (!fetchFn) {
      results.push({
        sourceId: chat.id,
        digest,
        status: "error",
        error: "Cliente HTTP no disponible",
      });
      errors++;
      continue;
    }

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (options.authToken) {
        headers["Authorization"] = `Bearer ${options.authToken}`;
      }

      const res = await fetchFn("/api/conversations", {
        method: "POST",
        headers,
        body: JSON.stringify({
          title: chat.title || "Conversación importada",
        }),
      });

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        results.push({
          sourceId: chat.id,
          digest,
          status: "error",
          error: body.error || `Error HTTP ${res.status}`,
        });
        errors++;
        continue;
      }

      const body = (await res.json()) as { ok?: boolean; conversation?: { id: string } };
      if (!body.ok || !body.conversation?.id) {
        results.push({
          sourceId: chat.id,
          digest,
          status: "error",
          error: "Respuesta inválida del servidor al crear conversación",
        });
        errors++;
        continue;
      }

      const conversationId = body.conversation.id;
      existingDigests.add(digest);
      results.push({
        sourceId: chat.id,
        digest,
        status: "imported",
        conversationId,
      });
      imported++;
    } catch (err) {
      results.push({
        sourceId: chat.id,
        digest,
        status: "error",
        error: err instanceof Error ? err.message : "Error inesperado al importar conversación",
      });
      errors++;
    }
  }

  // Validación final: el localStorage original debe seguir exactamente intacto byte a byte
  const finalRaw = store.getItem(COACH_STORAGE_KEY);
  if (initialRaw !== finalRaw) {
    console.error("ADVERTENCIA DE SEGURIDAD: localStorage original fue alterado durante la importación");
  }

  return {
    total,
    imported,
    skipped,
    errors,
    results,
  };
}

export function loadChats(): StoredChat[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(COACH_STORAGE_KEY);
    const parsed = raw ? (JSON.parse(raw) as StoredChat[]) : [];
    return Array.isArray(parsed) ? parsed.slice(0, MAX_CHATS) : [];
  } catch {
    return [];
  }
}

export function saveChats(chats: StoredChat[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(COACH_STORAGE_KEY, JSON.stringify(chats.slice(0, MAX_CHATS)));
}

export function getChat(id: string): StoredChat | null {
  return loadChats().find((chat) => chat.id === id) ?? null;
}

export function upsertChat(chat: StoredChat): StoredChat[] {
  const rest = loadChats().filter((item) => item.id !== chat.id);
  const next = [chat, ...rest].slice(0, MAX_CHATS);
  saveChats(next);
  return next;
}

export function setPendingFirstMessage(chatId: string, text: string) {
  if (typeof sessionStorage === "undefined") return;
  sessionStorage.setItem(`${PENDING_PREFIX}${chatId}`, text);
}

export function takePendingFirstMessage(chatId: string): string | null {
  if (typeof sessionStorage === "undefined") return null;
  const key = `${PENDING_PREFIX}${chatId}`;
  const value = sessionStorage.getItem(key);
  if (value) sessionStorage.removeItem(key);
  return value;
}

export function chatHref(id: string) {
  return `/chat?conversation=${encodeURIComponent(id)}`;
}
