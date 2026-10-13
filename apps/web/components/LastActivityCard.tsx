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
        <h2 className="mt-0">Última actividad</h2>
        <p className="muted m-0">
          Sin actividades recientes registradas en el snapshot. Pulsa Actualizar para sincronizar los datos de Garmin.
        </p>
      </section>
    );
  }

  const href = garminActivityUrl(activity.activity_id);
  const subtitle = sportLabel(activity.sport || activity.type_key || activity.type_label);

  return (
    <section className="card">
      <h2 className="mt-0">Última actividad</h2>
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
