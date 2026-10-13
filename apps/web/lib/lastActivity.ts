export type LastActivity = {
  activity_id: number;
  name: string;
  sport: string;
  type_key?: string | null;
  type_label?: string | null;
  start_time_local?: string | null;
  start_time_gmt?: string | null;
  duration_min?: number | null;
  distance_km?: number | null;
  elevation_gain_m?: number | null;
  avg_hr?: number | null;
  max_hr?: number | null;
  calories?: number | null;
  training_load?: number | null;
};

const SPORT_LABEL: Record<string, string> = {
  run: "Carrera",
  bike: "Ciclismo",
  swim: "Natación",
  walk: "Caminata",
  multisport: "Multideporte",
  other: "Otro",
};

export function sportLabel(sport: string): string {
  return SPORT_LABEL[sport] ?? sport;
}

export function garminActivityUrl(activityId: number): string {
  return `https://connect.garmin.com/modern/activity/${activityId}`;
}

export function formatActivityWhen(startTimeLocal?: string | null): string {
  if (!startTimeLocal) return "—";
  const normalized = startTimeLocal.includes("T")
    ? startTimeLocal
    : startTimeLocal.replace(" ", "T");
  const d = new Date(normalized);
  if (Number.isNaN(d.getTime())) return startTimeLocal;
  return d.toLocaleString("es-CO", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Bogota",
  });
}

export function formatDurationMin(minutes?: number | null): string {
  if (minutes == null || minutes <= 0) return "—";
  const total = Math.round(minutes);
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h <= 0) return `${m} min`;
  return `${h} h ${m} min`;
}

export function formatDistanceKm(km?: number | null): string {
  if (km == null || km <= 0) return "—";
  return `${km.toFixed(km >= 10 ? 1 : 2)} km`;
}
