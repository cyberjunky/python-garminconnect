import { buildActualSeries } from "@/lib/preparation";
import { MVP_USER_ID, supabase } from "@/lib/supabase";

export type ReadinessRow = {
  readiness_date: string;
  updated_at?: string;
  zone: string;
  score_ok: number | null;
  hrv: number | null;
  bb_change: number | null;
  sleep_h: number | null;
  sleep_score: number | null;
  stress: number | null;
  recommendation: string | null;
  thresholds: Record<string, number> | null;
};

export type HistoryRow = {
  readiness_date: string;
  zone: string;
  score_ok: number | null;
  hrv: number | null;
};

export type SnapshotPayload = {
  date?: string;
  macrocycle?: { code?: string; name?: string; focus?: string; hr_cap?: number };
  milestones?: { code: string; days_remaining: number }[];
  session?: {
    title?: string;
    action?: string;
    sport?: string;
    duration_min?: number;
    hr_cap?: number;
    guard_flags?: string[];
    details?: string[];
  };
  training_load?: {
    status_phrase?: string;
    acwr?: number;
    acwr_status?: string;
    vo2max?: number;
  };
  last_activity?: {
    activity_id: number;
    name: string;
    sport: string;
    type_key?: string | null;
    type_label?: string | null;
    start_time_local?: string | null;
    start_time_gmt?: string | null;
    duration_min?: number | null;
    distance_km?: number | null;
    elevation_gain_m?: number | null;
    avg_hr?: number | null;
    max_hr?: number | null;
    calories?: number | null;
    training_load?: number | null;
  };
  readiness?: { recommendation?: string };
  thresholds?: Record<string, number>;
};

export type SnapshotRow = {
  snapshot_date: string;
  payload: SnapshotPayload;
  updated_at?: string;
};

type LoadRow = {
  load_date: string;
  acwr: number | null;
  vo2max: number | null;
  status_phrase: string | null;
};

export function zoneClass(zone: string) {
  return `badge badge-${zone}`;
}

export function buildFocusItems(readiness: ReadinessRow | null, payload: SnapshotPayload): string[] {
  const items: string[] = [];
  const th = readiness?.thresholds || payload.thresholds || {};
  const r = readiness;

  if (r?.sleep_h != null && th.sleep_h != null && r.sleep_h < th.sleep_h) {
    items.push(`Sueño ${r.sleep_h.toFixed(1)} h — meta ≥${th.sleep_h} h`);
  }
  if (r?.sleep_score != null && th.sleep_score != null && r.sleep_score < th.sleep_score) {
    items.push(`Sleep score ${r.sleep_score} — meta ≥${th.sleep_score}`);
  }
  if (r?.hrv != null && th.hrv != null && r.hrv < th.hrv) {
    items.push(`HRV ${r.hrv.toFixed(0)} ms — meta ≥${th.hrv} ms`);
  }
  if (r?.bb_change != null && th.bb_change != null && r.bb_change < th.bb_change) {
    items.push(`Body Battery +${r.bb_change} — meta ≥+${th.bb_change}`);
  }
  const acwr = payload.training_load?.acwr;
  if (acwr != null && acwr > 1.3) {
    items.push(`ACWR ${acwr.toFixed(1)} — meta <1.3 (descanso hasta baje)`);
  }
  if (payload.training_load?.status_phrase === "OVERREACHING") {
    items.push("Garmin: OVERREACHING — cero intensidad");
  }
  if (items.length === 0 && r?.zone === "VERDE") {
    items.push("Indicadores alineados — puedes confirmar sesión del día");
  }
  return items;
}

export function buildWins(readiness: ReadinessRow | null, payload: SnapshotPayload): string[] {
  const wins: string[] = [];
  const th = readiness?.thresholds || payload.thresholds || {};
  const r = readiness;
  if (r?.sleep_h != null && th.sleep_h != null && r.sleep_h >= th.sleep_h) {
    wins.push(`Sueño ${r.sleep_h.toFixed(1)} h ✓`);
  }
  if (r?.stress != null && th.stress_max != null && r.stress <= th.stress_max) {
    wins.push(`Estrés ${r.stress} ✓`);
  }
  const acwr = payload.training_load?.acwr;
  if (acwr != null && acwr < 2.2) {
    wins.push(`ACWR bajando (${acwr.toFixed(1)})`);
  }
  if (payload.training_load?.vo2max != null) {
    wins.push(`VO₂max ${payload.training_load.vo2max} — base conservada`);
  }
  return wins;
}

export async function fetchDashboard() {
  const [readinessRes, snapshotRes, historyRes, loadRes, trendRes] = await Promise.all([
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
      .from("daily_snapshots")
      .select("snapshot_date, payload, updated_at")
      .eq("user_id", MVP_USER_ID)
      .order("snapshot_date", { ascending: false })
      .limit(1)
      .maybeSingle(),
    supabase
      .from("readiness_daily")
      .select("readiness_date, zone, score_ok, hrv")
      .eq("user_id", MVP_USER_ID)
      .order("readiness_date", { ascending: false })
      .limit(14),
    supabase
      .from("training_load")
      .select("load_date, acwr, vo2max, status_phrase")
      .eq("user_id", MVP_USER_ID)
      .order("load_date", { ascending: false })
      .limit(60),
    supabase
      .from("readiness_daily")
      .select(
        "readiness_date, zone, score_ok, hrv, bb_change, sleep_h, sleep_score, stress, thresholds"
      )
      .eq("user_id", MVP_USER_ID)
      .order("readiness_date", { ascending: false })
      .limit(120),
  ]);

  const loadByDate = new Map<string, LoadRow>();
  for (const row of (loadRes.data || []) as LoadRow[]) {
    loadByDate.set(row.load_date, row);
  }

  const trendRows = ((trendRes.data || []) as ReadinessRow[]).map((r) => {
    const load = loadByDate.get(r.readiness_date);
    const th = r.thresholds || {};
    return {
      date: r.readiness_date,
      zone: r.zone,
      score_ok: r.score_ok,
      hrv: r.hrv,
      sleep_h: r.sleep_h,
      sleep_score: r.sleep_score,
      stress: r.stress,
      bb_change: r.bb_change,
      acwr: load?.acwr ?? null,
      vo2max: load?.vo2max ?? null,
      status_phrase: load?.status_phrase ?? null,
      hrv_threshold: th.hrv,
      sleep_h_threshold: th.sleep_h,
      sleep_score_threshold: th.sleep_score,
      bb_change_threshold: th.bb_change,
      stress_max_threshold: th.stress_max,
    };
  });

  return {
    readiness: readinessRes.data as ReadinessRow | null,
    snapshot: snapshotRes.data as SnapshotRow | null,
    history: (historyRes.data || []) as HistoryRow[],
    preparationTrend: buildActualSeries(trendRows),
    error: readinessRes.error?.message || snapshotRes.error?.message,
  };
}
