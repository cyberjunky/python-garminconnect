import test from "node:test";
import assert from "node:assert";
import { formatDateEsCO, formatLastUpdatedLabel } from "./lastUpdated.ts";
import { formatGarminStatus, sportLabel } from "./lastActivity.ts";


test("formatDateEsCO formats dates with Spanish locale", () => {
  const formatted = formatDateEsCO("2026-12-31");
  assert.match(formatted, /31/);
  assert.match(formatted, /dic/i);
  assert.match(formatted, /2026/);

  // Falsy values
  assert.strictEqual(formatDateEsCO(null), "—");
  assert.strictEqual(formatDateEsCO(undefined), "—");
  assert.strictEqual(formatDateEsCO(""), "—");
});

test("formatLastUpdatedLabel produces friendly Spanish text", () => {
  const baseDate = new Date("2026-10-13T16:47:00Z"); // 11:47 in Bogota
  const labelToday = formatLastUpdatedLabel("2026-10-13T16:47:00Z", baseDate);
  assert.strictEqual(labelToday, "Actualizado hoy a las 11:47");

  const labelYesterday = formatLastUpdatedLabel("2026-10-12T16:47:00Z", baseDate);
  assert.strictEqual(labelYesterday, "Actualizado ayer a las 11:47");

  const labelEmpty = formatLastUpdatedLabel(null, baseDate);
  assert.strictEqual(labelEmpty, "Sin datos de actualización");
});

test("sportLabel translates raw English sports to Spanish", () => {
  assert.strictEqual(sportLabel("running"), "Carrera");
  assert.strictEqual(sportLabel("run"), "Carrera");
  assert.strictEqual(sportLabel("cycling"), "Ciclismo");
  assert.strictEqual(sportLabel("bike"), "Ciclismo");
  assert.strictEqual(sportLabel("swimming"), "Natación");
  assert.strictEqual(sportLabel("swim"), "Natación");
  assert.strictEqual(sportLabel("treadmill_running"), "Cinta");
  assert.strictEqual(sportLabel("lap_swimming"), "Natación en piscina");
});

test("formatGarminStatus translates raw Garmin training status to Spanish", () => {
  assert.strictEqual(formatGarminStatus("MAINTAINING"), "Mantenimiento");
  assert.strictEqual(formatGarminStatus("PRODUCTIVE"), "Productivo");
  assert.strictEqual(formatGarminStatus("RECOVERY"), "Recuperación");
  assert.strictEqual(formatGarminStatus("UNPRODUCTIVE"), "No productivo");
  assert.strictEqual(formatGarminStatus("OVERREACHING"), "Sobreesfuerzo");
  assert.strictEqual(formatGarminStatus("DETRAINING"), "Desentrenamiento");
  assert.strictEqual(formatGarminStatus(null), "—");
});

test("globals.css mobile layout enforces minmax(0, 1fr) and min-width: 0", async () => {
  const fs = await import("node:fs");
  const css = fs.readFileSync(new URL("../app/globals.css", import.meta.url), "utf-8");
  assert.match(css, /grid-template-columns:\s*minmax\(0,\s*1fr\)/);
  assert.match(css, /\.dash-nav-container[\s\S]*?min-width:\s*0/);
  assert.match(css, /\.dash-nav[\s\S]*?min-width:\s*0/);
  assert.match(css, /\.dash-nav-scroll-area[\s\S]*?min-width:\s*0/);
});

test("chat API route returns friendly Spanish copy and no technical leaks", async () => {
  const fs = await import("node:fs");
  const route = fs.readFileSync(new URL("../app/api/chat/route.ts", import.meta.url), "utf-8");
  assert.match(route, /El servicio del entrenador no está disponible en este momento/);
  assert.doesNotMatch(route, /error:\s*"Falta OPENAI_API_KEY/);
});

