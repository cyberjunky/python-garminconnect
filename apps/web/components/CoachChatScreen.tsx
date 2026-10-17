"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { CoachModelSelect } from "@/components/CoachModelSelect";
import {
  chatHref,
  getSurvivingLegacyChats,
  mergeConversations,
  executeOptInImport,
  takePendingFirstMessage,
  upsertChat,
  getChat,
  type StoredChat,
} from "@/lib/coachStorage";
import { formatDateEsCO } from "@/lib/lastUpdated";
import { useCoachConversation } from "@/hooks/useCoachConversation";
import { ClientAuthService } from "@/lib/infra/auth/clientAuthService";

export function CoachChatScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const conversationId = searchParams.get("conversation");

  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  // Opt-in import state
  const [legacyChats, setLegacyChats] = useState<StoredChat[]>([]);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  const threadEndRef = useRef<HTMLDivElement>(null);
  const bootstrappedRef = useRef<string | null>(null);
  const authService = new ClientAuthService();

  // Gestión de sesión de usuario
  useEffect(() => {
    void authService.getSession().then((session) => {
      if (session?.user) {
        setAccessToken(session.access_token);
        setUserEmail(session.user.email ?? null);
        setUserId(session.user.id);
      }
    });

    const { unsubscribe } = authService.onAuthStateChange((session) => {
      setAccessToken(session?.access_token ?? null);
      setUserEmail(session?.user?.email ?? null);
      setUserId(session?.user?.id ?? null);
    });

    return () => unsubscribe();
  }, []);

  // Detectar conversaciones supervivientes locales para importación opt-in (REQ-011)
  useEffect(() => {
    const surviving = getSurvivingLegacyChats();
    if (surviving.length > 0) {
      setLegacyChats(surviving);
    }
  }, []);

  // ViewModel de la conversación
  const {
    conversation,
    conversations,
    totalConversations,
    messages,
    draft,
    setDraft,
    sendMessage,
    retryLastMessage,
    loadConversations,
    loadNextPage,
    loadMessages,
    clearState,
    isSending,
    isLoading,
    error,
    saveStatus,
    hasConflict,
  } = useCoachConversation({
    conversationId,
    accessToken,
  });

  // Fallback a mensajes locales si la conversación no está en nube o ante 401
  const localChat = conversationId ? getChat(conversationId) : null;
  const effectiveMessages =
    messages.length > 0
      ? messages
      : (localChat?.messages.map((m, idx) => ({
          id: `local-${idx}`,
          role: m.role,
          content: m.content,
          status: "saved" as const,
        })) ?? []);

  // Respaldo local inmediato en localStorage mediante upsertChat al enviar y recibir mensajes (REQ-008)
  useEffect(() => {
    if (!conversationId) return;
    if (messages.length > 0) {
      upsertChat({
        id: conversationId,
        title: conversation?.title || localChat?.title || "Conversación",
        updatedAt: new Date().toISOString(),
        messages: messages.map((m) => ({ role: m.role, content: m.content })),
      });
      setLegacyChats(getSurvivingLegacyChats());
    }
  }, [conversationId, messages, conversation?.title, localChat?.title]);

  const mergedHistory = mergeConversations(conversations, legacyChats);

  const scrollToEnd = useCallback(() => {
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    threadEndRef.current?.scrollIntoView({
      behavior: prefersReducedMotion ? "auto" : "smooth",
    });
  }, []);

  // Redirección si falta conversación
  useEffect(() => {
    if (!conversationId) {
      router.replace("/");
    }
  }, [conversationId, router]);

  // Enviar primer mensaje pendiente si viene de Hoy
  useEffect(() => {
    if (!conversationId) return;
    if (bootstrappedRef.current === conversationId) return;
    bootstrappedRef.current = conversationId;

    const pending = takePendingFirstMessage(conversationId);
    if (pending) {
      void sendMessage(pending);
    }
  }, [conversationId, sendMessage]);

  // Carga de historial en panel
  useEffect(() => {
    if (historyOpen) {
      setLegacyChats(getSurvivingLegacyChats());
      void loadConversations({ limit: 20, offset: 0 });
    }
  }, [historyOpen, loadConversations]);

  // Auto-scroll al recibir mensajes
  useEffect(() => {
    scrollToEnd();
  }, [effectiveMessages.length, scrollToEnd]);

  function startNewChat() {
    router.push(chatHref(crypto.randomUUID()));
  }

  async function handleLogout() {
    clearState();
    await authService.signOut();
    router.replace("/login");
  }

  async function handleConfirmImport() {
    if (!userId) {
      setImportStatus("Debes iniciar sesión para importar tus conversaciones.");
      return;
    }

    setIsImporting(true);
    setImportStatus("Importando conversaciones de forma segura…");

    try {
      const report = await executeOptInImport({
        targetUserId: userId,
        targetAccountLabel: userEmail ?? undefined,
        confirmed: true,
        authToken: accessToken ?? undefined,
      });

      setImportStatus(
        `Importación completada: ${report.imported} importadas, ${report.skipped} omitidas (duplicadas), ${report.errors} errores. Tu almacenamiento local original permanece 100% intacto.`
      );
      void loadConversations({ limit: 20, offset: 0 });
    } catch (err) {
      setImportStatus(
        err instanceof Error ? err.message : "Error inesperado durante la importación"
      );
    } finally {
      setIsImporting(false);
    }
  }

  if (!conversationId) {
    return null;
  }

  return (
    <main className="chat-main">
      <header className="chat-header">
        <div className="chat-header-left">
          <Link href="/" className="chat-back" aria-label="Volver a Hoy">
            ←
          </Link>
          <h1 className="chat-title">Tri-Coach</h1>
          {userEmail ? (
            <span className="muted user-email-badge" title={`Sesión activa: ${userEmail}`}>
              {userEmail}
            </span>
          ) : (
            <Link href={`/login?next=${encodeURIComponent(chatHref(conversationId))}`} className="chat-login-link">
              Iniciar sesión
            </Link>
          )}
        </div>
        <div className="chat-header-actions">
          {legacyChats.length > 0 ? (
            <button
              type="button"
              className="chat-header-btn chat-import-btn"
              onClick={() => setShowImportModal(true)}
              title="Importar historial de este navegador"
            >
              📥 Importar ({legacyChats.length})
            </button>
          ) : null}
          <button
            type="button"
            className="chat-header-btn"
            onClick={startNewChat}
            disabled={isSending}
          >
            + Nuevo chat
          </button>
          <button
            type="button"
            className="chat-header-btn"
            onClick={() => setHistoryOpen((open) => !open)}
            aria-expanded={historyOpen}
          >
            Historial ({mergedHistory.length})
          </button>
          {userEmail ? (
            <button
              type="button"
              className="chat-header-btn chat-logout-btn"
              onClick={handleLogout}
              title="Cerrar sesión (REQ-013)"
            >
              Salir
            </button>
          ) : null}
        </div>
      </header>

      {/* Modal de importación opt-in (REQ-011, REQ-012) */}
      {showImportModal ? (
        <div className="optin-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="import-title">
          <div className="optin-modal-card">
            <h2 id="import-title" className="optin-modal-title">
              Importar conversaciones de este navegador
            </h2>
            <p className="optin-modal-desc">
              Hemos detectado <strong>{legacyChats.length} conversaciones</strong> guardadas
              previamente en este navegador.
            </p>
            <div className="optin-modal-target">
              <span className="muted">Cuenta destino confirmada:</span>
              <strong>{userEmail || "Sesión no autenticada"}</strong>
            </div>
            <p className="optin-modal-warning muted">
              ✓ Esta operación es una copia segura: tus datos originales de este navegador permanecerán intactos
              byte a byte.
            </p>
            {importStatus ? (
              <div className="dash-refresh-banner login-alert" role="status">
                {importStatus}
              </div>
            ) : null}
            <div className="optin-modal-actions">
              <button
                type="button"
                className="coach-send"
                onClick={handleConfirmImport}
                disabled={isImporting || !userEmail}
              >
                {isImporting ? "Importando…" : `Confirmar copia a ${userEmail || "mi cuenta"}`}
              </button>
              <button
                type="button"
                className="coach-new"
                onClick={() => {
                  setShowImportModal(false);
                  setImportStatus(null);
                }}
                disabled={isImporting}
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Panel lateral o desplegable de historial sincronizado */}
      {historyOpen ? (
        <div className="chat-history-panel-wrap">
          <ul className="chat-history-panel">
            {mergedHistory.length === 0 ? (
              <li className="muted">
                {isLoading ? "Cargando conversaciones…" : "Sin conversaciones registradas."}
              </li>
            ) : (
              mergedHistory.map((item) => (
                <li key={item.id}>
                  <Link
                    href={chatHref(item.id)}
                    className={item.id === conversationId ? "coach-history-item active" : "coach-history-item"}
                    onClick={() => setHistoryOpen(false)}
                  >
                    <span>{item.title}</span>
                    <span className="muted">{item.updatedAt ? formatDateEsCO(item.updatedAt) : ""}</span>
                  </Link>
                </li>
              ))
            )}
          </ul>
          {conversations.length < totalConversations ? (
            <button
              type="button"
              className="chat-load-more"
              onClick={() => void loadNextPage()}
              disabled={isLoading}
            >
              {isLoading ? "Cargando…" : "Cargar más conversaciones"}
            </button>
          ) : null}
        </div>
      ) : null}

      {/* Hilo de conversación */}
      <div className="chat-thread" role="log" aria-live="polite">
        {effectiveMessages.length === 0 && !isSending ? (
          <p className="muted chat-empty">Escribe tu pregunta sobre condición, sesión o retos.</p>
        ) : null}

        {effectiveMessages.map((message) => (
          <div
            key={message.id}
            className={message.role === "user" ? "chat-row chat-row-user" : "chat-row chat-row-assistant"}
          >
            {message.role === "assistant" ? <span className="chat-sender">Coach</span> : null}
            <div className={`coach-bubble coach-${message.role}`}>
              <p className="m-0">{message.content}</p>
              {message.role === "user" && message.status === "error" ? (
                <div className="chat-message-error-bar">
                  <span className="error-text">No guardado</span>
                  <button
                    type="button"
                    className="chat-retry-btn"
                    onClick={() => void retryLastMessage()}
                  >
                    Reintentar
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        ))}

        {isSending ? <p className="muted chat-thinking">Pensando…</p> : null}
        <div ref={threadEndRef} />
      </div>

      {/* Estados visibles de guardado / conflicto / error */}
      <div className="chat-status-bar">
        {saveStatus === "saved" ? (
          <span className="chat-status-badge saved" role="status">
            ✓ Guardado
          </span>
        ) : saveStatus === "saving" ? (
          <span className="chat-status-badge saving" role="status">
            Guardando…
          </span>
        ) : saveStatus === "conflict" || hasConflict ? (
          <div className="chat-status-badge conflict" role="alert">
            <span>⚠ Conflicto de sincronización con el servidor.</span>
            <button
              type="button"
              className="chat-retry-inline-btn"
              onClick={() => void retryLastMessage()}
            >
              Reenviar borrador
            </button>
          </div>
        ) : error ? (
          <div className="dash-refresh-status error chat-error" role="alert" aria-live="assertive">
            <span>{error}</span>
            <button
              type="button"
              className="chat-retry-inline-btn"
              onClick={() => void retryLastMessage()}
            >
              Reintentar
            </button>
          </div>
        ) : null}
      </div>

      {/* Compositor centrado max 880px */}
      <form
        className="chat-composer-wrap"
        onSubmit={(event) => {
          event.preventDefault();
          void sendMessage();
        }}
      >
        <div className="coach-composer chat-composer">
          <label htmlFor="chat-screen-input" className="sr-only">
            Mensaje para el entrenador
          </label>
          <textarea
            id="chat-screen-input"
            aria-label="Mensaje para el entrenador"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Pregunta lo que quieras sobre tu entrenamiento"
            rows={3}
            disabled={isSending}
          />
          <div className="coach-composer-bar">
            <CoachModelSelect />
            <button type="submit" className="coach-send" disabled={isSending || !draft.trim()}>
              {isSending ? "Enviando…" : "Enviar"}
            </button>
          </div>
        </div>
      </form>
    </main>
  );
}
