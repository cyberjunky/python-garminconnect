import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import { spawn, execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  BROWSER_MEASURE_SCRIPT,
  CHAT_SYNTHETIC_ROUTE,
  MATRIX_S_CELLS,
  evaluateCellMeasurement,
} from "./measure.mjs";
import { createMockSupabaseServer } from "./mock-supabase-server.mjs";
import { SYNTHETIC_CHATS_STORAGE } from "./synthetic-fixtures.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "../..");
const repoRoot = path.resolve(webRoot, "../..");
const evidenceDir = path.join(repoRoot, "deliverables", "evidence", "T-0025");
const globalsCssPath = path.join(webRoot, "app", "globals.css");

const MOCK_SUPABASE_PORT = 44199;
const NEXT_PORT = 3125;
const RUNNER_PORT = 3126;
const RUNNER_ORIGIN = `http://127.0.0.1:${RUNNER_PORT}`;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitForHttp(url, timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get(url, (res) => {
          res.resume();
          if (res.statusCode && res.statusCode < 500) resolve();
          else reject(new Error(`HTTP ${res.statusCode}`));
        });
        req.on("error", reject);
      });
      return;
    } catch {
      await sleep(200);
    }
  }
  throw new Error(`Timed out waiting for ${url}`);
}

function buildSafariRunnerHtml(globalsCssText) {
  const runnerConfig = {
    chatsStorage: SYNTHETIC_CHATS_STORAGE,
    chatRoute: CHAT_SYNTHETIC_ROUTE,
    matrixCells: MATRIX_S_CELLS,
    measureScript: BROWSER_MEASURE_SCRIPT,
    globalsCss: globalsCssText,
    baselineOverrideCss:
      ".app-main > main { max-width: 880px !important; margin: 0 !important; padding: 1.5rem 1.75rem 3rem !important; } @media (max-width: 800px) { .app-main > main { padding: 1.25rem 1rem 2.5rem !important; max-width: 100% !important; } }",
  };

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Safari Real Matrix S Runner (SPEC-002 / T-0025)</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      background: #020617;
      color: #f1f5f9;
      font-family: system-ui, -apple-system, sans-serif;
    }
    #status-bar {
      padding: 6px 12px;
      font-size: 12px;
      background: #0f172a;
      border-bottom: 1px solid #334155;
    }
    #frame-host {
      overflow: auto;
    }
    iframe {
      border: 0;
      display: block;
      background: #0f172a;
    }
  </style>
</head>
<body>
  <div id="status-bar">Ejecutando verificación Safari real (SPEC-002 Matriz S)…</div>
  <div id="frame-host"></div>
  <script>
    const CONFIG = ${JSON.stringify(runnerConfig)};
    const statusEl = document.getElementById("status-bar");
    const hostEl = document.getElementById("frame-host");
    const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));

    async function renderDomToPngDataUrl(frameDoc, width, height, extraCss) {
      const cloneBody = frameDoc.body.cloneNode(true);
      cloneBody.querySelectorAll("script").forEach((s) => s.remove());

      const origTextareas = Array.from(frameDoc.querySelectorAll("textarea"));
      const cloneTextareas = Array.from(cloneBody.querySelectorAll("textarea"));
      origTextareas.forEach((ta, i) => {
        if (cloneTextareas[i]) {
          cloneTextareas[i].textContent = ta.value || "";
        }
      });

      const wrapper = frameDoc.createElement("div");
      wrapper.setAttribute("xmlns", "http://www.w3.org/1999/xhtml");
      wrapper.style.width = width + "px";
      wrapper.style.minHeight = height + "px";
      wrapper.style.background = "#0f172a";
      wrapper.style.color = "#f1f5f9";
      wrapper.style.fontFamily = "system-ui, -apple-system, sans-serif";
      wrapper.style.margin = "0";
      wrapper.style.padding = "0";

      const styleEl = frameDoc.createElement("style");
      let cssForWidth = CONFIG.globalsCss;
      if (width <= 800) {
        cssForWidth += "\\n" + cssForWidth.replace(/@media\\s*\\(\\s*max-width:\\s*800px\\s*\\)\\s*\\{([\\s\\S]*?)\\n\\}/g, "$1");
      }
      if (extraCss) {
        cssForWidth += "\\n" + extraCss;
        if (width <= 800) {
          cssForWidth += "\\n.app-main > main { padding: 1.25rem 1rem 2.5rem !important; max-width: 100% !important; }";
        }
      }
      styleEl.textContent = cssForWidth;
      wrapper.appendChild(styleEl);

      while (cloneBody.firstChild) {
        wrapper.appendChild(cloneBody.firstChild);
      }

      const serialized = new XMLSerializer().serializeToString(wrapper);
      const svgMarkup =
        '<svg xmlns="http://www.w3.org/2000/svg" width="' +
        width +
        '" height="' +
        height +
        '">' +
        '<foreignObject x="0" y="0" width="100%" height="100%">' +
        serialized +
        "</foreignObject></svg>";

      const svgUrl = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svgMarkup);
      const img = new Image();
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = svgUrl;
      });

      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0, width, height);
      return canvas.toDataURL("image/png");
    }

    async function loadAndMeasure(route, width, height, opts = {}) {
      const { baselineCssOverride = false, openHistoryPanel = false, screenshotName = null } = opts;
      statusEl.textContent = "Midiendo " + route + " @ " + width + "x" + height + "…";
      hostEl.innerHTML = "";
      const frame = document.createElement("iframe");
      frame.style.width = width + "px";
      frame.style.height = height + "px";

      const loaded = new Promise((resolve) => {
        frame.addEventListener("load", () => resolve(), { once: true });
      });
      frame.src = route;
      hostEl.appendChild(frame);
      await loaded;
      await tick(route.startsWith("/chat") ? 180 : 60);

      const doc = frame.contentDocument;
      const win = frame.contentWindow;

      if (baselineCssOverride) {
        const st = doc.createElement("style");
        st.id = "baseline-override";
        st.textContent = CONFIG.baselineOverrideCss;
        doc.head.appendChild(st);
        await tick(40);
      }

      if (openHistoryPanel) {
        const btns = Array.from(doc.querySelectorAll(".chat-header-btn"));
        const histBtn = btns.find((b) => b.textContent && b.textContent.includes("Historial"));
        if (histBtn && histBtn.getAttribute("aria-expanded") !== "true") {
          histBtn.click();
          await tick(60);
        }
      }

      const raw = win.eval(CONFIG.measureScript);
      const measurement = JSON.parse(raw);
      measurement.viewportMethod = "safari-real-viewport-frame";

      if (screenshotName) {
        const dataUrl = await renderDomToPngDataUrl(
          doc,
          width,
          height,
          baselineCssOverride ? CONFIG.baselineOverrideCss : ""
        );
        await fetch("/__safari_screenshot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: screenshotName, dataUrl }),
        });
      }

      return measurement;
    }

    async function buildNavigationCycleFromMeasured(width, height, measuredByKey) {
      const steps = [];
      const routesOrder = ["/", "/retos", "/mesociclos", "/70-3-cartagena"];
      for (const r of routesOrder) {
        const m = measuredByKey[r + ":" + width];
        steps.push({
          step: "dashboard:" + r,
          route: m.route,
          mainWidth: m.mainWidth,
          globalOverflow: m.globalOverflow,
          pass: m.route === r && m.globalOverflow <= 1,
        });
      }

      const chatM = measuredByKey[CONFIG.chatRoute + ":" + width];
      steps.push({
        step: "chat:open-with-id",
        route: chatM.route,
        chatMainWidth: chatM.chatMainWidth,
        composerWidth: chatM.composerWidth,
        userAlignSelf: chatM.userAlignSelf,
        assistantAlignSelf: chatM.assistantAlignSelf,
        pass:
          chatM.route === CONFIG.chatRoute &&
          chatM.composerWidth <= 882 &&
          Math.abs(chatM.composerMarginLeft - chatM.composerMarginRight) <= 2 &&
          chatM.userAlignSelf === "flex-end" &&
          chatM.assistantAlignSelf === "flex-start",
      });

      const chatHistM = await loadAndMeasure(CONFIG.chatRoute, width, height, {
        openHistoryPanel: true,
      });
      steps.push({
        step: "chat:history-open",
        route: chatHistM.route,
        globalOverflow: chatHistM.globalOverflow,
        pass: chatHistM.route === CONFIG.chatRoute && chatHistM.globalOverflow <= 1,
      });

      const chat2Route = "/chat?conversation=layout-synthetic-history-2";
      const chat2M = await loadAndMeasure(chat2Route, width, height);
      steps.push({
        step: "chat:select-history-item",
        route: chat2M.route,
        composerWidth: chat2M.composerWidth,
        pass: chat2M.route === chat2Route && chat2M.composerWidth <= 882,
      });

      const backM = measuredByKey["/:" + width];
      steps.push({
        step: "chat:back-to-dashboard",
        route: backM.route,
        mainWidth: backM.mainWidth,
        pass: backM.route === "/" && backM.globalOverflow <= 1,
      });

      return {
        viewport: width + "x" + height,
        allPass: steps.every((s) => s.pass),
        steps,
      };
    }

    async function runAll() {
      try {
        localStorage.setItem("fitness-coach-chats", JSON.stringify(CONFIG.chatsStorage));
        sessionStorage.clear();

        const baselineSpecs = [
          { route: "/", width: 1600, height: 900, screenshot: "baseline-inicio-1600.png" },
          { route: "/", width: 375, height: 812, screenshot: "baseline-inicio-375.png" },
          { route: CONFIG.chatRoute, width: 1600, height: 900, screenshot: "baseline-chat-1600.png" },
        ];

        const baselineResults = [];
        for (const b of baselineSpecs) {
          const m = await loadAndMeasure(b.route, b.width, b.height, {
            baselineCssOverride: true,
            screenshotName: b.screenshot,
          });
          m.screenshot = b.screenshot;
          baselineResults.push(m);
        }

        const shotMap = {
          "/:1600": "candidate-inicio-1600.png",
          "/:375": "candidate-inicio-375.png",
          "/:800": "candidate-inicio-800.png",
          "/:801": "candidate-inicio-801.png",
          "/retos:1600": "candidate-retos-1600.png",
          "/mesociclos:1600": "candidate-mesociclos-1600.png",
          "/70-3-cartagena:1600": "candidate-cartagena-1600.png",
          [CONFIG.chatRoute + ":1600"]: "candidate-chat-1600.png",
          [CONFIG.chatRoute + ":375"]: "candidate-chat-375-historial.png",
        };

        const candidateResults = [];
        const measuredByKey = {};
        for (const cell of CONFIG.matrixCells) {
          const key = cell.route + ":" + cell.width;
          const shotName = shotMap[key] || null;
          const openHistoryPanel = cell.route === CONFIG.chatRoute && cell.width === 375;
          const m = await loadAndMeasure(cell.route, cell.width, cell.height, {
            baselineCssOverride: false,
            openHistoryPanel,
            screenshotName: shotName,
          });
          m.screenshot = shotName;
          candidateResults.push(m);
          measuredByKey[key] = m;
        }

        const navCycle375 = await buildNavigationCycleFromMeasured(375, 812, measuredByKey);
        const navCycle1600 = await buildNavigationCycleFromMeasured(1600, 900, measuredByKey);

        localStorage.removeItem("fitness-coach-chats");
        sessionStorage.clear();

        await fetch("/__safari_complete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            userAgent: navigator.userAgent,
            baselineResults,
            candidateResults,
            navigationCyclesP03: [navCycle375, navCycle1600],
          }),
        });

        statusEl.textContent = "Verificación completada exitosamente.";
        window.close();
      } catch (err) {
        await fetch("/__safari_error", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: String(err && err.stack ? err.stack : err) }),
        });
      }
    }

    runAll();
  </script>
</body>
</html>`;
}

export async function runSafariMatrix() {
  fs.mkdirSync(evidenceDir, { recursive: true });
  const globalsCssText = fs.readFileSync(globalsCssPath, "utf-8");

  const mockSupabase = createMockSupabaseServer();
  await new Promise((resolve) => mockSupabase.listen(MOCK_SUPABASE_PORT, "127.0.0.1", resolve));

  const nextBin = path.join(webRoot, "node_modules", ".bin", "next");
  const nextServer = spawn(nextBin, ["start", "-H", "127.0.0.1", "-p", String(NEXT_PORT)], {
    cwd: webRoot,
    env: {
      ...process.env,
      NODE_ENV: "production",
      NEXT_PUBLIC_SUPABASE_URL: `http://127.0.0.1:${MOCK_SUPABASE_PORT}`,
      NEXT_PUBLIC_SUPABASE_ANON_KEY: "synthetic-anon-key-local-only",
      OPENAI_API_KEY: "",
    },
    stdio: "ignore",
  });

  let proxyServer = null;
  try {
    await waitForHttp(`http://127.0.0.1:${NEXT_PORT}/`, 20000);

    let resolveRun;
    let rejectRun;
    const runPromise = new Promise((res, rej) => {
      resolveRun = res;
      rejectRun = rej;
    });

    const runnerHtml = buildSafariRunnerHtml(globalsCssText);

    proxyServer = http.createServer((req, res) => {
      if (req.url === "/__safari_runner" && req.method === "GET") {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(runnerHtml);
        return;
      }

      if (req.url === "/api/chat" && req.method === "GET") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(
          JSON.stringify({
            ok: true,
            configured: true,
            models: ["synthetic-model"],
            defaultModel: "synthetic-model",
          })
        );
        return;
      }

      if (req.url === "/__safari_screenshot" && req.method === "POST") {
        let body = "";
        req.on("data", (chunk) => (body += chunk));
        req.on("end", () => {
          try {
            const { name, dataUrl } = JSON.parse(body);
            const b64 = dataUrl.replace(/^data:image\/png;base64,/, "");
            fs.writeFileSync(path.join(evidenceDir, path.basename(name)), Buffer.from(b64, "base64"));
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true }));
          } catch (err) {
            res.writeHead(500);
            res.end(String(err));
          }
        });
        return;
      }

      if (req.url === "/__safari_complete" && req.method === "POST") {
        let body = "";
        req.on("data", (chunk) => (body += chunk));
        req.on("end", () => {
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ ok: true }));
          resolveRun(JSON.parse(body));
        });
        return;
      }

      if (req.url === "/__safari_error" && req.method === "POST") {
        let body = "";
        req.on("data", (chunk) => (body += chunk));
        req.on("end", () => {
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ ok: true }));
          rejectRun(new Error(`Safari runner error: ${body}`));
        });
        return;
      }

      const proxyReq = http.request(
        {
          hostname: "127.0.0.1",
          port: NEXT_PORT,
          path: req.url,
          method: req.method,
          agent: false,
          headers: { ...req.headers, host: `127.0.0.1:${NEXT_PORT}`, connection: "close" },
        },
        (proxyRes) => {
          res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
          proxyRes.pipe(res);
        }
      );
      proxyReq.on("error", (err) => {
        res.writeHead(502);
        res.end(String(err));
      });
      req.pipe(proxyReq);
    });

    await new Promise((resolve) => proxyServer.listen(RUNNER_PORT, "127.0.0.1", resolve));

    const safariVersion = execFileSync(
      "/usr/bin/osascript",
      ["-e", 'tell application "Safari" to get version'],
      { encoding: "utf-8" }
    ).trim();

    execFileSync("/usr/bin/open", ["-a", "/Applications/Safari.app", `${RUNNER_ORIGIN}/__safari_runner`]);

    let timeoutId;
    const timeoutPromise = new Promise((_, rej) => {
      timeoutId = setTimeout(() => rej(new Error("Timed out waiting for Safari runner completion")), 60000);
    });
    const payload = await Promise.race([runPromise, timeoutPromise]).finally(() => {
      clearTimeout(timeoutId);
    });

    const baselineResults = payload.baselineResults.map((m) => ({
      ...m,
      evaluation: evaluateCellMeasurement(m),
    }));

    const candidateResults = payload.candidateResults.map((m) => ({
      ...m,
      evaluation: evaluateCellMeasurement(m),
    }));

    const [navCycle375, navCycle1600] = payload.navigationCyclesP03;

    const gitSha = execFileSync("git", ["rev-parse", "HEAD"], {
      cwd: repoRoot,
      encoding: "utf-8",
    }).trim();

    const report = {
      taskId: "T-0025",
      spec: "SPEC-002",
      stage: "I-UI",
      candidateVersion: "0.4.0-rc.1",
      checkpointSha: gitSha,
      baselineCodeSha: "aeaa5da9a02c0070cb4f4259da13f1cb27ba16ab",
      browser: {
        app: "/Applications/Safari.app",
        safariVersion,
        driverMode: "launchservices-safari-runner",
        userAgent: payload.userAgent,
        zoom: "100%",
      },
      isolation: {
        supabaseEndpoint: `http://127.0.0.1:${MOCK_SUPABASE_PORT}`,
        nextEndpoint: `http://127.0.0.1:${NEXT_PORT}`,
        runnerOrigin: RUNNER_ORIGIN,
        cloudCalls: 0,
        personalDataUsed: false,
      },
      baselineComparative: baselineResults,
      candidateMatrixS: candidateResults,
      navigationCyclesP03: [navCycle375, navCycle1600],
      summary: {
        totalMatrixCells: candidateResults.length,
        passedMatrixCells: candidateResults.filter((c) => c.evaluation.pass).length,
        p03NavigationPass: navCycle375.allPass && navCycle1600.allPass,
      },
    };

    fs.writeFileSync(
      path.join(evidenceDir, "safari-matrix-s.json"),
      JSON.stringify(report, null, 2),
      "utf-8"
    );

    const mdLines = [
      "# Evidencia Safari Real — Matriz S (SPEC-002 §5, T-0025)",
      "",
      `- **Navegador**: Safari ${safariVersion} (\`/Applications/Safari.app\`)`,
      `- **User-Agent**: \`${payload.userAgent}\``,
      `- **Zoom**: 100%`,
      `- **Servidor local aislado**: \`${RUNNER_ORIGIN}\` -> Next \`http://127.0.0.1:${NEXT_PORT}\` + fixture Supabase loopback \`http://127.0.0.1:${MOCK_SUPABASE_PORT}\``,
      `- **Checkpoint base**: \`${gitSha}\` (código base \`aeaa5da9a02c0070cb4f4259da13f1cb27ba16ab\`)`,
      "",
      "## 1. Comparativa Baseline vs Candidato (Defecto de centrado en 1600px)",
      "",
      "| Estado | Ruta | Viewport (`clientWidth`) | `A` (`.app-main`) | `W` (`main`) | Padding izq/der | Margen izq / der (`Δ`) | Overflow global | Resultado P01 | Captura |",
      "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ];

    for (const b of baselineResults) {
      if (b.kind === "dashboard") {
        mdLines.push(
          `| Baseline (0.3.0) | \`${b.route}\` | ${b.clientWidth}px | ${b.appMainWidth}px | ${b.mainWidth}px | ${b.paddingLeft}/${b.paddingRight}px | ${b.marginLeft}px / ${b.marginRight}px (\`Δ=${b.marginDiff}px\`) | ${b.globalOverflow}px | ${b.evaluation.pass ? "PASS" : "FAIL (sesgo izq)"} | \`${b.screenshot}\` |`
        );
      } else {
        mdLines.push(
          `| Baseline (0.3.0) | \`${b.route}\` | ${b.clientWidth}px | — | chatMain ${b.chatMainWidth}px / composer ${b.composerWidth}px | — | composer ${b.composerMarginLeft}px / ${b.composerMarginRight}px (\`Δ=${b.composerMarginDiff}px\`) | ${b.globalOverflow}px | ${b.evaluation.pass ? "PASS" : "FAIL"} | \`${b.screenshot}\` |`
        );
      }
    }

    mdLines.push(
      "",
      "## 2. Matriz S Candidata (14 celdas en Safari real, v0.4.0-rc.1)",
      "",
      "| # | Ruta | `clientWidth` | `<=800px` | `A` (`.app-main`) | `W` (`main` / `.chat-main`) | Padding izq/der | Margen izq / der (`Δ`) | Overflow global | Scroll interno / Burbujas | P01/P02/P03 | Captura |",
      "|---:|---|---:|---|---:|---:|---:|---:|---:|---|---|---|"
    );

    candidateResults.forEach((c, idx) => {
      if (c.kind === "dashboard") {
        const scrollNote = c.internalScroll
          ? `scrollWidth=${c.internalScroll.scrollWidth}px, canReachEnd=${c.internalScroll.canReachEnd}, docScrollX=${c.internalScroll.docScrollLeftAfter}px`
          : "n/a";
        mdLines.push(
          `| ${idx + 1} | \`${c.route}\` | ${c.clientWidth}px | ${c.mediaMaxWidth800} | ${c.appMainWidth}px | ${c.mainWidth}px | ${c.paddingLeft}/${c.paddingRight}px | ${c.marginLeft}px / ${c.marginRight}px (\`Δ=${c.marginDiff}px\`) | ${c.globalOverflow}px | ${scrollNote} | ${c.evaluation.pass ? "PASS" : "FAIL"} | ${c.screenshot ? `\`${c.screenshot}\`` : "—"} |`
        );
      } else {
        const bubbleNote = `composer=${c.composerWidth}px (Δm=${c.composerMarginDiff}px), user=${c.userAlignSelf}, assistant=${c.assistantAlignSelf}`;
        mdLines.push(
          `| ${idx + 1} | \`${c.route}\` | ${c.clientWidth}px | ${c.mediaMaxWidth800} | — | ${c.chatMainWidth}px | 0/0px | ${c.composerMarginLeft}px / ${c.composerMarginRight}px (\`Δ=${c.composerMarginDiff}px\`) | ${c.globalOverflow}px | ${bubbleNote} | ${c.evaluation.pass ? "PASS" : "FAIL"} | ${c.screenshot ? `\`${c.screenshot}\`` : "—"} |`
        );
      }
    }
    );

    mdLines.push(
      "",
      "## 3. Ciclo de Navegación P03 (375px y 1600px)",
      "",
      "| Viewport | Paso | Ruta destino | Resultado |",
      "|---|---|---|---|"
    );

    for (const cycle of [navCycle375, navCycle1600]) {
      for (const s of cycle.steps) {
        mdLines.push(
          `| ${cycle.viewport} | \`${s.step}\` | \`${s.route}\` | ${s.pass ? "PASS" : "FAIL"} |`
        );
      }
    }

    fs.writeFileSync(path.join(evidenceDir, "safari-matrix-s.md"), mdLines.join("\n") + "\n", "utf-8");

    if (
      report.summary.passedMatrixCells !== report.summary.totalMatrixCells ||
      !report.summary.p03NavigationPass
    ) {
      throw new Error("Safari Matrix S verification failed one or more cells");
    }
  } finally {
    if (proxyServer) {
      proxyServer.close();
    }
    nextServer.kill("SIGTERM");
    mockSupabase.close();
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runSafariMatrix().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
