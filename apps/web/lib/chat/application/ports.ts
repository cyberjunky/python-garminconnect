import type { Conversation, Message, Operation } from "../domain/types";

export type ClaimOperationResult =
  | {
      status: "CLAIMED";
      operation: Operation;
      userMessage: Message;
      conversation: Conversation;
    }
  | {
      status: "ALREADY_COMPLETED";
      operation: Operation;
      assistantMessage: Message;
      conversation: Conversation;
    };

export interface IConversationRepository {
  getConversation(ownerId: string, conversationId: string): Promise<Conversation | null>;
  createConversation(ownerId: string, title: string): Promise<Conversation>;
  listConversations(
    ownerId: string,
    limit?: number,
    offset?: number
  ): Promise<{ conversations: Conversation[]; total: number }>;
  listMessages(ownerId: string, conversationId: string): Promise<Message[] | null>;
  getOperation(ownerId: string, operationId: string): Promise<Operation | null>;
  claimOperation(
    ownerId: string,
    operationId: string,
    conversationId: string,
    expectedRevision: number,
    userMessageContent: string
  ): Promise<ClaimOperationResult>;
  completeOperation(
    ownerId: string,
    operationId: string,
    conversationId: string,
    assistantMessageContent: string
  ): Promise<{ assistantMessage: Message; conversation: Conversation }>;
  failOperation(ownerId: string, operationId: string, errorReason: string): Promise<void>;
}

export interface IIdentityService {
  authenticateUser(authHeader: string | null | undefined): Promise<{ userId: string; email?: string }>;
}

export interface IHealthContextPort {
  getHealthContext(ownerId: string): Promise<{ promptText: string; profileId: string }>;
}

export interface ICoachProviderPort {
  generateCoachResponse(
    contextPrompt: string,
    recentMessages: { role: string; content: string }[]
  ): Promise<string>;
}
