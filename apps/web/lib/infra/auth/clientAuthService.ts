import type { SupabaseClient, Session } from "@supabase/supabase-js";
import { getSupabaseAnon } from "../supabase";

export interface ClientAuthServiceOptions {
  supabaseClient?: SupabaseClient;
}

export class ClientAuthService {
  private readonly supabase: SupabaseClient;

  constructor(options: ClientAuthServiceOptions = {}) {
    this.supabase = options.supabaseClient || getSupabaseAnon();
  }

  async requestEmailOtp(email: string): Promise<{ ok: boolean; error?: string }> {
    try {
      const { error } = await this.supabase.auth.signInWithOtp({
        email: email.trim().toLowerCase(),
        options: {
          shouldCreateUser: false, // Solo usuarios invitados por administración (ADR-004)
        },
      });

      if (error) {
        return { ok: false, error: error.message };
      }
      return { ok: true };
    } catch (err) {
      return {
        ok: false,
        error: err instanceof Error ? err.message : "Error inesperado al solicitar OTP",
      };
    }
  }

  async verifyEmailOtp(
    email: string,
    token: string
  ): Promise<{ ok: boolean; session?: Session | null; error?: string }> {
    try {
      const { data, error } = await this.supabase.auth.verifyOtp({
        email: email.trim().toLowerCase(),
        token: token.trim(),
        type: "email",
      });

      if (error) {
        return { ok: false, error: error.message };
      }
      return { ok: true, session: data.session };
    } catch (err) {
      return {
        ok: false,
        error: err instanceof Error ? err.message : "Error inesperado al verificar código",
      };
    }
  }

  async getSession(): Promise<Session | null> {
    try {
      const { data, error } = await this.supabase.auth.getSession();
      if (error) return null;
      return data.session;
    } catch {
      return null;
    }
  }

  async signOut(): Promise<void> {
    try {
      await this.supabase.auth.signOut();
    } catch {
      // Ignorar errores de red en cierre de sesión local
    }
  }

  onAuthStateChange(callback: (session: Session | null) => void): { unsubscribe: () => void } {
    const {
      data: { subscription },
    } = this.supabase.auth.onAuthStateChange((_event, session) => {
      callback(session);
    });
    return {
      unsubscribe: () => subscription.unsubscribe(),
    };
  }
}
