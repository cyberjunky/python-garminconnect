import type { Message } from "../domain/types";
import { NotFoundError } from "../domain/errors";
import type { IConversationRepository } from "./ports";

export interface GetMessagesInput {
  ownerId: string;
  conversationId: string;
}

export class GetMessagesUseCase {
  private readonly conversationRepository: IConversationRepository;

  constructor(conversationRepository: IConversationRepository) {
    this.conversationRepository = conversationRepository;
  }

  async execute(input: GetMessagesInput): Promise<Message[]> {
    const messages = await this.conversationRepository.listMessages(
      input.ownerId,
      input.conversationId
    );
    if (messages === null) {
      throw new NotFoundError("Conversación no encontrada");
    }
    return messages;
  }
}
