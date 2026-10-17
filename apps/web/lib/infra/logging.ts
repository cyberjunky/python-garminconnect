export interface TechnicalLogEntry {
  operationId?: string;
  conversationId?: string;
  statusCode?: number;
  durationMs?: number;
  result: "success" | "error" | "conflict" | "unauthorized" | "forbidden" | "not_found";
  code?: string;
  timestamp: string;
}

const ALLOWED_KEYS = new Set([
  "operationId",
  "conversationId",
  "statusCode",
  "durationMs",
  "result",
  "code",
  "timestamp",
]);

export function sanitizeForLogging(raw: Record<string, unknown>): TechnicalLogEntry {
  const resultValue = (typeof raw.result === "string" ? raw.result : "success") as TechnicalLogEntry["result"];
  const entry: TechnicalLogEntry = {
    result: resultValue,
    timestamp: typeof raw.timestamp === "string" ? raw.timestamp : new Date().toISOString(),
  };

  if (typeof raw.operationId === "string") {
    entry.operationId = raw.operationId;
  }
  if (typeof raw.conversationId === "string") {
    entry.conversationId = raw.conversationId;
  }
  if (typeof raw.statusCode === "number") {
    entry.statusCode = raw.statusCode;
  }
  if (typeof raw.durationMs === "number") {
    entry.durationMs = Math.round(raw.durationMs);
  }
  if (typeof raw.code === "string") {
    entry.code = raw.code;
  }

  return entry;
}

export function formatTechnicalLog(entry: TechnicalLogEntry): string {
  const parts = [
    `[COACH_AUDIT]`,
    `time=${entry.timestamp}`,
    `result=${entry.result}`,
  ];
  if (entry.operationId) parts.push(`op=${entry.operationId}`);
  if (entry.conversationId) parts.push(`conv=${entry.conversationId}`);
  if (entry.statusCode) parts.push(`status=${entry.statusCode}`);
  if (entry.durationMs !== undefined) parts.push(`duration=${entry.durationMs}ms`);
  if (entry.code) parts.push(`code=${entry.code}`);

  return parts.join(" ");
}

export function logTechnicalEvent(raw: Record<string, unknown>): void {
  const sanitized = sanitizeForLogging(raw);
  const formatted = formatTechnicalLog(sanitized);
  if (sanitized.result === "error") {
    console.error(formatted);
  } else {
    console.log(formatted);
  }
}
