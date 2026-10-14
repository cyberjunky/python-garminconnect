import { PreparationChart } from "@/components/PreparationChart";
import { formatDateEsCO, todayBogotaIso } from "@/lib/lastUpdated";
import {
  buildFocusItems,
  buildWins,
  fetchDashboard,
  zoneClass,
  type SnapshotPayload,
} from "@/lib/dashboard";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function RetosPage() {
  const { readiness, snapshot, history, preparationTrend, error } = await fetchDashboard();
  const payload: SnapshotPayload = snapshot?.payload || {};

  if (error && !readiness) {
    return (
      <main>
        <h1 className="page-title">Retos</h1>
        <p className="muted">
          No se pudieron cargar los datos de retos en este momento. Intenta de nuevo más tarde.
        </p>
      </main>
    );
  }

  const focus = buildFocusItems(readiness, payload);
  const wins = buildWins(readiness, payload);
  const session = payload.session || {};
  const training = payload.training_load || {};
  const todayIso = readiness?.readiness_date || snapshot?.snapshot_date || todayBogotaIso();

  const counts = { VERDE: 0, AMARILLO: 0, ROJO: 0 };
  for (const row of history) {
    if (row.zone in counts) counts[row.zone as keyof typeof counts]++;
  }
  const total = history.length || 1;

  return (
    <main>
      <h1 className="page-title">Retos</h1>

      <section className="card">
        <h2 className="mt-0">Preparación vs retos</h2>
        <PreparationChart actual={preparationTrend} todayIso={todayIso} vo2max={training.vo2max} />
      </section>

      <section className="card">
        <h2 className="mt-0">Sesión</h2>
        <p className="session-title">{session.title || session.action || "—"}</p>
        {session.duration_min != null && session.duration_min > 0 ? (
          <p className="muted">
            {session.duration_min} min · FC techo {session.hr_cap ?? payload.macrocycle?.hr_cap} bpm
          </p>
        ) : null}
        {(session.details || []).map((d) => (
          <p key={d} className="detail-line">
            {d}
          </p>
        ))}
        {session.guard_flags?.length ? (
          <p className="guards">Restricciones: {session.guard_flags.join(" · ")}</p>
        ) : null}
      </section>

      <div className="two-col">
        <section className="card">
          <h2 className="mt-0">Qué atender</h2>
          <ul className="list">
            {focus.length ? focus.map((item) => <li key={item}>{item}</li>) : <li>—</li>}
          </ul>
        </section>
        <section className="card">
          <h2 className="mt-0">Qué va bien</h2>
          <ul className="list list-ok">
            {wins.length ? wins.map((w) => <li key={w}>{w}</li>) : <li>—</li>}
          </ul>
        </section>
      </div>

      <section className="card">
        <h2 className="mt-0">Macrociclo</h2>
        <p className="m-0">
          {payload.macrocycle?.code} {payload.macrocycle?.name}
        </p>
        <p className="muted">{payload.macrocycle?.focus}</p>
      </section>

      <section className="card">
        <h2 className="mt-0">Tendencia 14d</h2>
        <div className="chart-bar">
          <span style={{ width: `${(counts.VERDE / total) * 100}%`, background: "var(--verde)" }} />
          <span style={{ width: `${(counts.AMARILLO / total) * 100}%`, background: "var(--amarillo)" }} />
          <span style={{ width: `${(counts.ROJO / total) * 100}%`, background: "var(--rojo)" }} />
        </div>
        <p className="muted">
          VERDE {counts.VERDE} · AMARILLO {counts.AMARILLO} · ROJO {counts.ROJO}
        </p>
        <table className="history-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Zona</th>
              <th>HRV</th>
            </tr>
          </thead>
          <tbody>
            {history.map((row) => (
              <tr key={row.readiness_date}>
                <td>{formatDateEsCO(row.readiness_date)}</td>
                <td>
                  <span className={zoneClass(row.zone)}>{row.zone}</span>
                </td>
                <td>{row.hrv?.toFixed(0) ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
