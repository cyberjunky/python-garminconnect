import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

test("REQ-017 / P17: CoachModelSelect.tsx es puramente estático e informativo sin elementos <select>", () => {
  const modelSelectPath = path.join(webRoot, "components", "CoachModelSelect.tsx");
  assert.ok(fs.existsSync(modelSelectPath), "CoachModelSelect.tsx debe existir");

  const content = fs.readFileSync(modelSelectPath, "utf-8");

  // No debe contener <select ni <option
  assert.doesNotMatch(
    content,
    /<select/i,
    "CoachModelSelect.tsx no debe contener etiqueta <select (selector de modelos eliminado)"
  );
  assert.doesNotMatch(
    content,
    /<option/i,
    "CoachModelSelect.tsx no debe contener etiquetas <option"
  );

  // Debe contener la identificación estática exclusiva de GPT-6 Luna · High
  assert.match(
    content,
    /GPT-6 Luna\s*·\s*High/i,
    "CoachModelSelect.tsx debe mostrar el texto informativo estático 'GPT-6 Luna · High' (REQ-017)"
  );
});

test("REQ-017 / P17: Ambas vistas CoachChat y CoachChatScreen carecen de selectores de modelos", () => {
  const coachChatPath = path.join(webRoot, "components", "CoachChat.tsx");
  const coachChatScreenPath = path.join(webRoot, "components", "CoachChatScreen.tsx");

  const chatContent = fs.readFileSync(coachChatPath, "utf-8");
  const screenContent = fs.readFileSync(coachChatScreenPath, "utf-8");

  assert.doesNotMatch(
    chatContent,
    /<select/i,
    "CoachChat.tsx no debe ofrecer un menú interactivo <select para alternar modelos"
  );
  assert.doesNotMatch(
    screenContent,
    /<select/i,
    "CoachChatScreen.tsx no debe ofrecer un menú interactivo <select para alternar modelos"
  );
});
