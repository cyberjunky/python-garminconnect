import type { Conversation } from "../domain/types";
import type { IConversationRepository } from "./ports";

export interface ListConversationsInput {
  ownerId: string;
  limit?: number;
  offset?: number;
}

export interface ListConversationsOutput {
  conversations: Conversation[];
  total: number;
}

export class ListConversationsUseCase {
  private readonly conversationRepository: IConversationRepository;

  constructor(conversationRepository: IConversationRepository) {
    this.conversationRepository = conversationRepository;
  }

  async execute(input: ListConversationsInput): Promise<ListConversationsOutput> {
    const limit = Math.min(Math.max(input.limit ?? 20, 1), 100);
    const offset = Math.max(input.offset ?? 0, 0);

    return this.conversationRepository.listConversations(input.ownerId, limit, offset);
  }
}
