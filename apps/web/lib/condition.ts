import { preparationIndex } from "@/lib/preparation";
import { MVP_USER_ID, supabase } from "@/lib/supabase";

export type ConditionSnapshot = {
  readinessDate: string | null;
  updatedAt: string | null;
  stale: boolean;
  zone: string | null;
  scoreOk: number | null;
  sleepH: number | null;
  sleepScore: number | null;
  hrv: number | null;
  stress: number | null;
  bbChange: number | null;
  recommendation: string | null;
  acwr: number | null;
  vo2max: number | null;
  statusPhrase: string | null;
  index: number | null;
  sessionTitle: string | null;
  phaseCode: string | null;
  phaseName: string | null;
};

const STALE_MS = 18 * 60 * 60 * 1000;

type ReadinessDb = {
  readiness_date: string;
  updated_at?: string;
  zone: string | null;
  score_ok: number | null;
  hrv: number | null;
  bb_change: number | null;
  sleep_h: number | null;
  sleep_score: number | null;
  stress: number | null;
  recommendation: string | null;
  thresholds: Record<string, number> | null;
};

type LoadDb = {
  acwr: number | null;
  vo2max: number | null;
  status_phrase: string | null;
};

type SnapshotDb = {
  updated_at?: string;
  payload?: {
    session?: { title?: string; action?: string };
    macrocycle?: { code?: string; name?: string };
    training_load?: { acwr?: number; vo2max?: number; status_phrase?: string };
  };
};

export async function loadCondition(): Promise<ConditionSnapshot> {
  const [readinessRes, loadRes, snapshotRes] = await Promise.all([
    supabase
      .from("readiness_daily")
      .select(
        "readiness_date, updated_at, zone, score_ok, hrv, bb_change, sleep_h, sleep_score, stress, recommendation, thresholds"
      )
      .eq("user_id", MVP_USER_ID)
      .order("readiness_date", { ascending: false })
      .limit(1)
      .maybeSingle(),
    supabase
      .from("training_load")
      .select("acwr, vo2max, status_phrase")
      .eq("user_id", MVP_USER_ID)
      .order("load_date", { ascending: false })
      .limit(1)
      .maybeSingle(),
    supabase
      .from("daily_snapshots")
      .select("updated_at, payload")
      .eq("user_id", MVP_USER_ID)
      .order("snapshot_date", { ascending: false })
      .limit(1)
      .maybeSingle(),
  ]);

  const readiness = readinessRes.data as ReadinessDb | null;
  const load = loadRes.data as LoadDb | null;
  const snapshot = snapshotRes.data as SnapshotDb | null;
  const th = readiness?.thresholds || {};
  const payload = snapshot?.payload || {};
  const training = payload.training_load || {};

  const acwr = load?.acwr ?? training.acwr ?? null;
  const vo2max = load?.vo2max ?? training.vo2max ?? null;
  const statusPhrase = load?.status_phrase ?? training.status_phrase ?? null;
  const updatedAt = snapshot?.updated_at || readiness?.updated_at || null;
  const updatedMs = updatedAt ? Date.parse(updatedAt) : NaN;
  const stale = Number.isNaN(updatedMs) || Date.now() - updatedMs > STALE_MS;

  const index =
    readiness == null
      ? null
      : preparationIndex({
          zone: readiness.zone,
          scoreOk: readiness.score_ok,
          sleepH: readiness.sleep_h,
          sleepScore: readiness.sleep_score,
          hrv: readiness.hrv,
          stress: readiness.stress,
          bbChange: readiness.bb_change,
          acwr,
          vo2max,
          statusPhrase,
          hrvThreshold: th.hrv,
          sleepHThreshold: th.sleep_h,
          sleepScoreThreshold: th.sleep_score,
          bbChangeThreshold: th.bb_change,
          stressMaxThreshold: th.stress_max,
        });

  return {
    readinessDate: readiness?.readiness_date ?? null,
    updatedAt,
    stale,
    zone: readiness?.zone ?? null,
    scoreOk: readiness?.score_ok ?? null,
    sleepH: readiness?.sleep_h ?? null,
    sleepScore: readiness?.sleep_score ?? null,
    hrv: readiness?.hrv ?? null,
    stress: readiness?.stress ?? null,
    bbChange: readiness?.bb_change ?? null,
    recommendation: readiness?.recommendation ?? null,
    acwr,
    vo2max,
    statusPhrase,
    index,
    sessionTitle: payload.session?.title ?? payload.session?.action ?? null,
    phaseCode: payload.macrocycle?.code ?? null,
    phaseName: payload.macrocycle?.name ?? null,
  };
}

export function conditionPrompt(snapshot: ConditionSnapshot): string {
  const lines = [
    "Eres el coach de Diego. Respondes en español, breve y concreto.",
    "Man-in-the-loop: propones la sesión, no la impones. Si readiness es ROJO, prioriza descanso.",
    "Usa solo los números de este contexto. Si falta un dato, dilo. No inventes métricas de Garmin.",
    snapshot.stale
      ? "Los datos tienen más de 18 horas. Dilo y sugiere pulsar Actualizar antes de decidir el entreno."
      : "Los datos están dentro de las últimas 18 horas.",
    `Fecha readiness: ${snapshot.readinessDate ?? "sin dato"}`,
    `Actualizado: ${snapshot.updatedAt ?? "sin dato"}`,
    `Zona: ${snapshot.zone ?? "—"} (${snapshot.scoreOk ?? "?"}/5)`,
    `Índice de preparación 0-100: ${snapshot.index ?? "—"}`,
    `Sueño: ${snapshot.sleepH ?? "—"} h, score ${snapshot.sleepScore ?? "—"}`,
    `HRV: ${snapshot.hrv ?? "—"} ms`,
    `Estrés: ${snapshot.stress ?? "—"}`,
    `Body Battery delta: ${snapshot.bbChange ?? "—"}`,
    `ACWR: ${snapshot.acwr ?? "—"}`,
    `Estado Garmin: ${snapshot.statusPhrase ?? "—"}`,
    `VO2max: ${snapshot.vo2max ?? "—"}`,
    `Fase: ${snapshot.phaseCode ?? "—"} ${snapshot.phaseName ?? ""}`.trim(),
    `Sesión planificada: ${snapshot.sessionTitle ?? "—"}`,
    `Recomendación del motor: ${snapshot.recommendation ?? "—"}`,
  ];
  return lines.join("\n");
}
