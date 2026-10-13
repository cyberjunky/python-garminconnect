import {
  EVENTS,
  daysUntilAcwrTarget,
  recoveryLocalDaysRemaining,
} from "@/lib/preparation";

type Props = {
  todayIso: string;
  acwr: number | null | undefined;
  phaseCode?: string;
  phaseName?: string;
  macrocycle?: {
    code?: string;
    name?: string;
    focus?: string;
    end?: string;
    start?: string;
  };
};

function daysToEvent(eventDate: string, todayIso: string): number {
  const a = new Date(todayIso + "T12:00:00").getTime();
  const b = new Date(eventDate + "T12:00:00").getTime();
  return Math.max(0, Math.round((b - a) / 86400000));
}

export function RecoveryMilestonesCard({
  todayIso,
  acwr,
  phaseCode,
  phaseName,
  macrocycle,
}: Props) {
  const code = macrocycle?.code ?? phaseCode ?? "R0";
  const name = macrocycle?.name ?? phaseName;
  const title = name ? `${name} (${code})` : `Fase ${code}`;

  const phaseEndDate = macrocycle?.end;
  const daysRemaining = phaseEndDate
    ? daysToEvent(phaseEndDate, todayIso)
    : code === "R0"
    ? recoveryLocalDaysRemaining(todayIso)
    : null;

  const acwrDays = daysUntilAcwrTarget(acwr, 1.0);

  return (
    <section className="card card-recovery">
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <div className="recovery-hero">
        {daysRemaining != null ? (
          <span className="recovery-number">{daysRemaining}</span>
        ) : null}
        <span className="recovery-label">
          {daysRemaining != null ? `días para cerrar fase ${code}` : `Fase ${code}`}
          {name ? ` · ${name}` : ""}
          {phaseEndDate || macrocycle?.focus ? (
            <>
              <br />
              <span className="muted">
                {phaseEndDate ? `meta: ${phaseEndDate}` : ""}
                {phaseEndDate && macrocycle?.focus ? " · " : ""}
                {macrocycle?.focus ?? ""}
              </span>
            </>
          ) : null}
        </span>
      </div>
      {acwr != null && acwr > 1.0 ? (
        <p className="muted" style={{ margin: "0.75rem 0 0" }}>
          ACWR {acwr.toFixed(1)} — estimado ~{acwrDays ?? "?"} días de descanso/Z1 para bajar de 1.0
          (heurística).
        </p>
      ) : (
        <p className="muted" style={{ margin: "0.75rem 0 0" }}>
          ACWR en rango {code} ✓
        </p>
      )}

      <h3 className="milestones-sub">Retos</h3>
      <ul className="milestone-list">
        {EVENTS.map((ev) => (
          <li key={ev.code}>
            <span className="milestone-dot" style={{ background: ev.color }} />
            <span className="milestone-name">
              {ev.href ? (
                <a href={ev.href} target="_blank" rel="noreferrer">
                  {ev.shortLabel}
                </a>
              ) : (
                ev.shortLabel
              )}
            </span>
            <span className="milestone-date">{ev.eventDate}</span>
            <span className="milestone-days">{daysToEvent(ev.eventDate, todayIso)}d</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
