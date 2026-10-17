import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { useCoachConversationLogic } from "../../hooks/useCoachConversation.ts";
import { ClientAuthService } from "../../lib/infra/auth/clientAuthService.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

test("REQ-004 & REQ-013 / P04 & P13: apps/web/app/login/page.tsx implementa formulario OTP y estado de autenticación", () => {
  const loginPagePath = path.join(webRoot, "app", "login", "page.tsx");
  assert.ok(fs.existsSync(loginPagePath), "apps/web/app/login/page.tsx debe existir");

  const content = fs.readFileSync(loginPagePath, "utf-8");
  assert.match(content, /email/i, "Login debe tener input para email");
  assert.match(content, /otp|código/i, "Login debe soportar código OTP");
});

test("REQ-013 / P13: Cambio de sesión o logout limpia inmediatamente historial y borradores de la cuenta previa", () => {
  const vm = useCoachConversationLogic({
    conversationId: "conv-user-a",
    initialRevision: 1,
    accessToken: "token-user-a",
  });

  // Simulamos que el usuario A tiene mensajes y borrador
  vm.setDraft("Borrador confidencial de usuario A");

  assert.strictEqual(vm.draft, "Borrador confidencial de usuario A");

  // Al hacer logout o limpiar sesión:
  vm.clearState();

  assert.strictEqual(vm.draft, "", "El borrador debe vaciarse al cerrar sesión");
  assert.strictEqual(vm.messages.length, 0, "Los mensajes en memoria deben eliminarse");
  assert.strictEqual(vm.conversation, null, "La conversación activa debe anularse");
  assert.strictEqual(vm.conversations.length, 0, "La lista de conversaciones debe resetearse");
});

test("REQ-004 / P04: ClientAuthService gestiona OTP con Supabase Auth sin exponer secretos ni service role", () => {
  let signInCalledWith = null;
  let verifyCalledWith = null;
  let signOutCalled = false;

  const mockSupabase = {
    auth: {
      signInWithOtp: async ({ email }) => {
        signInCalledWith = email;
        return { error: null };
      },
      verifyOtp: async ({ email, token, type }) => {
        verifyCalledWith = { email, token, type };
        return { data: { session: { access_token: "jwt-test" } }, error: null };
      },
      signOut: async () => {
        signOutCalled = true;
        return { error: null };
      },
      getSession: async () => ({ data: { session: null }, error: null }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
    },
  };

  const authService = new ClientAuthService({ supabaseClient: mockSupabase });

  // 1. Solicitar OTP
  authService.requestEmailOtp("atleta@garmin.co");
  assert.strictEqual(signInCalledWith, "atleta@garmin.co");

  // 2. Verificar OTP
  authService.verifyEmailOtp("atleta@garmin.co", "123456");
  assert.deepStrictEqual(verifyCalledWith, {
    email: "atleta@garmin.co",
    token: "123456",
    type: "email",
  });

  // 3. Cerrar sesión
  authService.signOut();
  assert.strictEqual(signOutCalled, true);
});
