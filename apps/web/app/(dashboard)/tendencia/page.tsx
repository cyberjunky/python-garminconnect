import { fetchMonthlyTrend } from "@/lib/tendencia";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function TendenciaPage() {
  const { rows, distribution, summary, error } = await fetchMonthlyTrend();

  if (error || rows.length === 0) {
    return (
      <main>
        <h1 className="page-title">Tendencia mensual</h1>
        <p className="page-subtitle muted">
          Evolución fisiológica y distribución de carga de los últimos 30 días
        </p>
        <div className="card">
          <h2 className="mt-0">Sin registros para el periodo</h2>
          <p className="muted">
            {error ||
              "No se pudieron cargar datos para los últimos 30 días o no hay registros disponibles. Vuelve a consultar más tarde."}
          </p>
        </div>
      </main>
    );
  }

  const { counts, percentages, totalDays } = distribution;

  return (
    <main>
      <header className="page-header">
        <h1 className="page-title">Tendencia mensual</h1>
        <p className="page-subtitle muted">
          Evolución fisiológica y distribución de carga en los últimos 30 días ({totalDays} días
          evaluados)
        </p>
      </header>

      {/* Sección 1: Barra de distribución mensual de zonas */}
      <section className="card zone-distribution-section" aria-labelledby="heading-distribution">
        <div className="section-title-wrap">
          <h2 id="heading-distribution" className="mt-0">
            Distribución de zonas (30 días)
          </h2>
          <span className="zone-compliance-badge">
            {summary.zoneCompliancePct}% en zona verde
          </span>
        </div>

        <p className="muted">
          Proporción de días en preparación VERDE (óptima), AMARILLO (precaución) y ROJO
          (descarga requerida).
        </p>

        <div
          className="zone-bar-track"
          role="meter"
          aria-label="Distribución de preparación mensual"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percentages.VERDE}
        >
          {percentages.VERDE > 0 ? (
            <div
              className="zone-bar-segment segment-verde"
              style={{ width: `${percentages.VERDE}%` }}
              title={`VERDE: ${counts.VERDE} días (${percentages.VERDE}%)`}
            />
          ) : null}
          {percentages.AMARILLO > 0 ? (
            <div
              className="zone-bar-segment segment-amarillo"
              style={{ width: `${percentages.AMARILLO}%` }}
              title={`AMARILLO: ${counts.AMARILLO} días (${percentages.AMARILLO}%)`}
            />
          ) : null}
          {percentages.ROJO > 0 ? (
            <div
              className="zone-bar-segment segment-rojo"
              style={{ width: `${percentages.ROJO}%` }}
              title={`ROJO: ${counts.ROJO} días (${percentages.ROJO}%)`}
            />
          ) : null}
        </div>

        <div className="zone-bar-legend">
          <div className="legend-item">
            <span className="legend-dot dot-verde" aria-hidden="true" />
            <span className="legend-label">VERDE</span>
            <span className="legend-value tabular-nums">
              {counts.VERDE} días ({percentages.VERDE}%)
            </span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-amarillo" aria-hidden="true" />
            <span className="legend-label">AMARILLO</span>
            <span className="legend-value tabular-nums">
              {counts.AMARILLO} días ({percentages.AMARILLO}%)
            </span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-rojo" aria-hidden="true" />
            <span className="legend-label">ROJO</span>
            <span className="legend-value tabular-nums">
              {counts.ROJO} días ({percentages.ROJO}%)
            </span>
          </div>
        </div>
      </section>

      {/* Sección 2: Resumen consolidado mensual */}
      <section className="card trend-summary-section" aria-labelledby="heading-summary">
        <h2 id="heading-summary" className="mt-0">
          Resumen consolidado (Promedios 30 días)
        </h2>
        <div className="trend-metrics-grid">
          <div className="trend-metric-card">
            <span className="metric-card-label">{summary.hrv.label}</span>
            <span className="metric-card-value tabular-nums">
              {summary.hrv.averageValue != null ? `${summary.hrv.averageValue} ms` : "—"}
            </span>
            <span className="metric-card-target muted">Meta: {summary.hrv.target}</span>
            <span className="metric-card-status">{summary.hrv.statusLabel}</span>
          </div>

          <div className="trend-metric-card">
            <span className="metric-card-label">{summary.sleepHours.label}</span>
            <span className="metric-card-value tabular-nums">
              {summary.sleepHours.averageValue != null
                ? `${summary.sleepHours.averageValue.toFixed(1)} h`
                : "—"}
            </span>
            <span className="metric-card-target muted">Meta: {summary.sleepHours.target}</span>
            <span className="metric-card-status">{summary.sleepHours.statusLabel}</span>
          </div>

          <div className="trend-metric-card">
            <span className="metric-card-label">{summary.sleepScore.label}</span>
            <span className="metric-card-value tabular-nums">
              {summary.sleepScore.averageValue != null
                ? `${summary.sleepScore.averageValue} pts`
                : "—"}
            </span>
            <span className="metric-card-target muted">Meta: {summary.sleepScore.target}</span>
            <span className="metric-card-status">{summary.sleepScore.statusLabel}</span>
          </div>

          <div className="trend-metric-card">
            <span className="metric-card-label">{summary.bodyBatteryChange.label}</span>
            <span className="metric-card-value tabular-nums">
              {summary.bodyBatteryChange.averageValue != null
                ? `${summary.bodyBatteryChange.averageValue > 0 ? "+" : ""}${summary.bodyBatteryChange.averageValue} pts`
                : "—"}
            </span>
            <span className="metric-card-target muted">
              Meta: {summary.bodyBatteryChange.target}
            </span>
            <span className="metric-card-status">{summary.bodyBatteryChange.statusLabel}</span>
          </div>

          <div className="trend-metric-card">
            <span className="metric-card-label">{summary.stress.label}</span>
            <span className="metric-card-value tabular-nums">
              {summary.stress.averageValue != null ? `${summary.stress.averageValue}` : "—"}
            </span>
            <span className="metric-card-target muted">Meta: {summary.stress.target}</span>
            <span className="metric-card-status">{summary.stress.statusLabel}</span>
          </div>

          <div className="trend-metric-card">
            <span className="metric-card-label">{summary.acwr.label}</span>
            <span className="metric-card-value tabular-nums">
              {summary.acwr.averageValue != null ? `${summary.acwr.averageValue.toFixed(2)}` : "—"}
            </span>
            <span className="metric-card-target muted">Meta: {summary.acwr.target}</span>
            <span className="metric-card-status">{summary.acwr.statusLabel}</span>
          </div>

          <div className="trend-metric-card">
            <span className="metric-card-label">{summary.vo2max.label}</span>
            <span className="metric-card-value tabular-nums">
              {summary.vo2max.averageValue != null
                ? `${summary.vo2max.averageValue.toFixed(1)}`
                : "—"}
            </span>
            <span className="metric-card-target muted">Meta: {summary.vo2max.target}</span>
            <span className="metric-card-status">{summary.vo2max.statusLabel}</span>
          </div>
        </div>
      </section>

      {/* Sección 3: Tabla de evolución diaria */}
      <section className="card trend-history-section" aria-labelledby="heading-history">
        <h2 id="heading-history" className="mt-0">
          Evolución diaria de 30 días
        </h2>
        <div className="trend-table-wrap">
          <table className="history-table trend-table" aria-label="Historial mensual de 30 días">
            <thead>
              <tr>
                <th scope="col">Fecha</th>
                <th scope="col">Zona</th>
                <th scope="col" className="text-right">
                  Score
                </th>
                <th scope="col" className="text-right">
                  HRV
                </th>
                <th scope="col" className="text-right">
                  Sueño
                </th>
                <th scope="col" className="text-right">
                  Calidad
                </th>
                <th scope="col" className="text-right">
                  Estrés
                </th>
                <th scope="col" className="text-right">
                  Body Battery
                </th>
                <th scope="col" className="text-right">
                  ACWR
                </th>
                <th scope="col" className="text-right">
                  VO₂max
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.date}>
                  <td className="cell-date">{row.dateFormatted}</td>
                  <td>
                    <span className={`badge badge-${row.zone}`}>{row.zone}</span>
                  </td>
                  <td className="tabular-nums text-right">{row.scoreOk ?? "—"}</td>
                  <td className="tabular-nums text-right">
                    {row.hrv != null ? `${row.hrv} ms` : "—"}
                  </td>
                  <td className="tabular-nums text-right">
                    {row.sleepHours != null ? `${row.sleepHours.toFixed(1)} h` : "—"}
                  </td>
                  <td className="tabular-nums text-right">{row.sleepScore ?? "—"}</td>
                  <td className="tabular-nums text-right">{row.stress ?? "—"}</td>
                  <td className="tabular-nums text-right">
                    {row.bbChange != null
                      ? `${row.bbChange > 0 ? "+" : ""}${row.bbChange}`
                      : "—"}
                  </td>
                  <td className="tabular-nums text-right">
                    {row.acwr != null ? row.acwr.toFixed(2) : "—"}
                  </td>
                  <td className="tabular-nums text-right">{row.vo2max ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
