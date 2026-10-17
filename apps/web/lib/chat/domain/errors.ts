export class DomainError extends Error {
  public readonly code: string;
  public readonly statusCode: number;

  constructor(message: string, code: string = "DOMAIN_ERROR", statusCode: number = 400) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
  }
}

export class ValidationError extends DomainError {
  constructor(message: string, code: string = "VALIDATION_ERROR") {
    super(message, code, 400);
  }
}

export class UnauthorizedError extends DomainError {
  constructor(message: string = "Sesión no válida o expirada", code: string = "UNAUTHORIZED") {
    super(message, code, 401);
  }
}

export class ForbiddenError extends DomainError {
  constructor(message: string = "Acceso no autorizado", code: string = "FORBIDDEN") {
    super(message, code, 403);
  }
}

export class HealthProfileNotLinkedError extends DomainError {
  constructor(
    message: string = "La cuenta no tiene un perfil de salud vinculado",
    code: string = "HEALTH_PROFILE_NOT_LINKED"
  ) {
    super(message, code, 403);
  }
}

export class NotFoundError extends DomainError {
  constructor(message: string = "Recurso no encontrado", code: string = "NOT_FOUND") {
    super(message, code, 404);
  }
}

export class ConcurrencyConflictError extends DomainError {
  constructor(
    message: string = "Conflicto de concurrencia: la conversación ha sido modificada por otra sesión",
    code: string = "CONCURRENCY_CONFLICT"
  ) {
    super(message, code, 409);
  }
}

export class OperationLeaseActiveError extends DomainError {
  constructor(
    message: string = "Existe una operación en curso con lease activo para esta solicitud",
    code: string = "OPERATION_IN_PROGRESS"
  ) {
    super(message, code, 409);
  }
}

export class CoachProviderError extends DomainError {
  constructor(
    message: string = "Error en el proveedor de inferencia",
    statusCode: number = 502,
    code: string = "COACH_PROVIDER_ERROR"
  ) {
    super(message, code, statusCode);
  }
}
