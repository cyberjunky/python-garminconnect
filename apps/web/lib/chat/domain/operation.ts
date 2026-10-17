import type { Operation } from "./types";

export const OPERATION_LEASE_MS = 30_000;

export function isOperationLeaseActive(operation: Operation, now: Date = new Date()): boolean {
  if (operation.status !== "in_progress") {
    return false;
  }
  const leaseEnd = new Date(operation.leaseUntil).getTime();
  return leaseEnd > now.getTime();
}

export function canClaimOperation(operation: Operation | null, now: Date = new Date()): boolean {
  if (!operation) {
    return true;
  }
  if (operation.status === "completed") {
    return false;
  }
  if (operation.status === "in_progress") {
    return !isOperationLeaseActive(operation, now);
  }
  // status === 'failed' can be retried
  return true;
}

export function computeLeaseUntil(from: Date = new Date()): string {
  return new Date(from.getTime() + OPERATION_LEASE_MS).toISOString();
}
