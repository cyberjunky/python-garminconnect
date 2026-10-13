import { CoachChat } from "@/components/CoachChat";
import { LastActivityCard } from "@/components/LastActivityCard";
import { RecoveryMilestonesCard } from "@/components/RecoveryMilestonesCard";
import { TodayCard } from "@/components/TodayCard";
import { fetchDashboard } from "@/lib/dashboard";
import { formatLastUpdatedLabel, latestTimestamp } from "@/lib/lastUpdated";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const RULES = [
  "Max 2 cafés antes de las 11:00",
  "Sueño ≥7.5 h esta noche",
  "0 alcohol post-carga",
  "ACWR objetivo <1.3",
  "80% del tiempo en Z1–Z2",
  "Hidratación 2.5–3 L/día",
  "Proteína ≥110 g/día",
];

export default async function HomePage() {
  const { readiness, snapshot, error } = await fetchDashboard();
  const payload = snapshot?.payload || {};
  const th = readiness?.thresholds || payload.thresholds || {};

  if (error && !readiness) {
    return (
      <main>
        <h1>Fitness Coach</h1>
        <p className="muted">Configure NEXT_PUBLIC_SUPABASE_URL y ANON_KEY. {error}</p>
      </main>
    );
  }

  const zone = readiness?.zone || "?";
  const training = payload.training_load || {};
  const dateLabel = readiness?.readiness_date || snapshot?.snapshot_date || "—";
  const lastUpdatedLabel = formatLastUpdatedLabel(
    latestTimestamp(snapshot?.updated_at, readiness?.updated_at)
  );
  const ruleIdx = dateLabel !== "—" ? new Date(dateLabel).getDay() % RULES.length : 0;
  const todayIso = dateLabel !== "—" ? dateLabel : new Date().toISOString().slice(0, 10);

  const metrics = [
    {
      label: "Sueño",
      value: readiness?.sleep_h != null ? `${readiness.sleep_h.toFixed(1)} h` : "—",
      ok: readiness?.sleep_h != null && th.sleep_h != null ? readiness.sleep_h >= th.sleep_h : null,
    },
    {
      label: "Sleep score",
      value: readiness?.sleep_score?.toString() ?? "—",
      ok:
        readiness?.sleep_score != null && th.sleep_score != null
          ? readiness.sleep_score >= th.sleep_score
          : null,
    },
    {
      label: "HRV",
      value: readiness?.hrv != null ? `${readiness.hrv.toFixed(0)} ms` : "—",
      ok: readiness?.hrv != null && th.hrv != null ? readiness.hrv >= th.hrv : null,
    },
    {
      label: "Estrés",
      value: readiness?.stress?.toString() ?? "—",
      ok:
        readiness?.stress != null && th.stress_max != null
          ? readiness.stress <= th.stress_max
          : null,
    },
    {
      label: "BB Δ",
      value: readiness?.bb_change != null ? `+${readiness.bb_change}` : "—",
      ok:
        readiness?.bb_change != null && th.bb_change != null
          ? readiness.bb_change >= th.bb_change
          : null,
    },
  ];

  return (
    <main>
      <p className="muted" style={{ marginTop: 0 }}>
        {lastUpdatedLabel}
      </p>

      <CoachChat />

      <TodayCard
        zone={zone}
        scoreOk={readiness?.score_ok ?? null}
        recommendation={readiness?.recommendation || payload.readiness?.recommendation || "—"}
        metrics={metrics}
        statusPhrase={training.status_phrase}
        acwr={training.acwr}
        vo2max={training.vo2max}
      />

      <LastActivityCard activity={payload.last_activity} />

      <RecoveryMilestonesCard
        todayIso={todayIso}
        acwr={training.acwr}
        phaseCode={payload.macrocycle?.code}
        phaseName={payload.macrocycle?.name}
      />

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Regla del día</h2>
        <p style={{ margin: 0 }}>{RULES[ruleIdx]}</p>
      </section>
    </main>
  );
}
