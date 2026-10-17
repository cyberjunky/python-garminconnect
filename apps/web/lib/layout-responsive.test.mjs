import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  MATRIX_S_CELLS,
  computeExpectedDashboardGeometry,
  evaluateCellMeasurement,
} from "../tests/layout-responsive/measure.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..");
const globalsCssPath = path.join(webRoot, "app", "globals.css");

function parsePxOrRem(val) {
  const v = val.trim();
  if (v.endsWith("px")) return parseFloat(v);
  if (v.endsWith("rem")) return parseFloat(v) * 16;
  return parseFloat(v) || 0;
}

function parsePaddingHorizontal(paddingValue) {
  const parts = paddingValue.trim().split(/\s+/);
  if (parts.length === 1) return parsePxOrRem(parts[0]);
  if (parts.length === 2 || parts.length === 3) return parsePxOrRem(parts[1]);
  if (parts.length >= 4) return parsePxOrRem(parts[1]);
  return 0;
}

function extractCssRules(cssText) {
  const mediaMatch = cssText.match(/@media\s*\(\s*max-width:\s*800px\s*\)\s*\{([\s\S]*?)\n\}/);
  const mobileBlock = mediaMatch ? mediaMatch[1] : "";
  const desktopText = mediaMatch ? cssText.replace(mediaMatch[0], "") : cssText;

  const findBlock = (source, selectorRegex) => {
    const m = source.match(selectorRegex);
    return m ? m[1] : null;
  };

  return {
    desktopDashboardMain: findBlock(desktopText, /\.app-main\s*>\s*main\s*\{([^}]*)\}/),
    mobileDashboardMain: findBlock(mobileBlock, /\.app-main\s*>\s*main\s*\{([^}]*)\}/),
    chatMain: findBlock(desktopText, /\.chat-main\s*\{([^}]*)\}/),
    chatComposer: findBlock(desktopText, /\.chat-composer\s*\{([^}]*)\}/),
    chatRowUser: findBlock(desktopText, /\.chat-row-user\s*\{([^}]*)\}/),
    chatRowAssistant: findBlock(desktopText, /\.chat-row-assistant\s*\{([^}]*)\}/),
  };
}

function parseProps(blockText) {
  const props = {};
  if (!blockText) return props;
  for (const decl of blockText.split(";")) {
    const idx = decl.indexOf(":");
    if (idx === -1) continue;
    const key = decl.slice(0, idx).trim();
    const val = decl.slice(idx + 1).trim();
    if (key) props[key] = val;
  }
  return props;
}

test("REQ-001 / P01: globals.css centra .app-main > main con max-width 1120px y paddings 28px (>800px) / 16px (<=800px)", () => {
  const css = fs.readFileSync(globalsCssPath, "utf-8");
  const rules = extractCssRules(css);

  assert.ok(
    rules.desktopDashboardMain,
    "globals.css debe definir selector acotado '.app-main > main' para el dashboard en escritorio"
  );
  assert.ok(
    rules.mobileDashboardMain,
    "globals.css debe definir selector acotado '.app-main > main' dentro de @media (max-width: 800px)"
  );

  const desktopProps = parseProps(rules.desktopDashboardMain);
  assert.strictEqual(desktopProps["width"], "100%", "El main del dashboard debe ocupar width: 100% hasta su tope");
  assert.strictEqual(desktopProps["max-width"], "1120px", "El main del dashboard debe tener max-width: 1120px");
  assert.match(
    desktopProps["margin"] || "",
    /^0(?:px)?\s+auto$/,
    "El main del dashboard debe centrarse horizontalmente con margin: 0 auto"
  );
  assert.strictEqual(
    parsePaddingHorizontal(desktopProps["padding"] || ""),
    28,
    "El padding horizontal en viewport > 800px debe ser 28px"
  );

  const mobileProps = parseProps(rules.mobileDashboardMain);
  assert.strictEqual(
    mobileProps["max-width"],
    "100%",
    "En <= 800px el main del dashboard debe tener max-width: 100%"
  );
  assert.strictEqual(
    parsePaddingHorizontal(mobileProps["padding"] || ""),
    16,
    "El padding horizontal en viewport <= 800px debe ser 16px"
  );
});

test("REQ-001 / P01: evaluador geometrico pasa las 14 celdas de la matriz S con la regla nueva y detecta el sesgo de 880px/margin:0", () => {
  const css = fs.readFileSync(globalsCssPath, "utf-8");
  const rules = extractCssRules(css);
  assert.ok(rules.desktopDashboardMain && rules.mobileDashboardMain, "Faltan reglas .app-main > main");

  const desktopProps = parseProps(rules.desktopDashboardMain);
  const mobileProps = parseProps(rules.mobileDashboardMain);
  const desktopMaxW = parsePxOrRem(desktopProps["max-width"] || "0");
  const desktopPad = parsePaddingHorizontal(desktopProps["padding"] || "0");
  const mobilePad = parsePaddingHorizontal(mobileProps["padding"] || "0");
  const isCentered = /^0(?:px)?\s+auto$/.test(desktopProps["margin"] || "");

  for (const cellSpec of MATRIX_S_CELLS) {
    if (cellSpec.kind === "dashboard") {
      const isMobile = cellSpec.width <= 800;
      const appMainWidth = isMobile ? cellSpec.width : cellSpec.width - 240;
      const mainWidth = isMobile ? appMainWidth : Math.min(appMainWidth, desktopMaxW);
      const pad = isMobile ? mobilePad : desktopPad;
      const marginLeft = isCentered ? (appMainWidth - mainWidth) / 2 : 0;
      const marginRight = appMainWidth - mainWidth - marginLeft;

      const verdict = evaluateCellMeasurement({
        kind: "dashboard",
        route: cellSpec.route,
        clientWidth: cellSpec.width,
        appMainWidth,
        mainWidth,
        paddingLeft: pad,
        paddingRight: pad,
        marginLeft,
        marginRight,
        globalOverflow: 0,
        controlsOutOfBounds: [],
      });
      assert.strictEqual(
        verdict.pass,
        true,
        `Celda ${cellSpec.route} @ ${cellSpec.width}px fallo: ${verdict.errors.join("; ")}`
      );
    } else {
      const wrapInner = cellSpec.width - 40;
      const composerWidth = Math.min(880, wrapInner);
      const composerMargin = (wrapInner - composerWidth) / 2;
      const verdict = evaluateCellMeasurement({
        kind: "chat",
        route: cellSpec.route,
        clientWidth: cellSpec.width,
        chatMainWidth: cellSpec.width,
        composerWidth,
        composerMarginLeft: composerMargin,
        composerMarginRight: composerMargin,
        userAlignSelf: "flex-end",
        assistantAlignSelf: "flex-start",
        globalOverflow: 0,
        controlsOutOfBounds: [],
      });
      assert.strictEqual(
        verdict.pass,
        true,
        `Celda chat ${cellSpec.route} @ ${cellSpec.width}px fallo: ${verdict.errors.join("; ")}`
      );
    }
  }

  // Verificar que el defecto original (max-width: 880px, margin: 0) en 1600px falla P01
  const legacyVerdict = evaluateCellMeasurement({
    kind: "dashboard",
    route: "/",
    clientWidth: 1600,
    appMainWidth: 1360,
    mainWidth: 880,
    paddingLeft: 28,
    paddingRight: 28,
    marginLeft: 0,
    marginRight: 480,
    globalOverflow: 0,
    controlsOutOfBounds: [],
  });
  assert.strictEqual(legacyVerdict.pass, false, "El evaluador debe rechazar la geometria sesgada de 880px / margin 0");
});

test("REQ-002 / P02 & REQ-003 / P03: preserva scroll interno de graficas y layout independiente del chat", () => {
  const css = fs.readFileSync(globalsCssPath, "utf-8");
  const rules = extractCssRules(css);

  const chatMainProps = parseProps(rules.chatMain);
  assert.strictEqual(chatMainProps["max-width"], "none");
  assert.strictEqual(chatMainProps["width"], "100%");
  assert.strictEqual(chatMainProps["margin"], "0");
  assert.strictEqual(chatMainProps["padding"], "0");

  const composerProps = parseProps(rules.chatComposer);
  assert.strictEqual(composerProps["max-width"], "880px");
  assert.strictEqual(composerProps["margin"], "0 auto");

  const userProps = parseProps(rules.chatRowUser);
  const assistantProps = parseProps(rules.chatRowAssistant);
  assert.strictEqual(userProps["align-self"], "flex-end");
  assert.strictEqual(assistantProps["align-self"], "flex-start");

  // Scroll interno de grafica y tabla intactos
  assert.match(css, /\.prep-chart-wrap\s*\{[\s\S]*?overflow-x:\s*auto/);
  assert.match(css, /\.prep-chart\s*\{[\s\S]*?min-width:\s*680px/);
  assert.match(css, /\.projection-table-wrap\s*\{[\s\S]*?overflow-x:\s*auto/);
});

test("REQ-022 / P22: verificacion de direccion de dependencias (Clean Architecture) en archivos tocados y dominio", () => {
  const extractSpecifiers = (filePath) => {
    const content = fs.readFileSync(filePath, "utf-8");
    const specifiers = [];
    const importRegex = /(?:import|export)\s+(?:[\s\S]*?\s+from\s+)?["']([^"']+)["']|import\(\s*["']([^"']+)["']\s*\)/g;
    let match;
    while ((match = importRegex.exec(content)) !== null) {
      specifiers.push(match[1] || match[2]);
    }
    return specifiers;
  };

  const resolveImport = (fromFile, spec) => {
    if (spec.startsWith("@/")) {
      return path.join(webRoot, spec.slice(2));
    }
    if (spec.startsWith(".")) {
      return path.resolve(path.dirname(fromFile), spec);
    }
    return spec;
  };

  // 1. Modulos de calculo puro en apps/web/lib no importan Next, React, Supabase, OpenAI ni UI
  const pureDomainFiles = [
    "lib/preparation.ts",
    "lib/lastActivity.ts",
    "lib/lastUpdated.ts",
    "lib/cartagena703.ts",
  ].map((rel) => path.join(webRoot, rel));

  for (const file of pureDomainFiles) {
    const specs = extractSpecifiers(file);
    for (const spec of specs) {
      const resolved = resolveImport(file, spec);
      assert.doesNotMatch(
        spec,
        /^(next|react|@supabase|openai)/,
        `Dominio puro ${path.relative(webRoot, file)} no puede importar framework/red (${spec})`
      );
      assert.ok(
        !resolved.includes(path.join(webRoot, "components")) &&
          !resolved.includes(path.join(webRoot, "app")) &&
          !resolved.endsWith("supabase") &&
          !resolved.endsWith("supabase.ts") &&
          !resolved.endsWith("openaiModels") &&
          !resolved.endsWith("openaiModels.ts"),
        `Dominio puro ${path.relative(webRoot, file)} no puede depender de UI o clientes de infraestructura (${spec})`
      );
    }
  }

  // 2. Layout del dashboard permanece en capa de presentacion sin clientes de infraestructura
  const dashboardLayoutFile = path.join(webRoot, "app", "(dashboard)", "layout.tsx");
  const layoutSpecs = extractSpecifiers(dashboardLayoutFile);
  for (const spec of layoutSpecs) {
    assert.doesNotMatch(
      spec,
      /(@supabase|openai|supabase|tests\/layout-responsive)/,
      `app/(dashboard)/layout.tsx no debe importar clientes de infraestructura ni soporte de tests (${spec})`
    );
  }

  // 3. Ningun archivo de runtime de la app importa desde tests/layout-responsive
  const walkTsFiles = (dir) => {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    let results = [];
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        results = results.concat(walkTsFiles(full));
      } else if (/\.(ts|tsx)$/.test(entry.name)) {
        results.push(full);
      }
    }
    return results;
  };

  const runtimeFiles = [
    ...walkTsFiles(path.join(webRoot, "app")),
    ...walkTsFiles(path.join(webRoot, "components")),
    ...walkTsFiles(path.join(webRoot, "lib")),
  ];

  for (const file of runtimeFiles) {
    const specs = extractSpecifiers(file);
    for (const spec of specs) {
      const resolved = resolveImport(file, spec);
      assert.ok(
        !resolved.includes(path.join(webRoot, "tests", "layout-responsive")),
        `Archivo de runtime ${path.relative(webRoot, file)} no debe importar soporte de pruebas (${spec})`
      );
    }
  }
});

test("REQ-001..003 / P01..P03: evidencia de las 14 celdas de la matriz S y navegacion P03 en Safari real", async () => {
  const repoRoot = path.resolve(webRoot, "../..");
  const evidenceDir = path.join(repoRoot, "deliverables", "evidence", "T-0025");
  const jsonPath = path.join(evidenceDir, "safari-matrix-s.json");

  if (!fs.existsSync(jsonPath) || process.env.FORCE_SAFARI_MATRIX === "1") {
    const { runSafariMatrix } = await import("../tests/layout-responsive/run-safari-matrix.mjs");
    await runSafariMatrix();
  }

  assert.ok(fs.existsSync(jsonPath), "Debe existir deliverables/evidence/T-0025/safari-matrix-s.json");
  const report = JSON.parse(fs.readFileSync(jsonPath, "utf-8"));

  assert.strictEqual(report.isolation.cloudCalls, 0, "Cero llamadas a servicios reales");
  assert.strictEqual(report.isolation.personalDataUsed, false, "Sin datos personales en pruebas");
  assert.strictEqual(report.candidateMatrixS.length, 14, "La matriz S debe tener exactamente 14 celdas");

  // El baseline en Inicio 1600px debe evidenciar el defecto previo de centrado
  const baseInicio1600 = report.baselineComparative.find((c) => c.route === "/" && c.clientWidth === 1600);
  assert.ok(baseInicio1600, "Debe existir medicion baseline de Inicio a 1600px");
  assert.strictEqual(
    baseInicio1600.evaluation.pass,
    false,
    "El baseline de Inicio a 1600px debe reflejar el fallo de centrado previo (880px / marginLeft 0)"
  );

  // Todas las 14 celdas candidatas deben cumplir P01, P02 y P03
  for (const cell of report.candidateMatrixS) {
    const check = evaluateCellMeasurement(cell);
    assert.strictEqual(
      check.pass,
      true,
      `Celda Safari real ${cell.route} @ ${cell.clientWidth}px fallo: ${check.errors.join("; ")}`
    );
  }

  assert.strictEqual(report.summary.p03NavigationPass, true, "El ciclo de navegacion P03 en 375px y 1600px debe pasar");

  const requiredShots = [
    "baseline-inicio-1600.png",
    "baseline-inicio-375.png",
    "baseline-chat-1600.png",
    "candidate-inicio-1600.png",
    "candidate-inicio-375.png",
    "candidate-inicio-800.png",
    "candidate-inicio-801.png",
    "candidate-retos-1600.png",
    "candidate-mesociclos-1600.png",
    "candidate-cartagena-1600.png",
    "candidate-chat-1600.png",
    "candidate-chat-375-historial.png",
  ];

  for (const shot of requiredShots) {
    const shotPath = path.join(evidenceDir, shot);
    assert.ok(fs.existsSync(shotPath), `Falta captura requerida: ${shot}`);
    const stat = fs.statSync(shotPath);
    assert.ok(stat.size > 1000, `Captura ${shot} vacia o invalida (${stat.size} bytes)`);
  }
});

