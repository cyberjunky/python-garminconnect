import type { Message } from "./types";

export const MAX_CONTEXT_MESSAGES = 12;

/**
 * Extracts up to MAX_CONTEXT_MESSAGES from the end of the history.
 * Does not mutate the source array.
 */
export function selectContextWindow(
  messages: readonly Message[],
  maxMessages: number = MAX_CONTEXT_MESSAGES
): Message[] {
  if (!messages || messages.length === 0) {
    return [];
  }
  return messages.slice(-maxMessages);
}
