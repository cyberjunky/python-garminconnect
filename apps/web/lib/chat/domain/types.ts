export type MessageRole = "user" | "assistant" | "system";

export type OperationStatus = "in_progress" | "completed" | "failed";

export type ImportStatus = "imported" | "skipped" | "failed";

export interface Conversation {
  id: string;
  ownerId: string;
  title: string;
  revision: number;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  conversationId: string;
  ownerId: string;
  sequence: number;
  role: MessageRole;
  content: string;
  createdAt: string;
}

export interface Operation {
  ownerId: string;
  operationId: string;
  conversationId: string;
  status: OperationStatus;
  resultMessageId: string | null;
  leaseUntil: string;
  createdAt: string;
  errorReason?: string;
}

export interface ImportRecord {
  id: string;
  ownerId: string;
  sourceId: string;
  sourceDigest: string;
  conversationId: string;
  status: ImportStatus;
  createdAt: string;
}

export interface ProfileLink {
  authUserId: string;
  profileId: string;
  createdAt: string;
}
