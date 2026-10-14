import { formatGarminStatus } from "@/lib/dashboard";

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
      <h2 className="mt-0">Hoy</h2>
      <span className={zoneClass(zone)} role="status">
        {zone} {scoreOk ?? "?"}/5
      </span>
      <p className="recommendation">{recommendation}</p>
      <div className="metrics-grid">
        {metrics.map((m) => (
          <div key={m.label} className={`metric-cell ${metricStatus(m.ok)}`}>
            <div className="metric-label-row">
              <span className="metric-label">{m.label}</span>
              {m.ok === true ? (
                <span className="metric-status-badge ok" title="En rango óptimo" aria-label="Óptimo">
                  ✓
                </span>
              ) : m.ok === false ? (
                <span className="metric-status-badge bad" title="Requiere atención" aria-label="Atención">
                  !
                </span>
              ) : null}
            </div>
            <span className="metric-value">{m.value}</span>
          </div>
        ))}
      </div>
      {statusPhrase || acwr != null ? (
        <p className="load-line">
          Carga: {formatGarminStatus(statusPhrase)}
          {acwr != null ? ` · ACWR ${acwr.toFixed(1)}` : ""}
          {vo2max != null ? ` · VO₂ ${vo2max}` : ""}
        </p>
      ) : null}
    </section>
  );
}
