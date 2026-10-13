type Metric = {
  label: string;
  value: string;
  ok: boolean | null;
};

type Props = {
  zone: string;
  scoreOk: number | null;
  recommendation: string;
  metrics: Metric[];
  statusPhrase?: string;
  acwr?: number;
  vo2max?: number;
};

function zoneClass(zone: string) {
  return `badge badge-${zone}`;
}

function metricStatus(ok: boolean | null): "ok" | "bad" | "na" {
  if (ok == null) return "na";
  return ok ? "ok" : "bad";
}

export function TodayCard({
  zone,
  scoreOk,
  recommendation,
  metrics,
  statusPhrase,
  acwr,
  vo2max,
}: Props) {
  return (
    <section className="card card-highlight">
      <h2 style={{ marginTop: 0 }}>Hoy</h2>
      <span className={zoneClass(zone)}>
        {zone} {scoreOk ?? "?"}/5
      </span>
      <p className="recommendation">{recommendation}</p>
      <div className="metrics-grid">
        {metrics.map((m) => (
          <div key={m.label} className={`metric-cell ${metricStatus(m.ok)}`}>
            <span className="metric-label">{m.label}</span>
            <span className="metric-value">{m.value}</span>
          </div>
        ))}
      </div>
      {statusPhrase || acwr != null ? (
        <p className="load-line">
          Carga: {statusPhrase || "—"}
          {acwr != null ? ` · ACWR ${acwr.toFixed(1)}` : ""}
          {vo2max != null ? ` · VO₂ ${vo2max}` : ""}
        </p>
      ) : null}
    </section>
  );
}
