import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const migrationPath = path.resolve(
  __dirname,
  "..",
  "..",
  "migrations",
  "20261017_coach_history.sql"
);

test("Migracion 20261017_coach_history.sql contiene las 5 tablas, RLS, checks y revoke de anon", () => {
  assert.ok(fs.existsSync(migrationPath), "El archivo de migracion debe existir");
  const sql = fs.readFileSync(migrationPath, "utf-8");

  // 1. Tablas requeridas
  assert.match(sql, /create table if not exists public\.coach_conversations/i);
  assert.match(sql, /create table if not exists public\.coach_messages/i);
  assert.match(sql, /create table if not exists public\.coach_operations/i);
  assert.match(sql, /create table if not exists public\.coach_imports/i);
  assert.match(sql, /create table if not exists public\.coach_profile_links/i);

  // 2. Limite de 4000 caracteres (REQ-006)
  assert.match(sql, /char_length\s*\(\s*content\s*\)\s*<=\s*4000/i);

  // 3. RLS habilitado en las 5 tablas
  assert.match(sql, /alter table public\.coach_conversations enable row level security/i);
  assert.match(sql, /alter table public\.coach_messages enable row level security/i);
  assert.match(sql, /alter table public\.coach_operations enable row level security/i);
  assert.match(sql, /alter table public\.coach_imports enable row level security/i);
  assert.match(sql, /alter table public\.coach_profile_links enable row level security/i);

  // 4. Politicas RLS auth.uid() = owner_id
  assert.match(sql, /auth\.uid\(\)\s*=\s*owner_id/i);
  assert.match(sql, /auth\.uid\(\)\s*=\s*auth_user_id/i);

  // 5. Revocacion estricta de permisos a anon
  assert.match(sql, /revoke all on public\.coach_conversations from anon/i);
  assert.match(sql, /revoke all on public\.coach_messages from anon/i);
  assert.match(sql, /revoke all on public\.coach_operations from anon/i);
  assert.match(sql, /revoke all on public\.coach_imports from anon/i);
  assert.match(sql, /revoke all on public\.coach_profile_links from anon/i);

  // 6. Claves foraneas compuestas para evitar asignacion cruzada de propietario (REQ-005)
  assert.match(
    sql,
    /foreign key\s*\(\s*conversation_id\s*,\s*owner_id\s*\)\s*references public\.coach_conversations\s*\(\s*id\s*,\s*owner_id\s*\)/i
  );
});
