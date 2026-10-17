import { ValidationError } from "./errors";

export { ValidationError };
export const MAX_MESSAGE_CHARS = 4000;

export function validateMessageContent(raw: unknown): string {
  if (typeof raw !== "string") {
    throw new ValidationError("El contenido del mensaje debe ser un texto", "INVALID_CONTENT_TYPE");
  }

  const trimmed = raw.trim();
  if (trimmed.length === 0) {
    throw new ValidationError("El mensaje no puede estar vacío", "EMPTY_MESSAGE");
  }

  if (raw.length > MAX_MESSAGE_CHARS) {
    throw new ValidationError(
      `El mensaje supera el límite máximo permitido de ${MAX_MESSAGE_CHARS} caracteres (longitud: ${raw.length})`,
      "MESSAGE_TOO_LONG"
    );
  }

  return raw;
}

export function validateConversationTitle(raw: unknown): string {
  if (typeof raw !== "string") {
    return "Nueva conversación";
  }
  const trimmed = raw.trim();
  if (trimmed.length === 0) {
    return "Nueva conversación";
  }
  return trimmed.slice(0, 200);
}
