import type { WeeklySportRow } from "@/lib/mesocycle";
import { formatDateEsCO } from "@/lib/lastUpdated";

type Props = { weeks: WeeklySportRow[] };

function fmt(n: number | null | undefined) {
  if (n == null) return "—";
  return `${Math.round(n)} min`;
}

function SportBars({
  label,
  planned,
  executed,
  color,
}: {
  label: string;
  planned: number;
  executed: number;
  color: string;
}) {
  const max = Math.max(planned, executed, 1);
  return (
    <div className="meso-sport-row">
      <span className="meso-sport-label">{label}</span>
      <div className="meso-bar-group">
        <div className="meso-bar-track" title={`Plan: ${fmt(planned)}`}>
          <div className="meso-bar planned" style={{ width: `${(planned / max) * 100}%`, background: color, opacity: 0.45 }} />
        </div>
        <div className="meso-bar-track" title={`Garmin: ${fmt(executed)}`}>
          <div className="meso-bar executed" style={{ width: `${(executed / max) * 100}%`, background: color }} />
        </div>
      </div>
      <span className="meso-sport-nums muted">
        {fmt(planned)} / {fmt(executed)}
      </span>
    </div>
  );
}

export function MesocycleVolumeChart({ weeks }: Props) {
  if (!weeks.length) {
    return (
      <p className="muted">
        Sin datos de volumen ejecutado aún. Tras el próximo collect diario (Garmin → Supabase) verás plan vs
        realizado por semana.
      </p>
    );
  }

  return (
    <div className="meso-weeks">
      {weeks.map((w) => {
        const recovery = w.kind === "recovery";
        const runP = w.planned_run_min ?? 0;
        const bikeP = w.planned_bike_min ?? 0;
        const swimP = w.planned_swim_min ?? 0;
        const runE = w.executed_run_min ?? 0;
        const bikeE = w.executed_bike_min ?? 0;
        const swimE = w.executed_swim_min ?? 0;
        return (
          <article key={w.week_start} className={`card meso-week ${recovery ? "meso-recovery" : ""}`}>
            <header className="meso-week-head">
              <div>
                <strong>Semana del {formatDateEsCO(w.week_start)}</strong>
                <span className="muted">
                  {" "}
                  · Bloque {(w.block_index ?? 0) + 1} · S{(w.week_in_block ?? 0) + 1}/4 · {w.phase_code}
                </span>
              </div>
              {recovery ? <span className="badge badge-AMARILLO">Recuperación 3+1</span> : null}
            </header>
            <p className="muted meso-legend">
              Barras claras = plan · sólidas = Garmin · Lunes siempre recuperación en el plan
            </p>
            <SportBars label="Carrera" planned={runP} executed={runE} color="var(--carrera)" />
            <SportBars label="Ciclismo" planned={bikeP} executed={bikeE} color="var(--ciclismo)" />
            <SportBars label="Natación" planned={swimP} executed={swimE} color="var(--natacion)" />
            <p className="muted meso-total">
              Total semana: plan {fmt(w.planned_total_min)} · Garmin {fmt(w.executed_total_min)}
            </p>
          </article>
        );
      })}
    </div>
  );
}
