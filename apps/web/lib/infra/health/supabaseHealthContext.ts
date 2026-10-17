import type { SupabaseClient } from "@supabase/supabase-js";
import type { IHealthContextPort } from "../../chat/application/ports";
import { HealthProfileNotLinkedError } from "../../chat/domain/errors";
import { conditionPrompt, type ConditionSnapshot } from "../../condition";
import { preparationIndex } from "../../preparation";
import { getSupabaseAnon } from "../supabase";

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

export async function fetchHealthConditionSnapshot(
  supabaseClient: SupabaseClient,
  profileId: string
): Promise<ConditionSnapshot> {
  const [readinessRes, loadRes, snapshotRes] = await Promise.all([
    supabaseClient
      .from("readiness_daily")
      .select(
        "readiness_date, updated_at, zone, score_ok, hrv, bb_change, sleep_h, sleep_score, stress, recommendation, thresholds"
      )
      .eq("user_id", profileId)
      .order("readiness_date", { ascending: false })
      .limit(1)
      .maybeSingle(),
    supabaseClient
      .from("training_load")
      .select("acwr, vo2max, status_phrase")
      .eq("user_id", profileId)
      .order("load_date", { ascending: false })
      .limit(1)
      .maybeSingle(),
    supabaseClient
      .from("daily_snapshots")
      .select("updated_at, payload")
      .eq("user_id", profileId)
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

export interface SupabaseHealthContextOptions {
  supabaseClient?: SupabaseClient;
}

export class SupabaseHealthContext implements IHealthContextPort {
  private readonly supabaseClient: SupabaseClient;

  constructor(options: SupabaseHealthContextOptions = {}) {
    this.supabaseClient = options.supabaseClient || getSupabaseAnon();
  }

  async getHealthContext(ownerId: string): Promise<{ promptText: string; profileId: string }> {
    // 1. Verificar si el owner autenticado tiene vinculo autorizado en coach_profile_links (REQ-014)
    const { data: link, error } = await this.supabaseClient
      .from("coach_profile_links")
      .select("profile_id")
      .eq("auth_user_id", ownerId)
      .maybeSingle();

    if (error || !link?.profile_id) {
      throw new HealthProfileNotLinkedError();
    }

    // 2. Consultar métricas del perfil vinculado en servidor
    const snapshot = await fetchHealthConditionSnapshot(this.supabaseClient, link.profile_id);
    const promptText = conditionPrompt(snapshot);

    return {
      promptText,
      profileId: link.profile_id,
    };
  }
}
