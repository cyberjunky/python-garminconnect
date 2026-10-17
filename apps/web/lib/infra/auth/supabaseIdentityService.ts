import type { SupabaseClient } from "@supabase/supabase-js";
import type { IIdentityService } from "../../chat/application/ports";
import { UnauthorizedError } from "../../chat/domain/errors";
import { getSupabaseAnon } from "../supabase";

export interface SupabaseIdentityServiceOptions {
  supabaseClient?: SupabaseClient;
}

export class SupabaseIdentityService implements IIdentityService {
  private readonly supabaseClient: SupabaseClient;

  constructor(options: SupabaseIdentityServiceOptions = {}) {
    this.supabaseClient = options.supabaseClient || getSupabaseAnon();
  }

  async authenticateUser(
    authHeader: string | null | undefined
  ): Promise<{ userId: string; email?: string }> {
    if (!authHeader || typeof authHeader !== "string") {
      throw new UnauthorizedError("Falta la cabecera de autorización");
    }

    const match = /^Bearer\s+(.+)$/i.exec(authHeader.trim());
    if (!match || !match[1]) {
      throw new UnauthorizedError("Formato de autorización no válido. Debe ser Bearer <token>");
    }

    const token = match[1];

    const {
      data: { user },
      error,
    } = await this.supabaseClient.auth.getUser(token);

    if (error || !user) {
      throw new UnauthorizedError("Sesión no válida o expirada");
    }

    return {
      userId: user.id,
      email: user.email,
    };
  }
}
