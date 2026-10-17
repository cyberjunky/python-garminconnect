import { PreparationChart } from "@/components/PreparationChart";
import { todayBogotaIso } from "@/lib/lastUpdated";
import {
  buildFocusItems,
  buildWins,
  fetchDashboard,
  type SnapshotPayload,
} from "@/lib/dashboard";
import { getMacrocycleDetails } from "@/lib/mesocycle";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function RetosPage() {
  const { readiness, snapshot, preparationTrend, error } = await fetchDashboard();
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

  const macrocycle = getMacrocycleDetails(
    todayIso,
    payload.macrocycle,
    payload.milestones,
    readiness?.zone,
    training.acwr
  );

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

      <section className="card macrocycle-card" aria-label="Macrociclo en 4 bloques">
        <h2 className="mt-0">Macrociclo</h2>

        <div className="macrocycle-blocks" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Bloque A: Definición pedagógica */}
          <div
            className="macro-block block-a"
            style={{
              padding: "0.85rem 1rem",
              background: "var(--card-subtle)",
              borderRadius: "8px",
              borderLeft: "3px solid var(--proyeccion)",
            }}
          >
            <h3 style={{ margin: "0 0 0.35rem", fontSize: "0.95rem", color: "var(--proyeccion)" }}>
              {macrocycle.definition.title}
            </h3>
            <p className="m-0" style={{ fontSize: "0.875rem", lineHeight: 1.5, color: "var(--text)" }}>
              {macrocycle.definition.text}
            </p>
          </div>

          {/* Bloque B: Momento y fase actual */}
          <div
            className="macro-block block-b"
            style={{
              padding: "0.85rem 1rem",
              background: "var(--card-subtle)",
              borderRadius: "8px",
              borderLeft: "3px solid var(--carrera)",
            }}
          >
            <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.95rem", color: "var(--carrera)" }}>
              Momento actual — {macrocycle.currentPhase.code} {macrocycle.currentPhase.name}
            </h3>
            <div
              className="macro-phase-grid"
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "0.5rem",
                fontSize: "0.875rem",
              }}
            >
              <div>
                <span className="muted">Foco:</span> <strong>{macrocycle.currentPhase.focus}</strong>
              </div>
              <div>
                <span className="muted">Deporte(s):</span> <strong>{macrocycle.currentPhase.sport}</strong>
              </div>
              <div>
                <span className="muted">Techo FC:</span> <strong>{macrocycle.currentPhase.hrCap} bpm</strong>
              </div>
              <div>
                <span className="muted">Duración máx:</span> <strong>{macrocycle.currentPhase.maxDurationMin} min</strong>
              </div>
            </div>
          </div>

          {/* Bloque C: Cómo mejorarla */}
          <div
            className="macro-block block-c"
            style={{
              padding: "0.85rem 1rem",
              background: "var(--card-subtle)",
              borderRadius: "8px",
              borderLeft: "3px solid var(--amarillo)",
            }}
          >
            <h3 style={{ margin: "0 0 0.35rem", fontSize: "0.95rem", color: "var(--amarillo)" }}>
              {macrocycle.howToImprove.title}
            </h3>
            <p className="m-0" style={{ fontSize: "0.875rem", lineHeight: 1.5, color: "var(--text)" }}>
              {macrocycle.howToImprove.recommendation}
            </p>
          </div>

          {/* Bloque D: Cuándo termina e hitos */}
          <div
            className="macro-block block-d"
            style={{
              padding: "0.85rem 1rem",
              background: "var(--card-subtle)",
              borderRadius: "8px",
              borderLeft: "3px solid var(--verde)",
            }}
          >
            <h3 style={{ margin: "0 0 0.35rem", fontSize: "0.95rem", color: "var(--verde)" }}>
              Cuándo termina
            </h3>
            <p style={{ margin: "0 0 0.75rem", fontSize: "0.875rem" }}>
              Cierre de fase {macrocycle.currentPhase.code}: <strong>{macrocycle.timing.phaseEndDateFormatted}</strong>{" "}
              <span className="muted">({macrocycle.timing.daysRemainingPhase} días restantes)</span>
            </p>
            <div className="macro-milestones">
              <span className="milestones-sub" style={{ display: "block", marginBottom: "0.35rem" }}>
                Hitos clave de la temporada
              </span>
              <ul className="list" style={{ fontSize: "0.85rem" }}>
                {macrocycle.timing.milestones.map((m) => (
                  <li key={m.code}>
                    <span>{m.name}</span> · <span className="muted">{m.eventDateFormatted}</span> ·{" "}
                    <strong>{m.daysRemaining} días</strong>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
