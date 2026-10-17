import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { register } from "node:module";

register(new URL("../chat-server/ts-resolver.mjs", import.meta.url));

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

test("REQ-013 / P13: Enlace /tendencia en DashboardNav con icono, texto e indicador activo", () => {
  const navPath = path.join(webRoot, "components", "DashboardNav.tsx");
  assert.ok(fs.existsSync(navPath), "DashboardNav.tsx debe existir");
  const content = fs.readFileSync(navPath, "utf-8");

  // Debe definir el enlace /tendencia con la etiqueta Tendencia
  assert.match(
    content,
    /\{\s*href:\s*["']\/tendencia["'],\s*label:\s*["']Tendencia["']/,
    "DashboardNav debe contener { href: '/tendencia', label: 'Tendencia' }"
  );

  // Debe usar usePathname() para evaluar la ruta activa
  assert.match(content, /usePathname\(\)/, "DashboardNav debe usar usePathname()");
  assert.match(
    content,
    /path\s*===\s*href\s*\?\s*["'][^"']*active[^"']*["']/,
    "DashboardNav debe aplicar la clase 'active' cuando la ruta coincida"
  );
  assert.match(
    content,
    /aria-current=\{\s*path\s*===\s*href\s*\?\s*["']page["']\s*:\s*undefined\s*\}/,
    "DashboardNav debe aplicar aria-current='page' cuando la ruta coincida"
  );

  // Debe contener un icono descriptivo para el enlace de tendencia o navegación
  assert.match(
    content,
    /(<svg|dash-nav-icon|polyline|trending)/i,
    "DashboardNav debe incluir icono visual para la navegación"
  );
});

test("REQ-014 / P14: Contenedor centrado max-width 1120px y padding responsive en /tendencia (ADR-003)", () => {
  const pagePath = path.join(webRoot, "app", "(dashboard)", "tendencia", "page.tsx");
  assert.ok(fs.existsSync(pagePath), "app/(dashboard)/tendencia/page.tsx debe existir");
  const pageContent = fs.readFileSync(pagePath, "utf-8");

  // La página debe estar envuelta en un elemento <main>
  assert.match(
    pageContent,
    /<main[\s>]/,
    "/tendencia/page.tsx debe retornar un contenedor semántico <main>"
  );

  // Verificamos que globals.css define el contenedor centrado de 1120px para .app-main > main
  const cssPath = path.join(webRoot, "app", "globals.css");
  const cssContent = fs.readFileSync(cssPath, "utf-8");

  assert.match(
    cssContent,
    /\.app-main\s*>\s*main\s*\{[\s\S]*?max-width:\s*1120px;[\s\S]*?margin:\s*0\s+auto;[\s\S]*?padding:\s*1\.5rem\s+28px\s+3rem;/,
    "globals.css debe centrar .app-main > main con max-width 1120px y padding 28px en desktop"
  );

  assert.match(
    cssContent,
    /\.app-main\s*>\s*main\s*\{[\s\S]*?padding:\s*1\.25rem\s+16px\s+2\.5rem;/,
    "globals.css debe aplicar padding responsive de 16px en pantallas <= 800px"
  );
});

test("REQ-015 / P15: calculateMonthlyZoneDistribution calcula proporciones y conteos exactos de zonas", async () => {
  const { calculateMonthlyZoneDistribution } = await import("../../lib/tendencia.ts");

  // 1. Muestra de 30 días
  const sample30 = [
    ...Array(18).fill({ zone: "VERDE" }),
    ...Array(9).fill({ zone: "AMARILLO" }),
    ...Array(3).fill({ zone: "ROJO" }),
  ];

  const dist30 = calculateMonthlyZoneDistribution(sample30);
  assert.strictEqual(dist30.totalDays, 30);
  assert.strictEqual(dist30.counts.VERDE, 18);
  assert.strictEqual(dist30.counts.AMARILLO, 9);
  assert.strictEqual(dist30.counts.ROJO, 3);
  assert.strictEqual(dist30.percentages.VERDE, 60);
  assert.strictEqual(dist30.percentages.AMARILLO, 30);
  assert.strictEqual(dist30.percentages.ROJO, 10);

  // 2. Muestra parcial de 10 días
  const sample10 = [
    ...Array(5).fill({ zone: "verde" }), // Tolerante a minúsculas
    ...Array(3).fill({ zone: "AMARILLO" }),
    ...Array(2).fill({ zone: "ROJO" }),
  ];
  const dist10 = calculateMonthlyZoneDistribution(sample10);
  assert.strictEqual(dist10.totalDays, 10);
  assert.strictEqual(dist10.counts.VERDE, 5);
  assert.strictEqual(dist10.counts.AMARILLO, 3);
  assert.strictEqual(dist10.counts.ROJO, 2);
  assert.strictEqual(dist10.percentages.VERDE, 50);
  assert.strictEqual(dist10.percentages.AMARILLO, 30);
  assert.strictEqual(dist10.percentages.ROJO, 20);

  // 3. Tolerancia a arreglo vacío
  const emptyDist = calculateMonthlyZoneDistribution([]);
  assert.strictEqual(emptyDist.totalDays, 0);
  assert.strictEqual(emptyDist.counts.VERDE, 0);
  assert.strictEqual(emptyDist.counts.AMARILLO, 0);
  assert.strictEqual(emptyDist.counts.ROJO, 0);
  assert.strictEqual(emptyDist.percentages.VERDE, 0);
  assert.strictEqual(emptyDist.percentages.AMARILLO, 0);
  assert.strictEqual(emptyDist.percentages.ROJO, 0);
});

test("REQ-016 / P16: calculateMonthlySummary calcula promedios mensuales y omite valores nulos", async () => {
  const { calculateMonthlySummary } = await import("../../lib/tendencia.ts");

  const sampleRows = [
    {
      date: "2026-10-17",
      dateFormatted: "17 oct 2026",
      zone: "VERDE",
      scoreOk: 8,
      hrv: 50,
      sleepHours: 8.0,
      sleepScore: 85,
      stress: 25,
      bbChange: 40,
      acwr: 1.1,
      vo2max: 52,
    },
    {
      date: "2026-10-16",
      dateFormatted: "16 oct 2026",
      zone: "AMARILLO",
      scoreOk: 6,
      hrv: 46,
      sleepHours: 6.5,
      sleepScore: 70,
      stress: 32,
      bbChange: 20,
      acwr: 1.2,
      vo2max: 52,
    },
    {
      date: "2026-10-15",
      dateFormatted: "15 oct 2026",
      zone: "VERDE",
      scoreOk: 7,
      hrv: null, // Nulo intencional
      sleepHours: 7.5,
      sleepScore: 80,
      stress: 28,
      bbChange: 30,
      acwr: null, // Nulo intencional
      vo2max: null,
    },
    {
      date: "2026-10-14",
      dateFormatted: "14 oct 2026",
      zone: "ROJO",
      scoreOk: 3,
      hrv: 38,
      sleepHours: 5.5,
      sleepScore: 55,
      stress: 45,
      bbChange: 10,
      acwr: 1.45,
      vo2max: 51,
    },
  ];

  const thresholds = {
    hrv: 48,
    sleep_h: 7.0,
    sleep_score: 75,
    bb_change: 30,
    stress_max: 35,
  };

  const summary = calculateMonthlySummary(sampleRows, thresholds);

  assert.strictEqual(summary.totalEvaluatedDays, 4);
  // Días en verde: 2 de 4 = 50%
  assert.strictEqual(summary.zoneCompliancePct, 50);

  // HRV: (50 + 46 + 38) / 3 = 134 / 3 = 44.666... ~ 44.7 ms
  assert.ok(summary.hrv.averageValue !== null);
  assert.strictEqual(Math.round(summary.hrv.averageValue), 45);
  assert.strictEqual(summary.hrv.unit, "ms");

  // Sueño horas: (8.0 + 6.5 + 7.5 + 5.5) / 4 = 27.5 / 4 = 6.875 ~ 6.9 h
  assert.ok(summary.sleepHours.averageValue !== null);
  assert.strictEqual(Math.round(summary.sleepHours.averageValue * 10) / 10, 6.9);
  assert.strictEqual(summary.sleepHours.unit, "h");

  // Sleep score: (85 + 70 + 80 + 55) / 4 = 290 / 4 = 72.5
  assert.strictEqual(summary.sleepScore.averageValue, 72.5);

  // Body battery cambio: (40 + 20 + 30 + 10) / 4 = 100 / 4 = 25
  assert.strictEqual(summary.bodyBatteryChange.averageValue, 25);

  // Estrés: (25 + 32 + 28 + 45) / 4 = 130 / 4 = 32.5
  assert.strictEqual(summary.stress.averageValue, 32.5);

  // ACWR: (1.1 + 1.2 + 1.45) / 3 = 3.75 / 3 = 1.25
  assert.strictEqual(summary.acwr.averageValue, 1.25);

  // VO2max: (52 + 52 + 51) / 3 = 155 / 3 = 51.666... ~ 51.7
  assert.ok(summary.vo2max.averageValue !== null);
  assert.strictEqual(Math.round(summary.vo2max.averageValue * 10) / 10, 51.7);

  // StatusLabels informativos presentes
  assert.ok(summary.hrv.statusLabel.length > 0);
  assert.ok(summary.sleepHours.statusLabel.length > 0);
  assert.ok(summary.acwr.statusLabel.length > 0);

  // Tolerancia ante filas vacías
  const emptySummary = calculateMonthlySummary([]);
  assert.strictEqual(emptySummary.totalEvaluatedDays, 0);
  assert.strictEqual(emptySummary.zoneCompliancePct, 0);
  assert.strictEqual(emptySummary.hrv.averageValue, null);
  assert.strictEqual(emptySummary.sleepHours.averageValue, null);
  assert.strictEqual(emptySummary.acwr.averageValue, null);
  assert.strictEqual(emptySummary.hrv.statusLabel, "Sin datos");
});

test("REQ-017 / P17: Tabla de evolución diaria con fechas es-CO, badges de zona y tabular-nums", () => {
  const pagePath = path.join(webRoot, "app", "(dashboard)", "tendencia", "page.tsx");
  const content = fs.readFileSync(pagePath, "utf-8");

  // Debe contener elemento tabla o clase de tabla de historial
  assert.match(
    content,
    /<table|trend-table|history-table/i,
    "La vista /tendencia debe renderizar una tabla de evolución de 30 días"
  );

  // Celdas o tabla con tabular-nums
  assert.match(
    content,
    /tabular-nums/,
    "La tabla debe utilizar la clase 'tabular-nums' para alineación numérica monoespaciada"
  );

  // Formateo de fechas es-CO o uso de dateFormatted
  assert.match(
    content,
    /(dateFormatted|formatDateEsCO)/,
    "La vista debe desplegar fechas formateadas en español de Colombia (es-CO)"
  );

  // Badges de zona semánticos
  assert.match(
    content,
    /(badge-|badge\s+badge-)/,
    "La vista debe asignar badges semánticos a las zonas (VERDE/AMARILLO/ROJO)"
  );
});

test("REQ-018 / P18: Estado vacío resiliente y amigable ante ausencia de datos o error", () => {
  const pagePath = path.join(webRoot, "app", "(dashboard)", "tendencia", "page.tsx");
  const content = fs.readFileSync(pagePath, "utf-8");

  // Debe contener verificación de ausencia de datos o error con mensaje amigable
  assert.match(
    content,
    /(No se pudieron cargar|No hay registros|No hay datos disponibles|Sin registros)/i,
    "La vista /tendencia debe incluir mensaje amigable ante estado vacío o error"
  );
});
