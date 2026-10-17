export const DEFAULT_OPENAI_MODELS = [
  "gpt-4o-mini",
  "gpt-4o",
  "gpt-4.1-mini",
  "gpt-4.1",
] as const;

export const COACH_MODEL_STORAGE_KEY = "fitness-coach-model";

const CHAT_MODEL_PREFIX = /^(gpt-|o\d|chatgpt-)/i;
const MODEL_ID_SAFE = /^[a-z0-9][a-z0-9._-]{0,80}$/i;
const MODEL_EXCLUDE =
  /(embed|whisper|tts|dall-e|moderation|realtime|audio|transcribe|search|computer|sora|image|video)/i;

let catalogCache: { models: string[]; at: number } | null = null;
const CATALOG_TTL_MS = 5 * 60 * 1000;

export function parseModelsEnv(raw: string | undefined): string[] {
  if (!raw?.trim()) return [];
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function modelSortKey(id: string): string {
  const lower = id.toLowerCase();
  if (lower.startsWith("gpt-5")) return `0-${lower}`;
  if (/^o\d/.test(lower)) return `1-${lower}`;
  if (lower.includes("4.1")) return `2-${lower}`;
  if (lower.includes("4o")) return `3-${lower}`;
  if (lower.startsWith("gpt-4")) return `4-${lower}`;
  return `9-${lower}`;
}

function sortModelIds(ids: string[]): string[] {
  return [...ids].sort((a, b) => modelSortKey(a).localeCompare(modelSortKey(b)));
}

export function isLikelyChatModel(id: string): boolean {
  return MODEL_ID_SAFE.test(id) && CHAT_MODEL_PREFIX.test(id) && !MODEL_EXCLUDE.test(id);
}

export async function fetchOpenAiChatModels(apiKey: string): Promise<string[]> {
  const res = await fetch("https://api.openai.com/v1/models", {
    headers: { Authorization: `Bearer ${apiKey}` },
    cache: "no-store",
  });
  if (!res.ok) return [];
  const body = (await res.json()) as { data?: { id: string }[] };
  const ids = (body.data ?? []).map((item) => item.id).filter(isLikelyChatModel);
  return sortModelIds([...new Set(ids)]);
}

export async function serverModelCatalog(): Promise<{ models: string[]; defaultModel: string }> {
  const fromEnv = parseModelsEnv(process.env.OPENAI_MODELS);
  const defaultModel = process.env.OPENAI_MODEL || "gpt-4o-mini";
  const apiKey = process.env.OPENAI_API_KEY;

  let fromApi: string[] = [];
  if (apiKey) {
    const now = Date.now();
    if (catalogCache && now - catalogCache.at < CATALOG_TTL_MS) {
      fromApi = catalogCache.models;
    } else {
      fromApi = await fetchOpenAiChatModels(apiKey);
      if (fromApi.length > 0) {
        catalogCache = { models: fromApi, at: now };
      }
    }
  }

  const base = fromApi.length > 0 ? fromApi : [...DEFAULT_OPENAI_MODELS];
  const merged = sortModelIds([...new Set([defaultModel, ...fromEnv, ...base])]);
  const resolvedDefault = merged.includes(defaultModel) ? defaultModel : merged[0] || "gpt-4o-mini";
  return { models: merged, defaultModel: resolvedDefault };
}

export function pickModel(requested: string | undefined, catalog: string[], fallback: string): string {
  if (requested && catalog.includes(requested)) return requested;
  const fromEnv = parseModelsEnv(process.env.OPENAI_MODELS);
  if (requested && fromEnv.includes(requested)) return requested;
  if (requested && isLikelyChatModel(requested)) return requested;
  if (catalog.includes(fallback)) return fallback;
  return catalog[0] || "gpt-4o-mini";
}

export function loadPreferredModel(defaultModel: string, catalog: string[]): string {
  if (typeof window === "undefined") return defaultModel;
  try {
    const stored = window.localStorage.getItem(COACH_MODEL_STORAGE_KEY);
    if (stored && catalog.includes(stored)) return stored;
    return defaultModel;
  } catch {
    return defaultModel;
  }
}

export function savePreferredModel(model: string) {
  window.localStorage.setItem(COACH_MODEL_STORAGE_KEY, model);
}
