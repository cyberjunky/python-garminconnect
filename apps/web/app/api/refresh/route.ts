import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const WORKFLOW = "coaching-daily-collect.yml";

function githubConfig() {
  const token = process.env.ACTIONS_DISPATCH_TOKEN;
  const repo = process.env.ACTIONS_DISPATCH_REPO || "dalarconics/python-garminconnect";
  const ref = process.env.ACTIONS_DISPATCH_REF || "master";
  return { token, repo, ref };
}

function missingToken() {
  return NextResponse.json(
    { ok: false, error: "Falta ACTIONS_DISPATCH_TOKEN en el proyecto de Vercel" },
    { status: 503 }
  );
}

function githubHeaders(token: string) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "Content-Type": "application/json",
  };
}

type WorkflowRun = {
  id: number;
  status: string;
  conclusion: string | null;
  created_at: string;
  html_url: string;
};

/** Dispatches the Garmin collect on GitHub Actions. Garmin tokens stay in GitHub, not on Vercel. */
export async function POST() {
  const { token, repo, ref } = githubConfig();
  if (!token) return missingToken();

  try {
    const res = await fetch(
      `https://api.github.com/repos/${repo}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: "POST",
        headers: githubHeaders(token),
        body: JSON.stringify({ ref }),
        cache: "no-store",
      }
    );

    if (!res.ok) {
      const detail = (await res.text()).slice(0, 300);
      return NextResponse.json(
        { ok: false, error: detail || `GitHub respondió ${res.status}` },
        { status: 502 }
      );
    }

    return NextResponse.json({
      ok: true,
      pending: true,
      message: "Consultando Garmin en GitHub. Tarda 1–2 min.",
    });
  } catch (err) {
    const error = err instanceof Error ? err.message : "No se pudo actualizar";
    return NextResponse.json({ ok: false, error }, { status: 502 });
  }
}

/** Polls the workflow run started at or after `since`. */
export async function GET(request: Request) {
  const { token, repo } = githubConfig();
  if (!token) return missingToken();

  const sinceRaw = new URL(request.url).searchParams.get("since");
  const sinceMs = sinceRaw ? Date.parse(sinceRaw) - 60_000 : Date.now() - 15 * 60_000;

  try {
    const res = await fetch(
      `https://api.github.com/repos/${repo}/actions/workflows/${WORKFLOW}/runs?event=workflow_dispatch&per_page=5`,
      { headers: githubHeaders(token), cache: "no-store" }
    );
    if (!res.ok) {
      const detail = (await res.text()).slice(0, 300);
      return NextResponse.json(
        { ok: false, error: detail || `GitHub respondió ${res.status}` },
        { status: 502 }
      );
    }
    const body = (await res.json()) as { workflow_runs?: WorkflowRun[] };
    const runs = body.workflow_runs || [];
    const run = runs.find((item) => Date.parse(item.created_at) >= sinceMs) ?? null;
    if (!run) {
      return NextResponse.json({ ok: true, pending: true, status: "queued" });
    }
    const done = run.status === "completed";
    return NextResponse.json({
      ok: true,
      pending: !done,
      status: run.status,
      conclusion: run.conclusion,
      htmlUrl: run.html_url,
    });
  } catch (err) {
    const error = err instanceof Error ? err.message : "No se pudo leer el estado";
    return NextResponse.json({ ok: false, error }, { status: 502 });
  }
}
