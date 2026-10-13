import {
  formatActivityWhen,
  formatDistanceKm,
  formatDurationMin,
  garminActivityUrl,
  sportLabel,
  type LastActivity,
} from "@/lib/lastActivity";

type Props = {
  activity: LastActivity | null | undefined;
};

export function LastActivityCard({ activity }: Props) {
  if (!activity) {
    return (
      <section className="card">
        <h2 style={{ marginTop: 0 }}>Última actividad</h2>
        <p className="muted" style={{ margin: 0 }}>
          Sin datos en el snapshot. Pulsa Actualizar y espera a que termine el collect en GitHub (1–2 min).
          Si sigue vacío, el workflow debe correr código reciente en la rama configurada en{" "}
          <code>ACTIONS_DISPATCH_REF</code> (por defecto <code>master</code>).
        </p>
      </section>
    );
  }

  const href = garminActivityUrl(activity.activity_id);
  const subtitle = activity.type_label || sportLabel(activity.sport);

  return (
    <section className="card">
      <h2 style={{ marginTop: 0 }}>Última actividad</h2>
      <p className="last-activity-title">
        <a href={href} target="_blank" rel="noreferrer">
          {activity.name}
        </a>
      </p>
      <p className="muted last-activity-meta">
        {subtitle} · {formatActivityWhen(activity.start_time_local)}
      </p>
      <div className="metrics-grid last-activity-metrics">
        <div className="metric-cell na">
          <span className="metric-label">Duración</span>
          <span className="metric-value">{formatDurationMin(activity.duration_min)}</span>
        </div>
        <div className="metric-cell na">
          <span className="metric-label">Distancia</span>
          <span className="metric-value">{formatDistanceKm(activity.distance_km)}</span>
        </div>
        <div className="metric-cell na">
          <span className="metric-label">FC media</span>
          <span className="metric-value">
            {activity.avg_hr != null ? `${activity.avg_hr} bpm` : "—"}
          </span>
        </div>
        <div className="metric-cell na">
          <span className="metric-label">Carga</span>
          <span className="metric-value">
            {activity.training_load != null ? activity.training_load.toFixed(0) : "—"}
          </span>
        </div>
      </div>
      {(activity.elevation_gain_m != null && activity.elevation_gain_m > 0) ||
      activity.calories != null ? (
        <p className="load-line">
          {activity.elevation_gain_m != null && activity.elevation_gain_m > 0
            ? `+${Math.round(activity.elevation_gain_m)} m desnivel`
            : null}
          {activity.elevation_gain_m != null &&
          activity.elevation_gain_m > 0 &&
          activity.calories != null
            ? " · "
            : null}
          {activity.calories != null ? `${activity.calories} kcal` : null}
        </p>
      ) : null}
    </section>
  );
}
