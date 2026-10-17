import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { register } from "node:module";

register(new URL("../chat-server/ts-resolver.mjs", import.meta.url));

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

test("REQ-001 / P01: Alerta de sueño < 7.5h con recomendación fisiológica de higiene y recuperación de deuda", async () => {
  const { buildFocusRecommendations, buildFocusItems } = await import(
    "../../lib/dashboard.ts"
  );

  const readiness = {
    readiness_date: "2026-10-17",
    zone: "AMARILLO",
    score_ok: 6,
    hrv: 52,
    bb_change: 35,
    sleep_h: 5.8,
    sleep_score: 68,
    stress: 28,
    recommendation: null,
    thresholds: { sleep_h: 7.0, sleep_score: 75, hrv: 48, bb_change: 30, stress_max: 35 },
  };
  const payload = { thresholds: readiness.thresholds };

  const recs = buildFocusRecommendations(readiness, payload);
  const items = buildFocusItems(readiness, payload);

  const sleepRec = recs.find((r) => r.metric === "sleep");
  assert.ok(sleepRec, "Debe generar una recomendación específica para métrica 'sleep'");
  assert.strictEqual(sleepRec.severity, "warning");
  assert.match(sleepRec.observation, /5\.8\s*h/i, "Observación debe contener las horas registradas (5.8 h)");
  assert.match(sleepRec.observation, /7\.0\s*h/i, "Observación debe contener la meta (≥7.0 h)");

  // Pauta fisiológica de higiene y mitigación de deuda
  assert.match(
    sleepRec.recommendation,
    /(deuda|adelanta.*acostarte|pantallas|luz azul)/i,
    "Recomendación debe pautar adelantar descanso nocturno y retirar pantallas/luz azul"
  );

  // fullText y buildFocusItems deben contener tanto la observación como la recomendación
  assert.match(sleepRec.fullText, /5\.8.*7\.0/);
  const itemStr = items.find((it) => it.includes("5.8"));
  assert.ok(itemStr, "buildFocusItems debe contener la recomendación de sueño completa");
  assert.match(itemStr, /(pantallas|luz azul|deuda|acostarte)/i);
});

test("REQ-001 / P01: Alerta de puntuación de sueño baja con recomendación fisiológica", async () => {
  const { buildFocusRecommendations } = await import("../../lib/dashboard.ts");

  const readiness = {
    readiness_date: "2026-10-17",
    zone: "AMARILLO",
    score_ok: 6,
    hrv: 52,
    bb_change: 35,
    sleep_h: 7.5,
    sleep_score: 64,
    stress: 28,
    recommendation: null,
    thresholds: { sleep_h: 7.0, sleep_score: 75 },
  };
  const payload = { thresholds: readiness.thresholds };

  const recs = buildFocusRecommendations(readiness, payload);
  const scoreRec = recs.find((r) => r.metric === "sleep_score");
  assert.ok(scoreRec, "Debe generar recomendación para sleep_score");
  assert.match(scoreRec.observation, /64.*75/);
  assert.match(scoreRec.recommendation, /(sueño|descanso|oscuridad|temperatura|higiene)/i);
});

test("REQ-002 / P02: Alerta de HRV deficitario con modulación autonómica, estimulación vagal y contención de intensidad", async () => {
  const { buildFocusRecommendations, buildFocusItems } = await import(
    "../../lib/dashboard.ts"
  );

  const readiness = {
    readiness_date: "2026-10-17",
    zone: "AMARILLO",
    score_ok: 5,
    hrv: 36,
    bb_change: 32,
    sleep_h: 7.8,
    sleep_score: 80,
    stress: 30,
    recommendation: null,
    thresholds: { hrv: 48, sleep_h: 7.0 },
  };
  const payload = { thresholds: readiness.thresholds };

  const recs = buildFocusRecommendations(readiness, payload);
  const items = buildFocusItems(readiness, payload);

  const hrvRec = recs.find((r) => r.metric === "hrv");
  assert.ok(hrvRec, "Debe generar recomendación para métrica 'hrv'");
  assert.strictEqual(hrvRec.severity, "warning");
  assert.match(hrvRec.observation, /36\s*ms.*48\s*ms/i);

  // Modulación autonómica, estimulación vagal y contención de intensidad
  assert.match(
    hrvRec.recommendation,
    /(vagal|parasimp[aá]t|Z1|respiraci[oó]n diafragm[aá]tica|recuperaci[oó]n activa)/i,
    "Debe recomendar estimulación vagal, recuperación activa Z1 o respiración diafragmática"
  );

  const hrvItem = items.find((it) => it.includes("36"));
  assert.ok(hrvItem);
  assert.match(hrvItem, /(vagal|parasimp[aá]t|Z1|respiraci[oó]n|recuperaci[oó]n)/i);
});

test("REQ-003 / P03: Alerta de Body Battery < 30 con recarga parasimpática y mitigación de estresores", async () => {
  const { buildFocusRecommendations, buildFocusItems } = await import(
    "../../lib/dashboard.ts"
  );

  const readiness = {
    readiness_date: "2026-10-17",
    zone: "AMARILLO",
    score_ok: 5,
    hrv: 50,
    bb_change: 15,
    sleep_h: 7.5,
    sleep_score: 78,
    stress: 25,
    recommendation: null,
    thresholds: { bb_change: 30 },
  };
  const payload = { thresholds: readiness.thresholds };

  const recs = buildFocusRecommendations(readiness, payload);
  const items = buildFocusItems(readiness, payload);

  const bbRec = recs.find((r) => r.metric === "bb_change");
  assert.ok(bbRec, "Debe generar recomendación para métrica 'bb_change'");
  assert.match(bbRec.observation, /\+?15.*\+?30/);

  // Recarga parasimpática, evitar cenas pesadas/alcohol, ambiente fresco
  assert.match(
    bbRec.recommendation,
    /(comidas pesadas|alcohol|parasimp[aá]t|estresores|descanso|regeneraci[oó]n)/i,
    "Debe recomendar mitigar estresores nocturnos como comidas pesadas/alcohol y optimizar descanso"
  );

  const bbItem = items.find((it) => it.includes("15"));
  assert.ok(bbItem);
  assert.match(bbItem, /(comidas pesadas|alcohol|parasimp[aá]t|estresores|descanso)/i);
});

test("REQ-004 / P04: Alerta de ACWR > 1.3 con reducción de carga según modelo de Gabbett", async () => {
  const { buildFocusRecommendations, buildFocusItems } = await import(
    "../../lib/dashboard.ts"
  );

  const readiness = {
    readiness_date: "2026-10-17",
    zone: "AMARILLO",
    score_ok: 5,
    hrv: 52,
    bb_change: 35,
    sleep_h: 7.6,
    sleep_score: 82,
    stress: 26,
    recommendation: null,
    thresholds: {},
  };
  const payload = {
    training_load: {
      acwr: 1.45,
      status_phrase: "PRODUCTIVE",
    },
  };

  const recs = buildFocusRecommendations(readiness, payload);
  const items = buildFocusItems(readiness, payload);

  const acwrRec = recs.find((r) => r.metric === "acwr");
  assert.ok(acwrRec, "Debe generar recomendación para ACWR > 1.3");
  assert.match(acwrRec.observation, /1\.45.*1\.3/);

  // Reducción de volumen semanal 20-30% y control de picos según Gabbett
  assert.match(
    acwrRec.recommendation,
    /(20%|30%|volumen|Gabbett|picos de intensidad|seguro)/i,
    "Debe recomendar modular o reducir volumen 20-30% según modelo Gabbett"
  );

  const acwrItem = items.find((it) => it.includes("1.45") || it.includes("ACWR"));
  assert.ok(acwrItem);
  assert.match(acwrItem, /(volumen|20%|30%|Gabbett|intensidad|1\.3)/i);
});

test("REQ-005 / P05: Sobreesfuerzo agudo (OVERREACHING) con descarga activa obligatoria", async () => {
  const { buildFocusRecommendations, buildFocusItems } = await import(
    "../../lib/dashboard.ts"
  );

  const readiness = {
    readiness_date: "2026-10-17",
    zone: "ROJO",
    score_ok: 3,
    hrv: 30,
    bb_change: 10,
    sleep_h: 5.2,
    sleep_score: 50,
    stress: 55,
    recommendation: null,
    thresholds: {},
  };
  const payload = {
    training_load: {
      status_phrase: "OVERREACHING",
      acwr: 1.6,
    },
  };

  const recs = buildFocusRecommendations(readiness, payload);
  const items = buildFocusItems(readiness, payload);

  const overRec = recs.find((r) => r.metric === "overreaching");
  assert.ok(overRec, "Debe generar recomendación para sobreesfuerzo agudo");
  assert.strictEqual(overRec.severity, "danger");

  // Prescripción de 24-48 h de descarga estricta o Z1 muy bajo impacto
  assert.match(
    overRec.recommendation,
    /(24.*48|descarga|regenerativo|Z1|bajo impacto|fatiga)/i,
    "Debe prescribir 24-48 h de descarga o rodajes regenerativos Z1"
  );

  const overItem = items.find((it) => it.toLowerCase().includes("sobreesfuerzo"));
  assert.ok(overItem);
  assert.match(overItem, /(descarga|regenerativo|24|48|Z1)/i);
});

test("REQ-006 / P06: Estado VERDE afirmativo con autorización de sesión planificada", async () => {
  const { buildFocusRecommendations, buildFocusItems } = await import(
    "../../lib/dashboard.ts"
  );

  const readiness = {
    readiness_date: "2026-10-17",
    zone: "VERDE",
    score_ok: 8,
    hrv: 58,
    bb_change: 42,
    sleep_h: 8.1,
    sleep_score: 88,
    stress: 20,
    recommendation: null,
    thresholds: { sleep_h: 7.0, sleep_score: 75, hrv: 48, bb_change: 30, stress_max: 35 },
  };
  const payload = {
    thresholds: readiness.thresholds,
    training_load: {
      acwr: 1.05,
      status_phrase: "PRODUCTIVE",
    },
  };

  const recs = buildFocusRecommendations(readiness, payload);
  const items = buildFocusItems(readiness, payload);

  assert.strictEqual(recs.length, 1);
  assert.strictEqual(recs[0].metric, "all_aligned");
  assert.strictEqual(recs[0].severity, "info");
  assert.match(
    recs[0].recommendation,
    /(sesi[oó]n|confirmar|ejecut|planificada|macrociclo|adelante)/i,
    "Recomendación en verde debe autorizar la sesión programada"
  );

  assert.strictEqual(items.length, 1);
  assert.match(items[0], /(sesi[oó]n|confirmar|ejecut|alineados)/i);
});

test("REQ-019 / P22: Clean Architecture - lib/dashboard.ts no importa React, Next.js ni dependencias de UI", () => {
  const dashboardPath = path.join(webRoot, "lib", "dashboard.ts");
  const content = fs.readFileSync(dashboardPath, "utf-8");

  assert.doesNotMatch(content, /from\s+['"]react['"]/, "dashboard.ts no debe importar React");
  assert.doesNotMatch(content, /from\s+['"]next(\/.*)?['"]/, "dashboard.ts no debe importar Next.js");
  assert.doesNotMatch(content, /from\s+['"]@\/components\/.*['"]/, "dashboard.ts no debe importar componentes UI");
});
