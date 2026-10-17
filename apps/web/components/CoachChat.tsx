"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { CoachModelSelect } from "@/components/CoachModelSelect";
import { chatHref, setPendingFirstMessage } from "@/lib/coachStorage";
import { formatDateEsCO } from "@/lib/lastUpdated";
import { useCoachConversation } from "@/hooks/useCoachConversation";
import { ClientAuthService } from "@/lib/infra/auth/clientAuthService";

export function CoachChat() {
  const router = useRouter();
  const [draft, setDraft] = useState("");
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const authService = new ClientAuthService();

  useEffect(() => {
    void authService.getSession().then((session) => {
      setAccessToken(session?.access_token ?? null);
    });
  }, []);

  const { conversations, loadConversations, createConversation, isLoading, error } =
    useCoachConversation({
      accessToken,
    });

  useEffect(() => {
    void loadConversations({ limit: 10, offset: 0 });
  }, [loadConversations, accessToken]);

  async function openNewChat(firstMessage?: string) {
    const newId = crypto.randomUUID();
    if (firstMessage) {
      setPendingFirstMessage(newId, firstMessage);
    }
    router.push(chatHref(newId));
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
          void openNewChat(text);
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
          <CoachModelSelect />
          <button
            type="button"
            className="coach-new"
            onClick={() => void openNewChat()}
          >
            Nueva conversación
          </button>
          <button type="submit" className="coach-send" disabled={!draft.trim()}>
            Enviar
          </button>
        </div>
      </form>

      {error ? (
        <p className="dash-refresh-status error mt-0" role="alert" style={{ marginTop: "0.5rem" }}>
          {error}
        </p>
      ) : null}

      <h2 className="coach-history-title">Últimas conversaciones</h2>
      {isLoading && conversations.length === 0 ? (
        <p className="muted">Cargando historial…</p>
      ) : conversations.length === 0 ? (
        <p className="muted">Aún no hay conversaciones registradas. Al enviar, se abre la pantalla de chat.</p>
      ) : (
        <ul className="coach-history">
          {conversations.map((chat) => (
            <li key={chat.id}>
              <Link href={chatHref(chat.id)} className="coach-history-item">
                <span>{chat.title}</span>
                <span className="muted">{chat.updatedAt ? formatDateEsCO(chat.updatedAt) : ""}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
