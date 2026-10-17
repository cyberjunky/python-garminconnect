import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

test("REQ-001 & REQ-002 / P01 & P02: globals.css preserva centrado max-width 1120px en dashboard y 880px en compositor de chat", () => {
  const cssPath = path.join(webRoot, "app", "globals.css");
  assert.ok(fs.existsSync(cssPath), "globals.css debe existir");

  const css = fs.readFileSync(cssPath, "utf-8");

  // Regla del contenedor principal dashboard
  const mainRuleMatch = /\.app-main\s*>\s*main\s*\{([^}]+)\}/s.exec(css);
  assert.ok(mainRuleMatch, "Debe existir la regla .app-main > main en globals.css");
  const mainRule = mainRuleMatch[1];

  assert.match(mainRule, /max-width:\s*1120px/, ".app-main > main debe conservar max-width: 1120px");
  assert.match(mainRule, /margin:\s*0\s+auto/, ".app-main > main debe conservar margin: 0 auto para centrado");
  assert.match(mainRule, /padding:\s*1\.5rem\s+28px\s+3rem/, ".app-main > main debe conservar padding 28px en viewport grande");

  // Regla del compositor de chat
  const chatComposerMatch = /\.chat-composer\s*\{([^}]+)\}/s.exec(css);
  assert.ok(chatComposerMatch, "Debe existir la regla .chat-composer en globals.css");
  const chatComposerRule = chatComposerMatch[1];

  assert.match(chatComposerRule, /max-width:\s*880px/, ".chat-composer debe tener max-width: 880px");
  assert.match(chatComposerRule, /margin:\s*0\s+auto/, ".chat-composer debe tener margin: 0 auto para centrado");

  // Breakpoint <=800px para dashboard padding 16px
  const media800Match = /@media\s*\(\s*max-width:\s*800px\s*\)\s*\{([\s\S]+?)\n\}/.exec(css);
  assert.ok(media800Match, "Debe existir bloque media query para max-width: 800px");
  assert.match(
    media800Match[1],
    /padding:\s*1\.25rem\s+16px\s+2\.5rem/,
    ".app-main > main debe aplicar padding 16px en viewport móvil"
  );
});

test("REQ-003 / P03: Componentes de chat conservan burbujas y roles accesibles", () => {
  const cssPath = path.join(webRoot, "app", "globals.css");
  const css = fs.readFileSync(cssPath, "utf-8");

  assert.match(css, /\.coach-bubble/, "globals.css debe incluir estilos para .coach-bubble");
  assert.match(css, /\.chat-row-user/, "globals.css debe incluir alineación para .chat-row-user");
  assert.match(css, /\.chat-row-assistant/, "globals.css debe incluir alineación para .chat-row-assistant");
});
