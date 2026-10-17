"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export interface MessageViewModel {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "saved" | "pending" | "error";
  errorMessage?: string;
  operationId?: string;
  sequence?: number;
  createdAt?: string;
}

export interface ConversationViewModel {
  id: string;
  title: string;
  revision: number;
  updatedAt?: string;
}

export type SaveStatus = "idle" | "saving" | "saved" | "error" | "conflict";

export interface UseCoachConversationOptions {
  conversationId?: string | null;
  initialRevision?: number;
  accessToken?: string | null;
  customFetch?: typeof fetch;
  apiBaseUrl?: string;
  onStateChange?: () => void;
}

export interface CoachConversationState {
  conversation: ConversationViewModel | null;
  conversations: ConversationViewModel[];
  totalConversations: number;
  messages: MessageViewModel[];
  draft: string;
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  hasConflict: boolean;
  saveStatus: SaveStatus;
  pendingRetryContent: string | null;
}

export class CoachConversationViewModel implements CoachConversationState {
  conversation: ConversationViewModel | null = null;
  conversations: ConversationViewModel[] = [];
  totalConversations = 0;
  messages: MessageViewModel[] = [];
  draft = "";
  isLoading = false;
  isSending = false;
  error: string | null = null;
  hasConflict = false;
  saveStatus: SaveStatus = "idle";
  pendingRetryContent: string | null = null;

  private lastAttemptedUserMessage: MessageViewModel | null = null;
  private accessToken: string | null;
  private readonly customFetch?: typeof fetch;
  private readonly apiBaseUrl: string;
  private readonly onStateChange?: () => void;

  constructor(options: UseCoachConversationOptions = {}) {
    this.accessToken = options.accessToken ?? null;
    this.customFetch = options.customFetch;
    this.apiBaseUrl = options.apiBaseUrl ?? "";
    this.onStateChange = options.onStateChange;

    if (options.conversationId) {
      this.conversation = {
        id: options.conversationId,
        title: "Conversación",
        revision: options.initialRevision ?? 1,
      };
    }
  }

  setAccessToken(token: string | null): void {
    if (this.accessToken !== token) {
      this.accessToken = token;
      this.notify();
    }
  }

  private notify() {
    this.onStateChange?.();
  }

  private getFetch(): typeof fetch {
    if (this.customFetch) return this.customFetch;
    if (typeof fetch !== "undefined") return fetch;
    throw new Error("Cliente HTTP fetch no disponible en el entorno");
  }

  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    return headers;
  }

  setDraft(text: string) {
    this.draft = text;
    this.notify();
  }

  clearState() {
    this.conversation = null;
    this.conversations = [];
    this.totalConversations = 0;
    this.messages = [];
    this.draft = "";
    this.isLoading = false;
    this.isSending = false;
    this.error = null;
    this.hasConflict = false;
    this.saveStatus = "idle";
    this.pendingRetryContent = null;
    this.lastAttemptedUserMessage = null;
    this.notify();
  }

  async loadConversations(options: { offset?: number; limit?: number } = {}): Promise<void> {
    const limit = options.limit ?? 20;
    const offset = options.offset ?? 0;
    this.isLoading = true;
    this.notify();

    try {
      const fetchFn = this.getFetch();
      const res = await fetchFn(
        `${this.apiBaseUrl}/api/conversations?limit=${limit}&offset=${offset}`,
        {
          headers: this.getAuthHeaders(),
        }
      );

      if (res.ok) {
        const body = (await res.json()) as {
          ok?: boolean;
          conversations?: ConversationViewModel[];
          total?: number;
        };
        if (body.ok && Array.isArray(body.conversations)) {
          if (offset === 0) {
            this.conversations = body.conversations;
          } else {
            this.conversations = [...this.conversations, ...body.conversations];
          }
          this.totalConversations = body.total ?? this.conversations.length;

          if (this.conversation) {
            const current = this.conversations.find((c) => c.id === this.conversation?.id);
            if (current) {
              this.conversation = {
                ...this.conversation,
                revision: current.revision,
                title: current.title,
                updatedAt: current.updatedAt,
              };
            }
          }
        }
      } else if (res.status === 401) {
        // Sesión no autenticada en nube: no es crash, permite continuar con almacenamiento local
        this.error = null;
      } else {
        const errBody = (await res.json().catch(() => ({}))) as { error?: string };
        this.error = errBody.error || `Error del servidor (${res.status})`;
      }
    } catch (err) {
      this.error = err instanceof Error ? err.message : "Error al cargar conversaciones";
    } finally {
      this.isLoading = false;
      this.notify();
    }
  }

  async loadNextPage(): Promise<void> {
    const nextOffset = this.conversations.length;
    await this.loadConversations({ offset: nextOffset, limit: 20 });
  }

  async loadMessages(conversationId: string): Promise<void> {
    this.isLoading = true;
    this.notify();

    try {
      const fetchFn = this.getFetch();
      const res = await fetchFn(
        `${this.apiBaseUrl}/api/conversations/${conversationId}/messages`,
        {
          headers: this.getAuthHeaders(),
        }
      );

      if (res.ok) {
        const body = (await res.json()) as {
          ok?: boolean;
          messages?: Array<{
            id: string;
            role: "user" | "assistant";
            content: string;
            sequence?: number;
            createdAt?: string;
          }>;
        };
        if (body.ok && Array.isArray(body.messages)) {
          this.messages = body.messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            status: "saved",
            sequence: m.sequence,
            createdAt: m.createdAt,
          }));
        }
      } else if (res.status === 401) {
        this.error = null;
      } else {
        const errBody = (await res.json().catch(() => ({}))) as { error?: string };
        this.error = errBody.error || `Error del servidor (${res.status})`;
      }
    } catch (err) {
      this.error = err instanceof Error ? err.message : "Error al cargar mensajes";
    } finally {
      this.isLoading = false;
      this.notify();
    }
  }

  async createConversation(title?: string): Promise<string | null> {
    try {
      const fetchFn = this.getFetch();
      const res = await fetchFn(`${this.apiBaseUrl}/api/conversations`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ title: title || "Nueva conversación" }),
      });

      if (res.ok) {
        const body = (await res.json()) as {
          ok?: boolean;
          conversation?: ConversationViewModel;
        };
        if (body.ok && body.conversation?.id) {
          this.conversation = body.conversation;
          this.notify();
          return body.conversation.id;
        }
      }
      return null;
    } catch {
      return null;
    }
  }

  async sendMessage(contentOverride?: string): Promise<boolean> {
    const text = (contentOverride ?? this.draft).trim();
    if (!text || this.isSending) return false;

    if (text.length > 4000) {
      this.error = "El mensaje supera el límite máximo permitido de 4000 caracteres";
      this.saveStatus = "error";
      this.notify();
      return false;
    }

    let convId = this.conversation?.id;
    if (!convId) {
      const createdId = await this.createConversation(text.slice(0, 80));
      if (!createdId) {
        this.error = "No se pudo inicializar la conversación en el servidor";
        this.saveStatus = "error";
        this.notify();
        return false;
      }
      convId = createdId;
    }

    const operationId = crypto.randomUUID();
    const userMessage: MessageViewModel = {
      id: `pending-${Date.now()}`,
      role: "user",
      content: text,
      status: "pending",
      operationId,
      createdAt: new Date().toISOString(),
    };

    this.messages.push(userMessage);
    this.lastAttemptedUserMessage = userMessage;
    this.draft = "";
    this.isSending = true;
    this.error = null;
    this.saveStatus = "saving";
    this.hasConflict = false;
    this.pendingRetryContent = null;
    this.notify();

    return this.dispatchChatRequest(convId, operationId, text, userMessage);
  }

  async retryLastMessage(): Promise<boolean> {
    if (!this.lastAttemptedUserMessage) return false;
    const msg = this.lastAttemptedUserMessage;
    const convId = this.conversation?.id;
    if (!convId || !msg.operationId) return false;

    this.isSending = true;
    this.saveStatus = "saving";
    this.error = null;
    this.notify();

    return this.dispatchChatRequest(convId, msg.operationId, msg.content, msg);
  }

  private async dispatchChatRequest(
    conversationId: string,
    operationId: string,
    content: string,
    userMessage: MessageViewModel
  ): Promise<boolean> {
    const fetchFn = this.getFetch();
    const expectedRevision = this.conversation?.revision ?? 1;

    try {
      const res = await fetchFn(`${this.apiBaseUrl}/api/chat`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          conversationId,
          operationId,
          content,
          expectedRevision,
        }),
      });

      if (res.status === 200) {
        const body = (await res.json()) as {
          ok?: boolean;
          message?: { id: string; content: string; createdAt?: string; sequence?: number };
          reply?: string;
          revision?: number;
        };

        userMessage.status = "saved";
        if (body.revision && this.conversation) {
          this.conversation.revision = body.revision;
        }

        const replyContent = body.reply || body.message?.content || "";
        this.messages.push({
          id: body.message?.id || `asst-${Date.now()}`,
          role: "assistant",
          content: replyContent,
          status: "saved",
          createdAt: body.message?.createdAt || new Date().toISOString(),
          sequence: body.message?.sequence,
        });

        this.saveStatus = "saved";
        this.isSending = false;
        this.notify();
        return true;
      }

      if (res.status === 409) {
        userMessage.status = "error";
        this.hasConflict = true;
        this.saveStatus = "conflict";
        this.pendingRetryContent = content;
        this.error = "Conflicto de concurrencia: se han recibido nuevos mensajes del servidor";

        // Refrescar mensajes y revisión del servidor (REQ-010)
        await this.loadMessages(conversationId);
        await this.loadConversations();

        this.isSending = false;
        this.notify();
        return false;
      }

      // Otros códigos de error (400, 401, 500, etc.)
      const errorBody = (await res.json().catch(() => ({}))) as { error?: string };
      userMessage.status = "error";
      this.saveStatus = "error";
      this.pendingRetryContent = content;
      this.error = errorBody.error || `Error del servidor (${res.status})`;
      this.isSending = false;
      this.notify();
      return false;
    } catch (err) {
      userMessage.status = "error";
      this.saveStatus = "error";
      this.pendingRetryContent = content;
      this.error = err instanceof Error ? err.message : "Error de red al comunicarse con el coach";
      this.isSending = false;
      this.notify();
      return false;
    }
  }
}

export function useCoachConversationLogic(options: UseCoachConversationOptions = {}) {
  return new CoachConversationViewModel(options);
}

export function useCoachConversation(options: UseCoachConversationOptions = {}) {
  const [, setTick] = useState(0);
  const rerender = useCallback(() => setTick((t) => t + 1), []);

  const vmRef = useRef<CoachConversationViewModel | null>(null);

  if (!vmRef.current) {
    vmRef.current = new CoachConversationViewModel({
      ...options,
      onStateChange: rerender,
    });
  }

  const vm = vmRef.current;

  // Sincronización reactiva del accessToken cuando cambia en el cliente (REQ-005)
  useEffect(() => {
    vm.setAccessToken(options.accessToken ?? null);
  }, [options.accessToken, vm]);

  // Carga inicial o cambios de conversación
  useEffect(() => {
    if (options.conversationId) {
      void vm.loadMessages(options.conversationId);
    }
  }, [options.conversationId, vm]);

  return {
    conversation: vm.conversation,
    conversations: vm.conversations,
    totalConversations: vm.totalConversations,
    messages: vm.messages,
    draft: vm.draft,
    isLoading: vm.isLoading,
    isSending: vm.isSending,
    error: vm.error,
    hasConflict: vm.hasConflict,
    saveStatus: vm.saveStatus,
    pendingRetryContent: vm.pendingRetryContent,
    setDraft: useCallback((text: string) => vm.setDraft(text), [vm]),
    sendMessage: useCallback((text?: string) => vm.sendMessage(text), [vm]),
    retryLastMessage: useCallback(() => vm.retryLastMessage(), [vm]),
    loadConversations: useCallback(
      (opts?: { offset?: number; limit?: number }) => vm.loadConversations(opts),
      [vm]
    ),
    loadNextPage: useCallback(() => vm.loadNextPage(), [vm]),
    loadMessages: useCallback((id: string) => vm.loadMessages(id), [vm]),
    createConversation: useCallback((title?: string) => vm.createConversation(title), [vm]),
    clearState: useCallback(() => vm.clearState(), [vm]),
    setAccessToken: useCallback((token: string | null) => vm.setAccessToken(token), [vm]),
  };
}
