"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CoachModelSelect } from "@/components/CoachModelSelect";
import {
  type StoredChat,
  chatHref,
  loadChats,
  setPendingFirstMessage,
} from "@/lib/coachStorage";
import { loadPreferredModel } from "@/lib/openaiModels";

export function CoachChat() {
  const [draft, setDraft] = useState("");
  const [chats, setChats] = useState<StoredChat[]>([]);
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [models, setModels] = useState<string[]>(["gpt-4o-mini"]);
  const [model, setModel] = useState("gpt-4o-mini");

  useEffect(() => {
    setChats(loadChats());
    void fetch("/api/chat")
      .then((res) => res.json())
      .then((body: { configured?: boolean; models?: string[]; defaultModel?: string }) => {
        setApiOk(Boolean(body.configured));
        const defaultModel = body.defaultModel || "gpt-4o-mini";
        setModels(body.models?.length ? body.models : [defaultModel]);
        const list = body.models?.length ? body.models : [defaultModel];
        setModel(loadPreferredModel(defaultModel, list));
      })
      .catch(() => setApiOk(false));
  }, []);

  function openChat(id: string, firstMessage?: string) {
    if (firstMessage) setPendingFirstMessage(id, firstMessage);
    window.location.assign(chatHref(id));
  }

  return (
    <section className="coach-chat" aria-label="Diálogo con el coach">
      <form
        className="coach-composer"
        onSubmit={(event) => {
          event.preventDefault();
          const text = draft.trim();
          if (!text) return;
          setDraft("");
          openChat(crypto.randomUUID(), text);
        }}
      >
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Pregunta por tu condición, la sesión o el próximo reto"
          rows={3}
        />
        <div className="coach-composer-bar">
          <CoachModelSelect models={models} value={model} onChange={setModel} />
          <button
            type="button"
            className="coach-new"
            onClick={() => openChat(crypto.randomUUID())}
          >
            Nueva
          </button>
          <button type="submit" className="coach-send" disabled={!draft.trim()}>
            Enviar
          </button>
        </div>
      </form>

      {apiOk === false ? (
        <p className="dash-refresh-status error" style={{ marginTop: "0.5rem" }}>
          Para activar el coach, configura <code>OPENAI_API_KEY</code> en Vercel y redeploy.
        </p>
      ) : null}

      <h2 className="coach-history-title">Últimas conversaciones</h2>
      {chats.length === 0 ? (
        <p className="muted">Aún no hay conversaciones en este navegador. Al enviar, se abre la pantalla de chat.</p>
      ) : (
        <ul className="coach-history">
          {chats.map((chat) => (
            <li key={chat.id}>
              <Link href={chatHref(chat.id)} className="coach-history-item">
                <span>{chat.title}</span>
                <span className="muted">{chat.updatedAt.slice(0, 10)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
