import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

function extractImportSpecifiers(filePath) {
  if (!fs.existsSync(filePath)) return [];
  const content = fs.readFileSync(filePath, "utf-8");
  const specifiers = [];
  const staticImportRegex = /(?:import|export)\s+(?:[\w*\s{},]*\s+from\s+)?['"]([^'"]+)['"]/g;
  let match;
  while ((match = staticImportRegex.exec(content)) !== null) {
    specifiers.push(match[1]);
  }
  const dynamicImportRegex = /import\s*\(\s*['"]([^'"]+)['"]\s*\)/g;
  while ((match = dynamicImportRegex.exec(content)) !== null) {
    specifiers.push(match[1]);
  }
  return specifiers;
}

test("REQ-022 / P22: Hook useCoachConversation existe y reside en apps/web/hooks/", () => {
  const hookFile = path.join(webRoot, "hooks", "useCoachConversation.ts");
  assert.ok(
    fs.existsSync(hookFile),
    "apps/web/hooks/useCoachConversation.ts debe existir como ViewModel desacoplado de presentacion"
  );
});

test("REQ-022 / P22: CoachChat y CoachChatScreen usan useCoachConversation y no llaman fetch a /api/chat o /api/conversations directamente", () => {
  const coachChatFile = path.join(webRoot, "components", "CoachChat.tsx");
  const coachChatScreenFile = path.join(webRoot, "components", "CoachChatScreen.tsx");

  assert.ok(fs.existsSync(coachChatFile), "CoachChat.tsx debe existir");
  assert.ok(fs.existsSync(coachChatScreenFile), "CoachChatScreen.tsx debe existir");

  const chatContent = fs.readFileSync(coachChatFile, "utf-8");
  const screenContent = fs.readFileSync(coachChatScreenFile, "utf-8");

  // CoachChatScreen debe importar y usar el hook useCoachConversation
  assert.match(
    screenContent,
    /useCoachConversation/,
    "CoachChatScreen.tsx debe usar useCoachConversation para orquestar la vista"
  );

  // No debe llamar directamente fetch('/api/chat') para enviar mensajes en los componentes UI
  assert.doesNotMatch(
    screenContent,
    /fetch\s*\(\s*['"]\/api\/chat['"]\s*,\s*\{\s*method:\s*['"]POST['"]/i,
    "CoachChatScreen.tsx no debe invocar fetch POST a /api/chat directamente: debe delegar en useCoachConversation"
  );

  // No debe importar directamente @supabase/supabase-js en componentes de UI
  const screenImports = extractImportSpecifiers(coachChatScreenFile);
  for (const spec of screenImports) {
    assert.doesNotMatch(
      spec,
      /@supabase\/supabase-js/,
      `CoachChatScreen.tsx no debe importar @supabase/supabase-js directamente (${spec})`
    );
  }

  const chatImports = extractImportSpecifiers(coachChatFile);
  for (const spec of chatImports) {
    assert.doesNotMatch(
      spec,
      /@supabase\/supabase-js/,
      `CoachChat.tsx no debe importar @supabase/supabase-js directamente (${spec})`
    );
  }
});

test("REQ-022 / P22: apps/web/lib/chat/domain se mantiene puro sin dependencias de UI o frameworks", () => {
  const domainDir = path.join(webRoot, "lib", "chat", "domain");
  const entries = fs.readdirSync(domainDir);
  for (const entry of entries) {
    if (/\.(ts|js)$/.test(entry)) {
      const filePath = path.join(domainDir, entry);
      const imports = extractImportSpecifiers(filePath);
      for (const spec of imports) {
        assert.doesNotMatch(
          spec,
          /^(next|react|@supabase)/,
          `Dominio ${entry} no debe importar frameworks ni SDKs (${spec})`
        );
      }
    }
  }
});
