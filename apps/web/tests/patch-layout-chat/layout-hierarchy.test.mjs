import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");
const pagePath = path.join(webRoot, "app", "(dashboard)", "page.tsx");
const globalsCssPath = path.join(webRoot, "app", "globals.css");
const coachChatPath = path.join(webRoot, "components", "CoachChat.tsx");

test("REQ-003 / P03: Posicionamiento de CoachChat como primer componente en Inicio tras page-header y antes de TodayCard", () => {
  const content = fs.readFileSync(pagePath, "utf-8");

  const headerIndex = content.indexOf('<header className="page-header">');
  const coachChatIndex = content.indexOf("<CoachChat");
  const todayCardIndex = content.indexOf("<TodayCard");

  assert.ok(headerIndex !== -1, "page.tsx debe contener <header className=\"page-header\">");
  assert.ok(coachChatIndex !== -1, "page.tsx debe contener <CoachChat />");
  assert.ok(todayCardIndex !== -1, "page.tsx debe contener <TodayCard />");

  assert.ok(
    coachChatIndex > headerIndex,
    "<CoachChat /> debe ubicarse después de <header className=\"page-header\">"
  );
  assert.ok(
    coachChatIndex < todayCardIndex,
    "<CoachChat /> debe ubicarse antes de <TodayCard /> para prioridad de acceso"
  );
});

test("REQ-004 / P04: Dimensionamiento compacto de CoachChat a ~25vh con max-height 28vh, min-height 180px, compositor 2 filas y scroll en historial", () => {
  const css = fs.readFileSync(globalsCssPath, "utf-8");

  // .coach-chat bounds
  const coachChatMatch = css.match(/\.coach-chat\s*\{([^}]*)\}/);
  assert.ok(coachChatMatch, ".coach-chat debe existir en globals.css");
  assert.match(coachChatMatch[1], /max-height:\s*28vh/, ".coach-chat debe tener max-height: 28vh");
  assert.match(coachChatMatch[1], /min-height:\s*180px/, ".coach-chat debe tener min-height: 180px");

  // .coach-composer textarea compact bounds
  const composerTextareaMatch = css.match(/\.coach-composer\s+textarea\s*\{([^}]*)\}/);
  assert.ok(composerTextareaMatch, ".coach-composer textarea debe existir en globals.css");
  assert.match(composerTextareaMatch[1], /resize:\s*none/, ".coach-composer textarea debe tener resize: none");
  assert.match(composerTextareaMatch[1], /min-height:\s*2\.75rem/, ".coach-composer textarea debe tener min-height: 2.75rem");

  // .coach-history internal scroll
  const historyMatch = css.match(/\.coach-history\s*\{([^}]*)\}/);
  assert.ok(historyMatch, ".coach-history debe existir en globals.css");
  assert.match(historyMatch[1], /overflow-y:\s*auto/, ".coach-history debe tener overflow-y: auto");

  // CoachChat.tsx textarea rows={2}
  const componentContent = fs.readFileSync(coachChatPath, "utf-8");
  assert.match(
    componentContent,
    /<textarea[\s\S]*?rows=\{2\}/,
    "CoachChat.tsx debe renderizar textarea con rows={2}"
  );
});
