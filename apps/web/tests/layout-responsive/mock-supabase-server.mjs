import http from "node:http";
import {
  SYNTHETIC_READINESS_HISTORY,
  SYNTHETIC_READINESS_LATEST,
  SYNTHETIC_SNAPSHOT,
  SYNTHETIC_TRAINING_LOAD,
  SYNTHETIC_WEEKLY_SPORT_LOAD,
} from "./synthetic-fixtures.mjs";

export function createMockSupabaseServer() {
  return http.createServer((req, res) => {
    const url = new URL(req.url || "/", "http://127.0.0.1");
    const accept = String(req.headers.accept || "");
    const wantsSingleObject = accept.includes("application/vnd.pgrst.object+json");

    if (req.method !== "GET" && req.method !== "HEAD") {
      res.writeHead(405, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ message: "Mutations disabled in synthetic fixture server" }));
      return;
    }

    const sendPayload = (rows, singleFallback) => {
      const body = wantsSingleObject ? singleFallback : rows;
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(body));
    };

    if (url.pathname === "/rest/v1/readiness_daily") {
      const limit = Number(url.searchParams.get("limit") || "0");
      if (wantsSingleObject || limit === 1) {
        sendPayload([SYNTHETIC_READINESS_LATEST], SYNTHETIC_READINESS_LATEST);
      } else {
        sendPayload(SYNTHETIC_READINESS_HISTORY, SYNTHETIC_READINESS_LATEST);
      }
      return;
    }

    if (url.pathname === "/rest/v1/daily_snapshots") {
      sendPayload([SYNTHETIC_SNAPSHOT], SYNTHETIC_SNAPSHOT);
      return;
    }

    if (url.pathname === "/rest/v1/training_load") {
      sendPayload(SYNTHETIC_TRAINING_LOAD, SYNTHETIC_TRAINING_LOAD[0]);
      return;
    }

    if (url.pathname === "/rest/v1/weekly_sport_load") {
      sendPayload(SYNTHETIC_WEEKLY_SPORT_LOAD, SYNTHETIC_WEEKLY_SPORT_LOAD[0]);
      return;
    }

    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ message: `Unknown synthetic endpoint: ${url.pathname}` }));
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const port = Number(process.env.MOCK_SUPABASE_PORT || 44199);
  const server = createMockSupabaseServer();
  server.listen(port, "127.0.0.1", () => {
    console.log(`Synthetic Supabase fixture server listening on http://127.0.0.1:${port}`);
  });
}
