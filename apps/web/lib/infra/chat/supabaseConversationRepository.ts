import type { SupabaseClient } from "@supabase/supabase-js";
import type {
  IConversationRepository,
  ClaimOperationResult,
} from "../../chat/application/ports";
import type {
  Conversation,
  Message,
  Operation,
} from "../../chat/domain/types";
import {
  ConcurrencyConflictError,
  NotFoundError,
  OperationLeaseActiveError,
} from "../../chat/domain/errors";
import { computeLeaseUntil, isOperationLeaseActive } from "../../chat/domain/operation";
import { getSupabaseAnon } from "../supabase";

export interface SupabaseConversationRepositoryOptions {
  supabaseClient?: SupabaseClient;
}

export class SupabaseConversationRepository implements IConversationRepository {
  private readonly supabaseClient: SupabaseClient;

  constructor(options: SupabaseConversationRepositoryOptions = {}) {
    this.supabaseClient = options.supabaseClient || getSupabaseAnon();
  }

  async getConversation(ownerId: string, conversationId: string): Promise<Conversation | null> {
    const { data, error } = await this.supabaseClient
      .from("coach_conversations")
      .select("id, owner_id, title, revision, created_at, updated_at")
      .eq("id", conversationId)
      .eq("owner_id", ownerId)
      .maybeSingle();

    if (error || !data) {
      return null;
    }

    return {
      id: data.id,
      ownerId: data.owner_id,
      title: data.title,
      revision: data.revision,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
    };
  }

  async createConversation(ownerId: string, title: string): Promise<Conversation> {
    const { data, error } = await this.supabaseClient
      .from("coach_conversations")
      .insert({
        owner_id: ownerId,
        title,
        revision: 1,
      })
      .select("id, owner_id, title, revision, created_at, updated_at")
      .single();

    if (error || !data) {
      throw new Error(`Error al crear la conversación: ${error?.message || "Sin datos"}`);
    }

    return {
      id: data.id,
      ownerId: data.owner_id,
      title: data.title,
      revision: data.revision,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
    };
  }

  async listConversations(
    ownerId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<{ conversations: Conversation[]; total: number }> {
    const { data, error, count } = await this.supabaseClient
      .from("coach_conversations")
      .select("id, owner_id, title, revision, created_at, updated_at", { count: "exact" })
      .eq("owner_id", ownerId)
      .order("updated_at", { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) {
      throw new Error(`Error al listar conversaciones: ${error.message}`);
    }

    const conversations: Conversation[] = (data || []).map((row) => ({
      id: row.id,
      ownerId: row.owner_id,
      title: row.title,
      revision: row.revision,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    }));

    return {
      conversations,
      total: count ?? conversations.length,
    };
  }

  async listMessages(ownerId: string, conversationId: string): Promise<Message[] | null> {
    const conv = await this.getConversation(ownerId, conversationId);
    if (!conv) {
      return null;
    }

    const { data, error } = await this.supabaseClient
      .from("coach_messages")
      .select("id, conversation_id, owner_id, sequence, role, content, created_at")
      .eq("conversation_id", conversationId)
      .eq("owner_id", ownerId)
      .order("sequence", { ascending: true });

    if (error) {
      throw new Error(`Error al leer mensajes: ${error.message}`);
    }

    return (data || []).map((row) => ({
      id: row.id,
      conversationId: row.conversation_id,
      ownerId: row.owner_id,
      sequence: row.sequence,
      role: row.role as Message["role"],
      content: row.content,
      createdAt: row.created_at,
    }));
  }

  async getOperation(ownerId: string, operationId: string): Promise<Operation | null> {
    const { data, error } = await this.supabaseClient
      .from("coach_operations")
      .select("owner_id, operation_id, conversation_id, status, result_message_id, lease_until, created_at")
      .eq("owner_id", ownerId)
      .eq("operation_id", operationId)
      .maybeSingle();

    if (error || !data) {
      return null;
    }

    return {
      ownerId: data.owner_id,
      operationId: data.operation_id,
      conversationId: data.conversation_id,
      status: data.status,
      resultMessageId: data.result_message_id,
      leaseUntil: data.lease_until,
      createdAt: data.created_at,
    };
  }

  async claimOperation(
    ownerId: string,
    operationId: string,
    conversationId: string,
    expectedRevision: number,
    userMessageContent: string
  ): Promise<ClaimOperationResult> {
    const conv = await this.getConversation(ownerId, conversationId);
    if (!conv) {
      throw new NotFoundError("Conversación no encontrada");
    }

    // 1. Verificar si la operación ya existe (idempotencia previa a chequeo de concurrencia)
    const existingOp = await this.getOperation(ownerId, operationId);
    const now = new Date();

    if (existingOp) {
      if (existingOp.status === "completed") {
        if (!existingOp.resultMessageId) {
          throw new Error("Operación marcada como completada pero sin mensaje de resultado");
        }
        const { data: msgData, error: msgError } = await this.supabaseClient
          .from("coach_messages")
          .select("id, conversation_id, owner_id, sequence, role, content, created_at")
          .eq("id", existingOp.resultMessageId)
          .eq("owner_id", ownerId)
          .single();

        if (msgError || !msgData) {
          throw new Error("No se pudo recuperar el mensaje resultante de la operación completada");
        }

        const assistantMessage: Message = {
          id: msgData.id,
          conversationId: msgData.conversation_id,
          ownerId: msgData.owner_id,
          sequence: msgData.sequence,
          role: msgData.role as Message["role"],
          content: msgData.content,
          createdAt: msgData.created_at,
        };

        return {
          status: "ALREADY_COMPLETED",
          operation: existingOp,
          assistantMessage,
          conversation: conv,
        };
      }

      if (isOperationLeaseActive(existingOp, now)) {
        throw new OperationLeaseActiveError(
          "Existe una operación en curso con lease activo para esta solicitud"
        );
      }
    }

    // 2. Si es una operación nueva o rescate, verificar revisión de concurrencia
    if (conv.revision !== expectedRevision) {
      throw new ConcurrencyConflictError(
        `Conflicto de concurrencia: revisión esperada ${expectedRevision}, actual ${conv.revision}`
      );
    }

    // Calcular siguiente sequence para el mensaje
    const { count, error: countErr } = await this.supabaseClient
      .from("coach_messages")
      .select("id", { count: "exact", head: true })
      .eq("conversation_id", conversationId)
      .eq("owner_id", ownerId);

    if (countErr) {
      throw new Error(`Error al contar mensajes existentes: ${countErr.message}`);
    }

    const nextSeq = (count ?? 0) + 1;

    // Guardar mensaje de usuario
    const { data: userMsgData, error: userMsgErr } = await this.supabaseClient
      .from("coach_messages")
      .insert({
        conversation_id: conversationId,
        owner_id: ownerId,
        sequence: nextSeq,
        role: "user",
        content: userMessageContent,
      })
      .select("id, conversation_id, owner_id, sequence, role, content, created_at")
      .single();

    if (userMsgErr || !userMsgData) {
      throw new Error(`Error al persistir mensaje de usuario: ${userMsgErr?.message || "Sin datos"}`);
    }

    const userMessage: Message = {
      id: userMsgData.id,
      conversationId: userMsgData.conversation_id,
      ownerId: userMsgData.owner_id,
      sequence: userMsgData.sequence,
      role: userMsgData.role as Message["role"],
      content: userMsgData.content,
      createdAt: userMsgData.created_at,
    };

    // Crear o renovar la operación en estado in_progress con lease
    const leaseUntil = computeLeaseUntil(now);
    const { data: opData, error: opErr } = await this.supabaseClient
      .from("coach_operations")
      .upsert({
        owner_id: ownerId,
        operation_id: operationId,
        conversation_id: conversationId,
        status: "in_progress",
        result_message_id: null,
        lease_until: leaseUntil,
      })
      .select("owner_id, operation_id, conversation_id, status, result_message_id, lease_until, created_at")
      .single();

    if (opErr || !opData) {
      throw new Error(`Error al registrar operación: ${opErr?.message || "Sin datos"}`);
    }

    const operation: Operation = {
      ownerId: opData.owner_id,
      operationId: opData.operation_id,
      conversationId: opData.conversation_id,
      status: opData.status,
      resultMessageId: opData.result_message_id,
      leaseUntil: opData.lease_until,
      createdAt: opData.created_at,
    };

    return {
      status: "CLAIMED",
      operation,
      userMessage,
      conversation: conv,
    };
  }

  async completeOperation(
    ownerId: string,
    operationId: string,
    conversationId: string,
    assistantMessageContent: string
  ): Promise<{ assistantMessage: Message; conversation: Conversation }> {
    // Siguiente secuencia para assistant
    const { count, error: countErr } = await this.supabaseClient
      .from("coach_messages")
      .select("id", { count: "exact", head: true })
      .eq("conversation_id", conversationId)
      .eq("owner_id", ownerId);

    if (countErr) {
      throw new Error(`Error al contar mensajes para respuesta: ${countErr.message}`);
    }

    const nextSeq = (count ?? 0) + 1;

    // Guardar respuesta del asistente
    const { data: asstData, error: asstErr } = await this.supabaseClient
      .from("coach_messages")
      .insert({
        conversation_id: conversationId,
        owner_id: ownerId,
        sequence: nextSeq,
        role: "assistant",
        content: assistantMessageContent,
      })
      .select("id, conversation_id, owner_id, sequence, role, content, created_at")
      .single();

    if (asstErr || !asstData) {
      throw new Error(`Error al persistir mensaje de asistente: ${asstErr?.message || "Sin datos"}`);
    }

    const assistantMessage: Message = {
      id: asstData.id,
      conversationId: asstData.conversation_id,
      ownerId: asstData.owner_id,
      sequence: asstData.sequence,
      role: asstData.role as Message["role"],
      content: asstData.content,
      createdAt: asstData.created_at,
    };

    // Incrementar revisión en conversación
    const conv = await this.getConversation(ownerId, conversationId);
    const newRevision = (conv?.revision ?? 1) + 1;

    const { data: updatedConvData, error: convErr } = await this.supabaseClient
      .from("coach_conversations")
      .update({
        revision: newRevision,
        updated_at: new Date().toISOString(),
      })
      .eq("id", conversationId)
      .eq("owner_id", ownerId)
      .select("id, owner_id, title, revision, created_at, updated_at")
      .single();

    if (convErr || !updatedConvData) {
      throw new Error(`Error al actualizar revisión de conversación: ${convErr?.message}`);
    }

    const conversation: Conversation = {
      id: updatedConvData.id,
      ownerId: updatedConvData.owner_id,
      title: updatedConvData.title,
      revision: updatedConvData.revision,
      createdAt: updatedConvData.created_at,
      updatedAt: updatedConvData.updated_at,
    };

    // Marcar operación completada con resultado
    await this.supabaseClient
      .from("coach_operations")
      .update({
        status: "completed",
        result_message_id: assistantMessage.id,
      })
      .eq("owner_id", ownerId)
      .eq("operation_id", operationId);

    return { assistantMessage, conversation };
  }

  async failOperation(ownerId: string, operationId: string, _errorReason: string): Promise<void> {
    await this.supabaseClient
      .from("coach_operations")
      .update({
        status: "failed",
      })
      .eq("owner_id", ownerId)
      .eq("operation_id", operationId);
  }
}
