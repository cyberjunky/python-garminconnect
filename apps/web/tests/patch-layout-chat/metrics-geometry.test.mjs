import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");
const globalsCssPath = path.join(webRoot, "app", "globals.css");

/**
 * Evaluates the geometric behavior of .metrics-grid and .metric-cell for a given viewport.
 * Simulates CSS grid with repeat(auto-fit, minmax(colMinPx, 1fr)), cell padding, gap,
 * and text rendering requirements for "PUNTUACIÓN DE SUEÑO".
 */
export function calculateMetricGridGeometry(viewportWidth, options = {}) {
  const isMobile = viewportWidth <= 800;
  const colMinRem = options.colMinRem ?? 7.5; // Canonical 7.5rem = 120px
  const colMinPx = colMinRem * 16;
  const gapPx = 0.5 * 16; // gap: 0.5rem = 8px

  // Dashboard container geometry
  const mainPadding = isMobile ? 16 * 2 : 28 * 2;
  const availableMainWidth = isMobile
    ? viewportWidth - mainPadding
    : Math.min(viewportWidth - 240, 1120) - mainPadding;

  // Card padding 1.25rem = 20px each side (40px)
  const cardPadding = 20 * 2;
  const gridWidth = Math.max(0, availableMainWidth - cardPadding);

  // CSS Grid auto-fit column calculation
  // cols * colMinPx + (cols - 1) * gapPx <= gridWidth
  let cols = Math.floor((gridWidth + gapPx) / (colMinPx + gapPx));
  if (cols < 1) cols = 1;

  const actualColWidth = (gridWidth - (cols - 1) * gapPx) / cols;

  // Metric cell padding: 0.5rem top/bottom, 0.65rem left/right (0.65 * 16 = 10.4px * 2 = 20.8px)
  // border-left: 3px solid
  const cellPaddingHorizontal = 10.4 * 2;
  const cellBorderLeft = 3;
  const cellInnerWidth = actualColWidth - cellPaddingHorizontal - cellBorderLeft;

  // Metric label row layout: gap: 0.35rem (5.6px)
  const rowGap = 0.35 * 16;
  const badgeWidth = 12; // Status badge width
  const maxLabelWidth = cellInnerWidth - rowGap - badgeWidth;

  // "PUNTUACIÓN DE SUEÑO" at 0.7rem (11.2px) uppercase
  // Longest unbroken word: "PUNTUACIÓN" (10 chars, ~7.4px avg width = ~74px)
  // Second line: "DE SUEÑO" (8 chars, ~58px)
  const longestWordPx = 74;
  const unbrokenTotalPx = 135; // If it doesn't wrap

  const wrapsProperly = options.hasBreakWord !== false;
  const requiredLabelWidth = wrapsProperly ? longestWordPx : unbrokenTotalPx;

  // If label cannot break or cell lacks min-width: 0, row expands
  const labelOverflows = requiredLabelWidth > maxLabelWidth;
  const labelScrollWidth = Math.max(requiredLabelWidth, maxLabelWidth);
  const rowScrollWidth = labelScrollWidth + rowGap + badgeWidth;
  const cellScrollWidth = rowScrollWidth + cellPaddingHorizontal + cellBorderLeft;
  const cellClientWidth = actualColWidth;

  return {
    viewportWidth,
    gridWidth,
    cols,
    actualColWidth,
    cellInnerWidth,
    maxLabelWidth,
    requiredLabelWidth,
    labelOverflows,
    cellScrollWidth,
    cellClientWidth,
    isContained: cellScrollWidth <= cellClientWidth + 0.5,
  };
}

test("REQ-001 / P01: Ausencia de desborde horizontal (scrollWidth <= clientWidth) en .metrics-grid en viewports 375px a 1600px", () => {
  const css = fs.readFileSync(globalsCssPath, "utf-8");
  const has75rem = css.includes("minmax(7.5rem, 1fr)");
  const hasWordBreak = css.includes("overflow-wrap: break-word") || css.includes("word-break: break-word");

  const testViewports = [375, 390, 414, 768, 800, 1024, 1120, 1440, 1600];

  for (const vp of testViewports) {
    const geo = calculateMetricGridGeometry(vp, {
      colMinRem: has75rem ? 7.5 : 5.5,
      hasBreakWord: hasWordBreak,
    });

    assert.ok(
      geo.isContained,
      `Viewport ${vp}px desborda: cellScrollWidth (${geo.cellScrollWidth.toFixed(1)}px) > cellClientWidth (${geo.cellClientWidth.toFixed(1)}px)`
    );
  }
});

test("REQ-002 / P02: globals.css contiene las reglas canónicas de contención y no-desborde para métricas", () => {
  const css = fs.readFileSync(globalsCssPath, "utf-8");

  // .metrics-grid debe usar repeat(auto-fit, minmax(7.5rem, 1fr))
  assert.match(
    css,
    /\.metrics-grid\s*\{[^}]*grid-template-columns:\s*repeat\(\s*auto-fit\s*,\s*minmax\(\s*7\.5rem\s*,\s*1fr\s*\)\s*\)/,
    ".metrics-grid debe usar repeat(auto-fit, minmax(7.5rem, 1fr))"
  );

  // .metric-cell debe tener min-width: 0 y overflow: hidden
  const cellMatch = css.match(/\.metric-cell\s*\{([^}]*)\}/);
  assert.ok(cellMatch, ".metric-cell debe existir en globals.css");
  assert.match(cellMatch[1], /min-width:\s*0/, ".metric-cell debe tener min-width: 0");
  assert.match(cellMatch[1], /overflow:\s*hidden/, ".metric-cell debe tener overflow: hidden");

  // .metric-label-row debe tener align-items: flex-start, gap: 0.35rem, min-width: 0
  const rowMatch = css.match(/\.metric-label-row\s*\{([^}]*)\}/);
  assert.ok(rowMatch, ".metric-label-row debe existir en globals.css");
  assert.match(rowMatch[1], /align-items:\s*flex-start/, ".metric-label-row debe tener align-items: flex-start");
  assert.match(rowMatch[1], /gap:\s*0\.35rem/, ".metric-label-row debe tener gap: 0.35rem");
  assert.match(rowMatch[1], /min-width:\s*0/, ".metric-label-row debe tener min-width: 0");

  // .metric-label debe tener overflow-wrap: break-word y line-height: 1.25
  const labelMatch = css.match(/\.metric-label\s*\{([^}]*)\}/);
  assert.ok(labelMatch, ".metric-label debe existir en globals.css");
  assert.match(labelMatch[1], /overflow-wrap:\s*break-word/, ".metric-label debe tener overflow-wrap: break-word");
  assert.match(labelMatch[1], /line-height:\s*1\.25/, ".metric-label debe tener line-height: 1.25");

  // .metric-status-badge debe tener flex-shrink: 0
  const badgeMatch = css.match(/\.metric-status-badge\s*\{([^}]*)\}/);
  assert.ok(badgeMatch, ".metric-status-badge debe existir en globals.css");
  assert.match(badgeMatch[1], /flex-shrink:\s*0/, ".metric-status-badge debe tener flex-shrink: 0");
});
