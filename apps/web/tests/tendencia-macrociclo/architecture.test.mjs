import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

test("REQ-019 / P19 (P22): Clean Architecture - lib/tendencia.ts no importa React, Next.js ni componentes UI", () => {
  const tendenciaPath = path.join(webRoot, "lib", "tendencia.ts");
  assert.ok(fs.existsSync(tendenciaPath), "lib/tendencia.ts debe existir");
  const content = fs.readFileSync(tendenciaPath, "utf-8");

  // Prohibición estricta de UI en dominio
  assert.doesNotMatch(content, /from\s+['"]react['"]/, "lib/tendencia.ts no debe importar React");
  assert.doesNotMatch(content, /from\s+['"]react-dom['"]/, "lib/tendencia.ts no debe importar ReactDOM");
  assert.doesNotMatch(content, /from\s+['"]next(\/.*)?['"]/, "lib/tendencia.ts no debe importar Next.js");
  assert.doesNotMatch(content, /from\s+['"]@\/components\/.*['"]/, "lib/tendencia.ts no debe importar componentes UI");

  // No debe importar directamente el cliente de base de datos cloud @supabase/supabase-js
  assert.doesNotMatch(
    content,
    /from\s+['"]@supabase\/supabase-js['"]/,
    "lib/tendencia.ts no debe importar @supabase/supabase-js directamente; debe usar la capa de infraestructura @/lib/infra/supabase"
  );
});

test("REQ-019 / P19 (P22): Clean Architecture - DashboardNav no acopla infraestructura ni persistencia", () => {
  const navPath = path.join(webRoot, "components", "DashboardNav.tsx");
  assert.ok(fs.existsSync(navPath), "DashboardNav.tsx debe existir");
  const content = fs.readFileSync(navPath, "utf-8");

  assert.doesNotMatch(content, /@supabase/, "DashboardNav.tsx no debe importar Supabase");
  assert.doesNotMatch(content, /infra\/supabase/, "DashboardNav.tsx no debe importar cliente de infraestructura");
});

test("REQ-019 / P19 (P22): Clean Architecture - page.tsx delega cálculos puros en lib/tendencia.ts", () => {
  const pagePath = path.join(webRoot, "app", "(dashboard)", "tendencia", "page.tsx");
  assert.ok(fs.existsSync(pagePath), "app/(dashboard)/tendencia/page.tsx debe existir");
  const content = fs.readFileSync(pagePath, "utf-8");

  // Comprueba que importa las funciones puras o adaptador de lib/tendencia.ts
  assert.match(
    content,
    /from\s+['"]@\/lib\/tendencia['"]|from\s+['"]\.\.\/\.\.\/\.\.\/lib\/tendencia['"]/,
    "tendencia/page.tsx debe delegar su lógica en lib/tendencia.ts"
  );
});
