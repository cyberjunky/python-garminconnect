import type { Conversation } from "../domain/types";
import { validateConversationTitle } from "../domain/validation";
import { ValidationError } from "../domain/errors";
import type { IConversationRepository } from "./ports";

export interface CreateConversationInput {
  ownerId: string;
  title?: string;
}

export class CreateConversationUseCase {
  private readonly conversationRepository: IConversationRepository;

  constructor(conversationRepository: IConversationRepository) {
    this.conversationRepository = conversationRepository;
  }

  async execute(input: CreateConversationInput): Promise<Conversation> {
    if (!input.ownerId?.trim()) {
      throw new ValidationError("Falta el identificador del propietario", "MISSING_OWNER_ID");
    }
    const title = validateConversationTitle(input.title);
    return this.conversationRepository.createConversation(input.ownerId, title);
  }
}
