"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { CoachModelSelect } from "@/components/CoachModelSelect";
import {
  type ChatMessage,
  type StoredChat,
  chatHref,
  getChat,
  loadChats,
  takePendingFirstMessage,
  upsertChat,
} from "@/lib/coachStorage";
import { loadPreferredModel } from "@/lib/openaiModels";

type ApiStatus = {
  configured: boolean;
  models: string[];
  defaultModel: string;
};

async function fetchReply(
  messages: ChatMessage[],
  model: string
): Promise<{ reply: string } | { error: string }> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, model }),
  });
  const body = (await res.json()) as { ok?: boolean; reply?: string; error?: string };
  if (!res.ok || !body.ok || !body.reply) {
    return { error: body.error || "No se pudo consultar al coach" };
  }
  return { reply: body.reply };
}

export function CoachChatScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const conversationId = searchParams.get("conversation");

  const [draft, setDraft] = useState("");
  const [chat, setChat] = useState<StoredChat | null>(null);
  const [history, setHistory] = useState<StoredChat[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [model, setModel] = useState("gpt-4o-mini");
  const [historyOpen, setHistoryOpen] = useState(false);
  const threadEndRef = useRef<HTMLDivElement>(null);
  const bootstrappedRef = useRef<string | null>(null);

  const scrollToEnd = useCallback(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    void fetch("/api/chat")
      .then((res) => res.json())
      .then((body: { configured?: boolean; models?: string[]; defaultModel?: string }) => {
        const defaultModel = body.defaultModel || "gpt-4o-mini";
        const models = body.models?.length ? body.models : [defaultModel];
        setApiStatus({
          configured: Boolean(body.configured),
          models,
          defaultModel,
        });
        setModel(loadPreferredModel(defaultModel, models));
      })
      .catch(() =>
        setApiStatus({ configured: false, models: ["gpt-4o-mini"], defaultModel: "gpt-4o-mini" })
      );
  }, []);

  useEffect(() => {
    setHistory(loadChats());
  }, []);

  useEffect(() => {
    if (!conversationId) {
      router.replace("/");
      return;
    }
    const existing = getChat(conversationId);
    const base: StoredChat = existing ?? {
      id: conversationId,
      title: "Nueva conversación",
      updatedAt: new Date().toISOString(),
      messages: [],
    };
    setChat(base);
    setError(null);
    bootstrappedRef.current = null;
  }, [conversationId, router]);

  const persistAndSet = useCallback((next: StoredChat) => {
    setChat(next);
    setHistory(upsertChat(next));
  }, []);

  const sendText = useCallback(
    async (text: string, current: StoredChat) => {
      const trimmed = text.trim();
      if (!trimmed || sending) return;

      if (apiStatus && !apiStatus.configured) {
        setError("Falta OPENAI_API_KEY en Vercel (Production). Agrégala y redeploy.");
        return;
      }

      setSending(true);
      setError(null);
      const userMessage: ChatMessage = { role: "user", content: trimmed };
      const withUser: StoredChat = {
        ...current,
        title: current.messages.length === 0 ? trimmed.slice(0, 80) : current.title,
        updatedAt: new Date().toISOString(),
        messages: [...current.messages, userMessage],
      };
      persistAndSet(withUser);
      setDraft("");

      const result = await fetchReply(withUser.messages, model);
      if ("error" in result) {
        setError(result.error);
        setSending(false);
        return;
      }

      persistAndSet({
        ...withUser,
        updatedAt: new Date().toISOString(),
        messages: [...withUser.messages, { role: "assistant", content: result.reply }],
      });
      setSending(false);
      scrollToEnd();
    },
    [apiStatus, model, persistAndSet, scrollToEnd, sending]
  );

  useEffect(() => {
    if (!conversationId || !chat) return;
    if (bootstrappedRef.current === conversationId) return;
    bootstrappedRef.current = conversationId;

    const pending = takePendingFirstMessage(conversationId);
    if (pending && chat.messages.length === 0) {
      void sendText(pending, chat);
    }
  }, [chat, conversationId, sendText]);

  useEffect(() => {
    scrollToEnd();
  }, [chat?.messages.length, scrollToEnd]);

  function startNewChat() {
    router.push(chatHref(crypto.randomUUID()));
  }

  if (!conversationId || !chat) {
    return null;
  }

  const models = apiStatus?.models ?? [model];

  return (
    <main className="chat-main">
      <header className="chat-header">
        <div className="chat-header-left">
          <Link href="/" className="chat-back" aria-label="Volver a Hoy">
            ←
          </Link>
          <h1 className="chat-title">Coach</h1>
        </div>
        <div className="chat-header-actions">
          <button type="button" className="chat-header-btn" onClick={startNewChat} disabled={sending}>
            + Nuevo chat
          </button>
          <button
            type="button"
            className="chat-header-btn"
            onClick={() => setHistoryOpen((open) => !open)}
            aria-expanded={historyOpen}
          >
            Historial
          </button>
        </div>
      </header>

      {apiStatus && !apiStatus.configured ? (
        <p className="chat-api-hint dash-refresh-status error">
          OpenAI no está configurado. En Vercel → Settings → Environment Variables, agrega{" "}
          <code>OPENAI_API_KEY</code> y redeploy.
        </p>
      ) : null}

      {historyOpen ? (
        <ul className="chat-history-panel">
          {history.length === 0 ? (
            <li className="muted">Sin conversaciones guardadas.</li>
          ) : (
            history.map((item) => (
              <li key={item.id}>
                <Link
                  href={chatHref(item.id)}
                  className={item.id === conversationId ? "coach-history-item active" : "coach-history-item"}
                  onClick={() => setHistoryOpen(false)}
                >
                  <span>{item.title}</span>
                  <span className="muted">{item.updatedAt.slice(0, 10)}</span>
                </Link>
              </li>
            ))
          )}
        </ul>
      ) : null}

      <div className="chat-thread" role="log" aria-live="polite">
        {chat.messages.length === 0 && !sending ? (
          <p className="muted chat-empty">Escribe tu primera pregunta sobre condición, sesión o retos.</p>
        ) : null}
        {chat.messages.map((message, index) => (
          <div
            key={`${chat.id}-${index}`}
            className={message.role === "user" ? "chat-row chat-row-user" : "chat-row chat-row-assistant"}
          >
            {message.role === "assistant" ? <span className="chat-sender">Coach</span> : null}
            <p className={`coach-bubble coach-${message.role}`}>{message.content}</p>
          </div>
        ))}
        {sending ? <p className="muted chat-thinking">Pensando…</p> : null}
        <div ref={threadEndRef} />
      </div>

      {error ? <p className="dash-refresh-status error chat-error">{error}</p> : null}

      <form
        className="chat-composer-wrap"
        onSubmit={(event) => {
          event.preventDefault();
          void sendText(draft, chat);
        }}
      >
        <div className="coach-composer chat-composer">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Pregunta lo que quieras sobre tu entrenamiento…"
            rows={3}
            disabled={sending}
          />
          <div className="coach-composer-bar">
            <CoachModelSelect
              models={models}
              value={model}
              onChange={setModel}
              disabled={sending}
            />
            <button type="submit" className="coach-send" disabled={sending || !draft.trim()}>
              Enviar
            </button>
          </div>
        </div>
      </form>
    </main>
  );
}
