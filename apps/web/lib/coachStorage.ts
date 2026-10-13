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
  sessionStorage.setItem(`${PENDING_PREFIX}${chatId}`, text);
}

export function takePendingFirstMessage(chatId: string): string | null {
  const key = `${PENDING_PREFIX}${chatId}`;
  const value = sessionStorage.getItem(key);
  if (value) sessionStorage.removeItem(key);
  return value;
}

export function chatHref(id: string) {
  return `/chat?conversation=${encodeURIComponent(id)}`;
}
