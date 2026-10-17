import test from "node:test";
import assert from "node:assert";

class MockConversationRepository {
  constructor() {
    this.conversations = new Map();
    this.messages = new Map(); // key: conversationId, value: Message[]
    this.operations = new Map(); // key: `${ownerId}:${operationId}`, value: Operation
  }

  async getConversation(ownerId, conversationId) {
    const conv = this.conversations.get(conversationId);
    if (!conv) return null;
    if (conv.ownerId !== ownerId) return null; // Aislamiento estricto de propietario (P05)
    return conv;
  }

  async createConversation(ownerId, title) {
    const id = `conv-${this.conversations.size + 1}`;
    const conv = {
      id,
      ownerId,
      title,
      revision: 1,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.conversations.set(id, conv);
    this.messages.set(id, []);
    return conv;
  }

  async listConversations(ownerId, limit = 20, offset = 0) {
    const all = Array.from(this.conversations.values())
      .filter((c) => c.ownerId === ownerId)
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
    return {
      conversations: all.slice(offset, offset + limit),
      total: all.length,
    };
  }

  async listMessages(ownerId, conversationId) {
    const conv = await this.getConversation(ownerId, conversationId);
    if (!conv) return null;
    return this.messages.get(conversationId) || [];
  }

  async getOperation(ownerId, operationId) {
    return this.operations.get(`${ownerId}:${operationId}`) || null;
  }

  async claimOperation(ownerId, operationId, conversationId, expectedRevision, userContent) {
    const conv = await this.getConversation(ownerId, conversationId);
    if (!conv) {
      const err = new Error("Conversacion no encontrada");
      err.code = "NOT_FOUND";
      throw err;
    }

    const opKey = `${ownerId}:${operationId}`;
    const existingOp = this.operations.get(opKey);
    const now = new Date();

    if (existingOp) {
      if (existingOp.status === "completed") {
        const msgs = this.messages.get(conversationId) || [];
        const resultMsg = msgs.find((m) => m.id === existingOp.resultMessageId);
        return {
          status: "ALREADY_COMPLETED",
          operation: existingOp,
          assistantMessage: resultMsg,
          conversation: conv,
        };
      }
      if (existingOp.status === "in_progress" && new Date(existingOp.leaseUntil) > now) {
        const err = new Error("Operacion en curso con lease activo");
        err.code = "OPERATION_IN_PROGRESS";
        throw err;
      }
    }

    if (conv.revision !== expectedRevision) {
      const err = new Error(`Conflicto de concurrencia: revision esperada ${expectedRevision}, actual ${conv.revision}`);
      err.code = "CONCURRENCY_CONFLICT";
      throw err;
    }

    const msgs = this.messages.get(conversationId) || [];
    const sequence = msgs.length + 1;
    const userMessage = {
      id: `msg-user-${sequence}`,
      conversationId,
      ownerId,
      sequence,
      role: "user",
      content: userContent,
      createdAt: now.toISOString(),
    };
    msgs.push(userMessage);

    const leaseUntil = new Date(now.getTime() + 30000).toISOString();
    const operation = {
      ownerId,
      operationId,
      conversationId,
      status: "in_progress",
      resultMessageId: null,
      leaseUntil,
      createdAt: now.toISOString(),
    };
    this.operations.set(opKey, operation);

    return {
      status: "CLAIMED",
      operation,
      userMessage,
      conversation: conv,
    };
  }

  async completeOperation(ownerId, operationId, conversationId, assistantContent) {
    const conv = await this.getConversation(ownerId, conversationId);
    const msgs = this.messages.get(conversationId) || [];
    const sequence = msgs.length + 1;
    const assistantMessage = {
      id: `msg-asst-${sequence}`,
      conversationId,
      ownerId,
      sequence,
      role: "assistant",
      content: assistantContent,
      createdAt: new Date().toISOString(),
    };
    msgs.push(assistantMessage);

    conv.revision += 1;
    conv.updatedAt = new Date().toISOString();

    const opKey = `${ownerId}:${operationId}`;
    const op = this.operations.get(opKey);
    if (op) {
      op.status = "completed";
      op.resultMessageId = assistantMessage.id;
    }

    return { assistantMessage, conversation: conv };
  }

  async failOperation(ownerId, operationId, errorReason) {
    const opKey = `${ownerId}:${operationId}`;
    const op = this.operations.get(opKey);
    if (op) {
      op.status = "failed";
      op.errorReason = errorReason;
    }
  }
}

class MockHealthContextPort {
  constructor(linkedOwners = new Set()) {
    this.linkedOwners = linkedOwners;
    this.callsCount = 0;
  }

  async getHealthContext(ownerId) {
    this.callsCount++;
    if (!this.linkedOwners.has(ownerId)) {
      const err = new Error("Perfil de salud no vinculado para este usuario");
      err.code = "HEALTH_PROFILE_NOT_LINKED";
      throw err;
    }
    return {
      promptText: "Contexto de salud sintetico para pruebas: Zona VERDE, HRV 55ms.",
      profileId: "00000000-0000-0000-0000-000000000001",
    };
  }
}

class MockCoachProviderPort {
  constructor(responseToReturn = "Respuesta del coach") {
    this.responseToReturn = responseToReturn;
    this.calls = [];
    this.shouldThrow = null;
  }

  async generateCoachResponse(contextPrompt, recentMessages) {
    this.calls.push({ contextPrompt, recentMessages });
    if (this.shouldThrow) {
      throw this.shouldThrow;
    }
    return this.responseToReturn;
  }
}

test("REQ-004 & REQ-005 / P04 & P05: Usuario A no accede a conversaciones de usuario B", async () => {
  const { SendMessageUseCase } = await import(
    "../../lib/chat/application/sendMessageUseCase.ts"
  );

  const repo = new MockConversationRepository();
  const health = new MockHealthContextPort(new Set(["user-A", "user-B"]));
  const coach = new MockCoachProviderPort();

  const useCase = new SendMessageUseCase({
    conversationRepository: repo,
    healthContextPort: health,
    coachProviderPort: coach,
  });

  // Usuario A crea conversacion
  const convA = await repo.createConversation("user-A", "Conversacion de A");

  // Usuario B intenta enviar un mensaje a la conversacion de A
  await assert.rejects(
    async () => {
      await useCase.execute({
        ownerId: "user-B",
        conversationId: convA.id,
        content: "Hola desde usuario B",
        operationId: "op-b-1",
        expectedRevision: 1,
      });
    },
    (err) => {
      assert.strictEqual(err.code, "NOT_FOUND");
      return true;
    }
  );

  // El historial de A no tiene mensajes de B
  const messagesA = await repo.listMessages("user-A", convA.id);
  assert.strictEqual(messagesA.length, 0);
});

test("REQ-014 / P14: Usuario sin vinculo a salud recibe 403 y no llama al modelo ni lee salud", async () => {
  const { SendMessageUseCase } = await import(
    "../../lib/chat/application/sendMessageUseCase.ts"
  );

  const repo = new MockConversationRepository();
  // Solo user-A tiene vinculo, user-unlinked no lo tiene
  const health = new MockHealthContextPort(new Set(["user-A"]));
  const coach = new MockCoachProviderPort();

  const useCase = new SendMessageUseCase({
    conversationRepository: repo,
    healthContextPort: health,
    coachProviderPort: coach,
  });

  const conv = await repo.createConversation("user-unlinked", "Mi chat");

  await assert.rejects(
    async () => {
      await useCase.execute({
        ownerId: "user-unlinked",
        conversationId: conv.id,
        content: "Hola coach",
        operationId: "op-1",
        expectedRevision: 1,
      });
    },
    (err) => {
      assert.strictEqual(err.code, "HEALTH_PROFILE_NOT_LINKED");
      return true;
    }
  );

  // Cero llamadas al coach
  assert.strictEqual(coach.calls.length, 0);
});

test("REQ-009 / P09: Operacion repetida con mismo operationId devuelve resultado guardado sin duplicar inferencia", async () => {
  const { SendMessageUseCase } = await import(
    "../../lib/chat/application/sendMessageUseCase.ts"
  );

  const repo = new MockConversationRepository();
  const health = new MockHealthContextPort(new Set(["user-A"]));
  const coach = new MockCoachProviderPort("Consejo inicial del coach");

  const useCase = new SendMessageUseCase({
    conversationRepository: repo,
    healthContextPort: health,
    coachProviderPort: coach,
  });

  const conv = await repo.createConversation("user-A", "Chat idempotencia");

  // Primera ejecucion exitosa
  const result1 = await useCase.execute({
    ownerId: "user-A",
    conversationId: conv.id,
    content: "¿Como entreno hoy?",
    operationId: "op-idempotent-1",
    expectedRevision: 1,
  });

  assert.strictEqual(result1.assistantMessage.content, "Consejo inicial del coach");
  assert.strictEqual(coach.calls.length, 1);

  // Reintento con el mismo operation_id (p. ej. doble click o reintento de red)
  const result2 = await useCase.execute({
    ownerId: "user-A",
    conversationId: conv.id,
    content: "¿Como entreno hoy?",
    operationId: "op-idempotent-1",
    expectedRevision: 1,
  });

  // Devuelve el mensaje ya guardado
  assert.strictEqual(result2.assistantMessage.id, result1.assistantMessage.id);
  assert.strictEqual(result2.assistantMessage.content, "Consejo inicial del coach");

  // CERO llamadas adicionales al LLM (no duplica inferencia)
  assert.strictEqual(coach.calls.length, 1);

  // Exactamente 2 mensajes en la conversacion (user + assistant)
  const allMessages = await repo.listMessages("user-A", conv.id);
  assert.strictEqual(allMessages.length, 2);
});

test("REQ-010 / P10: Escritura sobre revision desactualizada genera conflicto 409", async () => {
  const { SendMessageUseCase } = await import(
    "../../lib/chat/application/sendMessageUseCase.ts"
  );

  const repo = new MockConversationRepository();
  const health = new MockHealthContextPort(new Set(["user-A"]));
  const coach = new MockCoachProviderPort("Respuesta 1");

  const useCase = new SendMessageUseCase({
    conversationRepository: repo,
    healthContextPort: health,
    coachProviderPort: coach,
  });

  const conv = await repo.createConversation("user-A", "Chat concurrencia");

  // Escritor 1 avanza la revision a 2
  await useCase.execute({
    ownerId: "user-A",
    conversationId: conv.id,
    content: "Mensaje 1",
    operationId: "op-1",
    expectedRevision: 1,
  });

  // Escritor 2 envia con revision obsoleta 1
  await assert.rejects(
    async () => {
      await useCase.execute({
        ownerId: "user-A",
        conversationId: conv.id,
        content: "Mensaje concorrente con revision vieja",
        operationId: "op-2",
        expectedRevision: 1,
      });
    },
    (err) => {
      assert.strictEqual(err.code, "CONCURRENCY_CONFLICT");
      return true;
    }
  );
});

test("REQ-018 / P18: Envio al coach selecciona maximo ultimos 12 mensajes preservando historial en DB", async () => {
  const { SendMessageUseCase } = await import(
    "../../lib/chat/application/sendMessageUseCase.ts"
  );

  const repo = new MockConversationRepository();
  const health = new MockHealthContextPort(new Set(["user-A"]));
  const coach = new MockCoachProviderPort("Respuesta 21");

  const useCase = new SendMessageUseCase({
    conversationRepository: repo,
    healthContextPort: health,
    coachProviderPort: coach,
  });

  const conv = await repo.createConversation("user-A", "Chat largo");

  // Poblamos 20 mensajes previos en el repo
  const msgs = repo.messages.get(conv.id);
  for (let i = 1; i <= 20; i++) {
    msgs.push({
      id: `msg-seed-${i}`,
      conversationId: conv.id,
      ownerId: "user-A",
      sequence: i,
      role: i % 2 === 1 ? "user" : "assistant",
      content: `Mensaje previo ${i}`,
      createdAt: new Date().toISOString(),
    });
  }
  conv.revision = 21;

  // Enviamos mensaje 21
  await useCase.execute({
    ownerId: "user-A",
    conversationId: conv.id,
    content: "Pregunta numero 21",
    operationId: "op-long-21",
    expectedRevision: 21,
  });

  // Comprobamos la llamada al coach
  assert.strictEqual(coach.calls.length, 1);
  const sentMessages = coach.calls[0].recentMessages;

  // El payload al LLM tiene exactamente 12 mensajes
  assert.strictEqual(sentMessages.length, 12);
  // El ultimo enviado es la pregunta 21 del usuario
  assert.strictEqual(sentMessages[11].content, "Pregunta numero 21");

  // La base de datos tiene TODOS los 22 mensajes (20 previos + 1 user + 1 assistant)
  const dbMessages = await repo.listMessages("user-A", conv.id);
  assert.strictEqual(dbMessages.length, 22);
});

test("REQ-016 / P16: Fallo en proveedor rechaza sin sustituir modelo y deja mensaje usuario", async () => {
  const { SendMessageUseCase } = await import(
    "../../lib/chat/application/sendMessageUseCase.ts"
  );

  const repo = new MockConversationRepository();
  const health = new MockHealthContextPort(new Set(["user-A"]));
  const coach = new MockCoachProviderPort();
  const providerError = new Error("OpenAI error 500");
  providerError.code = "COACH_PROVIDER_ERROR";
  coach.shouldThrow = providerError;

  const useCase = new SendMessageUseCase({
    conversationRepository: repo,
    healthContextPort: health,
    coachProviderPort: coach,
  });

  const conv = await repo.createConversation("user-A", "Chat fallo");

  await assert.rejects(
    async () => {
      await useCase.execute({
        ownerId: "user-A",
        conversationId: conv.id,
        content: "Pregunta que fallara",
        operationId: "op-fail-1",
        expectedRevision: 1,
      });
    },
    (err) => {
      assert.strictEqual(err.code, "COACH_PROVIDER_ERROR");
      return true;
    }
  );

  // La operacion queda marcada como failed
  const op = await repo.getOperation("user-A", "op-fail-1");
  assert.strictEqual(op.status, "failed");

  // El mensaje del usuario permanece guardado para no perder su borrador
  const msgs = await repo.listMessages("user-A", conv.id);
  assert.strictEqual(msgs.length, 1);
  assert.strictEqual(msgs[0].role, "user");
  assert.strictEqual(msgs[0].content, "Pregunta que fallara");
});
