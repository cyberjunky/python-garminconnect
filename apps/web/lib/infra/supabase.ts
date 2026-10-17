import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

let anonClient: SupabaseClient | null = null;

export function getSupabaseAnon(): SupabaseClient {
  if (anonClient) return anonClient;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "http://127.0.0.1:44199";
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "synthetic-local-anon-key";
  anonClient = createClient(url, key);
  return anonClient;
}

export const supabase = new Proxy({} as SupabaseClient, {
  get(_target, prop, receiver) {
    const real = getSupabaseAnon();
    const value = Reflect.get(real, prop, receiver);
    return typeof value === "function" ? value.bind(real) : value;
  },
});

export function createSupabaseUserClient(accessToken: string): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "http://127.0.0.1:44199";
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "synthetic-local-anon-key";
  return createClient(url, key, {
    global: {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  });
}

export function createSupabaseServiceClient(): SupabaseClient | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "http://127.0.0.1:44199";
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceKey) {
    return null;
  }
  return createClient(url, serviceKey);
}
