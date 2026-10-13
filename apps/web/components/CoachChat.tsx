"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { CoachModelSelect } from "@/components/CoachModelSelect";
import {
  type StoredChat,
  chatHref,
  loadChats,
  setPendingFirstMessage,
} from "@/lib/coachStorage";
import { formatDateEsCO } from "@/lib/lastUpdated";
import { loadPreferredModel } from "@/lib/openaiModels";

export function CoachChat() {
  const router = useRouter();
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
    router.push(chatHref(id));
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
        <label htmlFor="coach-draft-input" className="sr-only">
          Pregunta para el entrenador
        </label>
        <textarea
          id="coach-draft-input"
          aria-label="Pregunta para el entrenador"
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
            Nueva conversación
          </button>
          <button type="submit" className="coach-send" disabled={!draft.trim()}>
            Enviar
          </button>
        </div>
      </form>

      {apiOk === false ? (
        <p className="dash-refresh-status error mt-0" role="alert" style={{ marginTop: "0.5rem" }}>
          El servicio del entrenador no está disponible en este momento. Intenta de nuevo más tarde.
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
                <span className="muted">{formatDateEsCO(chat.updatedAt)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
