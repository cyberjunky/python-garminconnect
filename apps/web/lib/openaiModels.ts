export const COACH_MODEL_STORAGE_KEY = "fitness-coach-model";

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

export function savePreferredModel(model: string): void {
  try {
    window.localStorage.setItem(COACH_MODEL_STORAGE_KEY, model);
  } catch {
    // Local storage non-blocking fallback
  }
}
