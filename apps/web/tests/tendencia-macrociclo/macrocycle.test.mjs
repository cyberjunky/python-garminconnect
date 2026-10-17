import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { register } from "node:module";

register(new URL("../chat-server/ts-resolver.mjs", import.meta.url));

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

test("REQ-007 / P07: getMacrocycleDetails estructura los 4 bloques delimitados", async () => {
  const { getMacrocycleDetails } = await import("../../lib/mesocycle.ts");

  const details = getMacrocycleDetails("2026-10-17");

  // Bloque A: Definición
  assert.ok(details.definition, "Bloque A (definition) debe existir");
  assert.ok(details.definition.title, "Bloque A debe tener título");
  assert.ok(details.definition.text, "Bloque A debe tener texto explicativo");

  // Bloque B: Momento y fase actual
  assert.ok(details.currentPhase, "Bloque B (currentPhase) debe existir");
  assert.strictEqual(details.currentPhase.code, "R1");
  assert.ok(details.currentPhase.name);
  assert.ok(details.currentPhase.focus);
  assert.ok(details.currentPhase.sport);
  assert.strictEqual(typeof details.currentPhase.hrCap, "number");
  assert.strictEqual(typeof details.currentPhase.maxDurationMin, "number");

  // Bloque C: Cómo mejorarla
  assert.ok(details.howToImprove, "Bloque C (howToImprove) debe existir");
  assert.ok(details.howToImprove.title);
  assert.ok(details.howToImprove.recommendation);

  // Bloque D: Cuándo termina e hitos
  assert.ok(details.timing, "Bloque D (timing) debe existir");
  assert.ok(details.timing.phaseEndDateFormatted);
  assert.strictEqual(typeof details.timing.daysRemainingPhase, "number");
  assert.ok(Array.isArray(details.timing.milestones));
  assert.ok(details.timing.milestones.length >= 3);
});

test("REQ-008 / P08: Explicación pedagógica del concepto de macrociclo en Bloque A", async () => {
  const { getMacrocycleDetails } = await import("../../lib/mesocycle.ts");

  const details = getMacrocycleDetails("2026-10-17");
  const text = details.definition.text;

  // Debe explicar periodización plurianual hacia objetivos mayores
  assert.match(
    text,
    /(periodizaci[oó]n|planificaci[oó]n|temporada|plurianual)/i,
    "Bloque A debe explicar la periodización o planificación de temporada"
  );
  assert.match(
    text,
    /(fases|pico de rendimiento|adaptaci[oó]n|mitocondrial|resistencia)/i,
    "Bloque A debe explicar la función de las fases en la progresión física"
  );
  assert.match(
    text,
    /(mmB|Bogot[aá]|Letras|Cartagena|70\.3)/i,
    "Bloque A debe vincular la planificación a los hitos de la temporada"
  );
});

test("REQ-009 / P09: Detalle de momento/fase actual con techo de FC y duración máxima en Bloque B", async () => {
  const { getMacrocycleDetails } = await import("../../lib/mesocycle.ts");

  // Fecha en fase R1 (6 oct 2026 - 31 dic 2026)
  const r1Details = getMacrocycleDetails("2026-10-17");
  assert.strictEqual(r1Details.currentPhase.code, "R1");
  assert.match(r1Details.currentPhase.name, /Base aer[oó]bica/i);
  assert.strictEqual(r1Details.currentPhase.focus, "80/20 Z1-Z2");
  assert.strictEqual(r1Details.currentPhase.sport, "run+bike");
  assert.strictEqual(r1Details.currentPhase.hrCap, 135);
  assert.strictEqual(r1Details.currentPhase.maxDurationMin, 75);

  // Fecha en fase R2 (1 ene 2027 - 31 mar 2027)
  const r2Details = getMacrocycleDetails("2027-02-15");
  assert.strictEqual(r2Details.currentPhase.code, "R2");
  assert.match(r2Details.currentPhase.name, /Construcci[oó]n/i);
  assert.strictEqual(r2Details.currentPhase.sport, "run");
  assert.strictEqual(r2Details.currentPhase.hrCap, 141);
  assert.strictEqual(r2Details.currentPhase.maxDurationMin, 90);

  // Fecha en fase R0 (20 sep 2026 - 5 oct 2026)
  const r0Details = getMacrocycleDetails("2026-09-25");
  assert.strictEqual(r0Details.currentPhase.code, "R0");
  assert.match(r0Details.currentPhase.name, /Recuperaci[oó]n/i);
  assert.strictEqual(r0Details.currentPhase.hrCap, 128);
  assert.strictEqual(r0Details.currentPhase.maxDurationMin, 45);
});

test("REQ-010 / P10: Recomendación práctica contextualizada según fase y fatiga en Bloque C", async () => {
  const { getMacrocycleDetails } = await import("../../lib/mesocycle.ts");

  // R1 en estado verde / óptimo
  const normalDetails = getMacrocycleDetails("2026-10-17", undefined, undefined, "VERDE", 1.05);
  assert.match(
    normalDetails.howToImprove.recommendation,
    /(Z1|Z2|135|mitocondrial|aer[oó]bic|disciplina|volumen suave)/i,
    "Para R1 verde debe prescribir disciplina estricta en Z1-Z2 (< 135 bpm)"
  );

  // R1 con fatiga / estado no verde o ACWR alto
  const fatigueDetails = getMacrocycleDetails("2026-10-17", undefined, undefined, "AMARILLO", 1.42);
  assert.match(
    fatigueDetails.howToImprove.recommendation,
    /(fatiga|carga|asimilar|recuperaci[oó]n|suave|modul|descanso)/i,
    "Con fatiga o ACWR alto debe modular recomendación hacia recuperación/asimilación"
  );
});

test("REQ-011 / P11: Fecha fin en formato es-CO, días restantes y lista de hitos en Bloque D", async () => {
  const { getMacrocycleDetails } = await import("../../lib/mesocycle.ts");

  // Del 2026-10-17 al 2026-12-31 son exactamente 75 días
  const details = getMacrocycleDetails("2026-10-17");

  // Fecha fin de R1 formateada en es-CO: "31 dic 2026" o "31 de dic de 2026"
  assert.match(
    details.timing.phaseEndDateFormatted.toLowerCase(),
    /31(?:\s+de)?\s+dic(?:\.|\s+de)?\s+2026/i,
    "Fecha fin formateada en es-CO debe coincidir con formato de fecha colombiana"
  );
  assert.strictEqual(details.timing.daysRemainingPhase, 75);

  // Hitos principales presentes
  const ms = details.timing.milestones;
  const mmb = ms.find((m) => m.code === "mmb_2027");
  const letras = ms.find((m) => m.code === "reto_letras_2027");
  const cartagena = ms.find((m) => m.code === "cartagena_703_2027");

  assert.ok(mmb, "Hito mmB 2027 debe estar en la lista");
  assert.match(mmb.eventDateFormatted.toLowerCase(), /25(?:\s+de)?\s+jul(?:\.|\s+de)?\s+2027/i);
  assert.strictEqual(mmb.daysRemaining, 281); // 2026-10-17 a 2027-07-25: 281 días

  assert.ok(letras, "Hito Reto Letras 2027 debe estar en la lista");
  assert.match(letras.eventDateFormatted.toLowerCase(), /13(?:\s+de)?\s+sep(t)?(?:\.|\s+de)?\s+2027/i);
  assert.strictEqual(letras.daysRemaining, 331); // 2026-10-17 a 2027-09-13: 331 días

  assert.ok(cartagena, "Hito Cartagena 70.3 2027 debe estar en la lista");
  assert.match(cartagena.eventDateFormatted.toLowerCase(), /29(?:\s+de)?\s+nov(?:\.|\s+de)?\s+2027/i);
  assert.strictEqual(cartagena.daysRemaining, 408); // 2026-10-17 a 2027-11-29: 408 días
});

test("REQ-012 / P12: En /retos, retiro de tendencia histórica 14d y preservación de secciones", () => {
  const retosPagePath = path.join(webRoot, "app", "(dashboard)", "retos", "page.tsx");
  const content = fs.readFileSync(retosPagePath, "utf-8");

  // Retiro estricto de Tendencia 14d
  assert.doesNotMatch(
    content,
    /Tendencia\s+14d/i,
    "retos/page.tsx NO debe contener la sección 'Tendencia 14d'"
  );
  assert.doesNotMatch(
    content,
    /<table[^>]*className=['"][^'"]*history-table/i,
    "retos/page.tsx NO debe renderizar la tabla de historial de 14 días"
  );

  // Preservación de las demás secciones
  assert.match(content, /Preparación vs retos/i, "Debe preservar 'Preparación vs retos'");
  assert.match(content, /Sesión/i, "Debe preservar 'Sesión'");
  assert.match(content, /Qué atender/i, "Debe preservar 'Qué atender'");
  assert.match(content, /Qué va bien/i, "Debe preservar 'Qué va bien'");
  assert.match(content, /Macrociclo/i, "Debe contener tarjeta 'Macrociclo'");

  // La tarjeta macrociclo debe incluir estructura de 4 bloques delimitados (A, B, C, D)
  assert.match(
    content,
    /(macrocycle-block|macro-block|block-a|bloque)/i,
    "La tarjeta de Macrociclo debe delimitar los 4 bloques semánticos"
  );
});

test("REQ-019 / P22: Clean Architecture - lib/mesocycle.ts no importa React, Next ni Supabase", () => {
  const mesocyclePath = path.join(webRoot, "lib", "mesocycle.ts");
  const content = fs.readFileSync(mesocyclePath, "utf-8");

  assert.doesNotMatch(content, /from\s+['"]react['"]/, "mesocycle.ts no debe importar React");
  assert.doesNotMatch(content, /from\s+['"]next(\/.*)?['"]/, "mesocycle.ts no debe importar Next.js");
  assert.doesNotMatch(content, /from\s+['"]@supabase\//, "mesocycle.ts no debe importar Supabase");
});
