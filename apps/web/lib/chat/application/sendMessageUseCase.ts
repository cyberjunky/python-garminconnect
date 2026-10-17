import type { Message, Conversation } from "../domain/types";
import { validateMessageContent } from "../domain/validation";
import { selectContextWindow } from "../domain/windowing";
import { ValidationError } from "../domain/errors";
import type {
  IConversationRepository,
  IHealthContextPort,
  ICoachProviderPort,
} from "./ports";

export interface SendMessageInput {
  ownerId: string;
  conversationId: string;
  content: string;
  operationId: string;
  expectedRevision: number;
}

export interface SendMessageOutput {
  ok: boolean;
  assistantMessage: Message;
  conversation: Conversation;
  cached: boolean;
}

export class SendMessageUseCase {
  private readonly conversationRepository: IConversationRepository;
  private readonly healthContextPort: IHealthContextPort;
  private readonly coachProviderPort: ICoachProviderPort;

  constructor(ports: {
    conversationRepository: IConversationRepository;
    healthContextPort: IHealthContextPort;
    coachProviderPort: ICoachProviderPort;
  }) {
    this.conversationRepository = ports.conversationRepository;
    this.healthContextPort = ports.healthContextPort;
    this.coachProviderPort = ports.coachProviderPort;
  }

  async execute(input: SendMessageInput): Promise<SendMessageOutput> {
    if (!input.ownerId?.trim()) {
      throw new ValidationError("Falta el identificador del propietario", "MISSING_OWNER_ID");
    }
    if (!input.conversationId?.trim()) {
      throw new ValidationError("Falta el identificador de conversación", "MISSING_CONVERSATION_ID");
    }
    if (!input.operationId?.trim()) {
      throw new ValidationError("Falta el identificador de operación", "MISSING_OPERATION_ID");
    }
    if (typeof input.expectedRevision !== "number" || input.expectedRevision < 1) {
      throw new ValidationError("Revisión esperada no válida", "INVALID_REVISION");
    }

    // 1. Valida longitud máxima de 4000 caracteres (REQ-006)
    const validContent = validateMessageContent(input.content);

    // 2. Comprueba vinculo con perfil de salud MVP (REQ-014)
    // Si no está vinculado, lanza error 403 y se detiene ANTES de llamar al coach
    const healthContext = await this.healthContextPort.getHealthContext(input.ownerId);

    // 3. Reclama la operación en el repositorio con lease (REQ-009, REQ-010)
    const claimResult = await this.conversationRepository.claimOperation(
      input.ownerId,
      input.operationId,
      input.conversationId,
      input.expectedRevision,
      validContent
    );

    // Si ya habia sido completada previamente (idempotencia pura), devuelve el resultado guardado
    if (claimResult.status === "ALREADY_COMPLETED") {
      return {
        ok: true,
        assistantMessage: claimResult.assistantMessage,
        conversation: claimResult.conversation,
        cached: true,
      };
    }

    // 4. Obtiene historial completo y extrae la ventana de los ultimos 12 mensajes (REQ-018)
    const allMessages = (await this.conversationRepository.listMessages(
      input.ownerId,
      input.conversationId
    )) || [];
    const contextWindow = selectContextWindow(allMessages, 12);
    const recentPayload = contextWindow.map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));

    // 5. Llama al modelo exclusivo gpt-6-luna (REQ-015, REQ-016)
    let replyContent: string;
    try {
      replyContent = await this.coachProviderPort.generateCoachResponse(
        healthContext.promptText,
        recentPayload
      );
    } catch (err) {
      const reason = err instanceof Error ? err.message : String(err);
      await this.conversationRepository.failOperation(
        input.ownerId,
        input.operationId,
        reason
      );
      throw err;
    }

    // 6. Persiste la respuesta del asistente y marca la operación completada
    const completed = await this.conversationRepository.completeOperation(
      input.ownerId,
      input.operationId,
      input.conversationId,
      replyContent
    );

    return {
      ok: true,
      assistantMessage: completed.assistantMessage,
      conversation: completed.conversation,
      cached: false,
    };
  }
}
