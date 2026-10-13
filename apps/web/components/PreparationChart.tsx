import {
  EVENTS,
  actualToChartPoints,
  buildIdealLine,
  buildProjection,
  chartWindow,
  timeFraction,
  monthAxisTicks,
  toSvgPath,
  type DailyActual,
} from "@/lib/preparation";
import { formatDateEsCO } from "@/lib/lastUpdated";

type Props = {
  actual: DailyActual[];
  todayIso: string;
  vo2max?: number | null;
};

const W = 960;
const H = 272;
const PAD = { top: 56, right: 12, bottom: 36, left: 36 };
const PROJECTION_COLOR = "#c084fc";

export function PreparationChart({ actual, todayIso, vo2max }: Props) {
  const { chartStart, chartEnd } = chartWindow(todayIso);
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const scaleX = (x: number) => PAD.left + x * plotW;
  const scaleY = (y: number) => PAD.top + plotH - (y / 100) * plotH;

  const actualPoints = actualToChartPoints(actual, chartStart, chartEnd);
  const actualPath = toSvgPath(actualPoints, scaleX, scaleY);

  const { forecast, atEvents, slopePerDay } = buildProjection(
    actual,
    chartStart,
    chartEnd,
    todayIso,
    vo2max
  );
  const projectionPath = toSvgPath(forecast, scaleX, scaleY);

  const ideals = EVENTS.map((ev) => ({
    ev,
    path: toSvgPath(buildIdealLine(ev, chartStart, chartEnd), scaleX, scaleY),
  }));

  const todayX = scaleX(timeFraction(todayIso, chartStart, chartEnd));
  const monthTicks = monthAxisTicks(chartStart, chartEnd);
  const eventLabelY = [PAD.top - 8, PAD.top - 20, PAD.top - 32, PAD.top - 44];

  const slopeLabel =
    slopePerDay >= 0
      ? `+${(slopePerDay * 7).toFixed(2)} pts/semana`
      : `${(slopePerDay * 7).toFixed(2)} pts/semana`;

  return (
    <div className="prep-chart-wrap">
      <p className="muted chart-caption">
        Índice 0–100 (readiness, carga, VO₂/edad, sueño/HRV/BB).{" "}
        <span style={{ color: "#f1f5f9" }}>Blanca</span> = hoy ·{" "}
        <span style={{ color: PROJECTION_COLOR }}>Lila</span> = si mantienes el ritmo reciente (
        {slopeLabel}, con techo por VO₂). Punteadas = ideal por fase hasta cada reto.
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="prep-chart" role="img" aria-label="Preparación vs retos">
        {[0, 25, 50, 75, 100].map((y) => {
          const yy = scaleY(y);
          return (
            <g key={y}>
              <line x1={PAD.left} y1={yy} x2={W - PAD.right} y2={yy} stroke="#334155" strokeWidth="1" />
              <text x={6} y={yy + 4} fill="#64748b" fontSize="10">
                {y}
              </text>
            </g>
          );
        })}
        <rect
          x={PAD.left}
          y={PAD.top}
          width={plotW}
          height={plotH}
          fill="none"
          stroke="#475569"
          strokeWidth="1"
        />
        {monthTicks.map((tick) => (
          <g key={`${tick.label}-${tick.x}`}>
            <line
              x1={scaleX(tick.x)}
              y1={PAD.top + plotH}
              x2={scaleX(tick.x)}
              y2={PAD.top + plotH + 5}
              stroke="#475569"
              strokeWidth="1"
            />
            <text x={scaleX(tick.x)} y={H - 8} fill="#94a3b8" fontSize="9" textAnchor="middle">
              {tick.label}
            </text>
          </g>
        ))}
        {ideals.map(({ ev, path }) => (
          <path
            key={ev.code}
            d={path}
            fill="none"
            stroke={ev.color}
            strokeWidth="2"
            strokeDasharray="8 5"
            opacity={0.95}
          />
        ))}
        {projectionPath ? (
          <path
            d={projectionPath}
            fill="none"
            stroke={PROJECTION_COLOR}
            strokeWidth="2.5"
            strokeDasharray="2 6"
            strokeLinecap="round"
            opacity={0.95}
          />
        ) : null}
        {actualPath ? (
          <path d={actualPath} fill="none" stroke="#f1f5f9" strokeWidth="3" strokeLinejoin="round" />
        ) : null}
        {actualPoints.map((p) => (
          <circle
            key={p.date}
            cx={scaleX(p.x)}
            cy={scaleY(p.y)}
            r={5}
            fill="#f1f5f9"
            stroke="#0f172a"
            strokeWidth="1.5"
          />
        ))}
        {atEvents.map(({ event, projected }) => {
          const dx = scaleX(timeFraction(event.eventDate, chartStart, chartEnd));
          const dy = scaleY(projected);
          return (
            <g key={`proj-${event.code}`}>
              <circle cx={dx} cy={dy} r={6} fill={PROJECTION_COLOR} stroke="#1e1b4b" strokeWidth="1.5" />
              <text x={dx + 8} y={dy + 4} fill={PROJECTION_COLOR} fontSize="10" fontWeight="600">
                {projected}
              </text>
            </g>
          );
        })}
        {EVENTS.map((ev, idx) => {
          const dx = scaleX(timeFraction(ev.eventDate, chartStart, chartEnd));
          const anchor = dx > W - 80 ? "end" : dx < PAD.left + 48 ? "start" : "middle";
          return (
            <g key={ev.code}>
              <line
                x1={dx}
                y1={PAD.top}
                x2={dx}
                y2={PAD.top + plotH}
                stroke={ev.color}
                strokeWidth="1.5"
                opacity={0.55}
              />
              <text
                x={anchor === "end" ? Math.min(dx, W - 6) : dx}
                y={eventLabelY[idx] ?? PAD.top - 8}
                fill={ev.color}
                fontSize="10"
                fontWeight="600"
                textAnchor={anchor}
              >
                {ev.shortLabel}
              </text>
            </g>
          );
        })}
        <line
          x1={todayX}
          y1={PAD.top}
          x2={todayX}
          y2={PAD.top + plotH}
          stroke="#cbd5e1"
          strokeDasharray="4 4"
          strokeWidth="1.5"
        />
        <text x={todayX + 5} y={PAD.top + 14} fill="#cbd5e1" fontSize="10">
          hoy
        </text>
      </svg>
      <ul className="chart-legend">
        <li>
          <span className="legend-line legend-actual" /> Tu estado (real)
        </li>
        <li>
          <span className="legend-line legend-projection" /> Proyección (ritmo actual)
        </li>
        {EVENTS.map((ev) => (
          <li key={ev.code}>
            <span className="legend-line" style={{ borderColor: ev.color }} /> Ideal {ev.shortLabel}
          </li>
        ))}
      </ul>
      <div className="projection-table-wrap">
        <table className="projection-table">
          <thead>
            <tr>
              <th>Reto</th>
              <th>Fecha</th>
              <th>Proyección</th>
              <th>Ideal reto</th>
              <th>Gap</th>
            </tr>
          </thead>
          <tbody>
            {atEvents.map(({ event, projected, target, gap }) => (
              <tr key={event.code}>
                <td>
                  {event.href ? (
                    <a href={event.href} target="_blank" rel="noreferrer">
                      {event.shortLabel}
                    </a>
                  ) : (
                    event.shortLabel
                  )}
                </td>
                <td>{formatDateEsCO(event.eventDate)}</td>
                <td className="proj-val">{projected}</td>
                <td>{target}</td>
                <td className={gap <= 0 ? "gap-ok" : "gap-warn"}>
                  {gap <= 0 ? `+${Math.abs(gap)}` : `−${gap}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted chart-caption" style={{ marginTop: "0.5rem" }}>
        {formatDateEsCO(chartStart)} → {formatDateEsCO(chartEnd)} · hoy {formatDateEsCO(todayIso)}
      </p>
    </div>
  );
}
