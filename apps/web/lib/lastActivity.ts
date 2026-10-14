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
  running: "Carrera",
  trail_running: "Trail running",
  treadmill_running: "Cinta",
  bike: "Ciclismo",
  cycling: "Ciclismo",
  road_biking: "Ciclismo de ruta",
  indoor_cycling: "Ciclismo indoor",
  gravel_cycling: "Ciclismo gravel",
  mountain_biking: "Ciclismo de montaña",
  swim: "Natación",
  swimming: "Natación",
  lap_swimming: "Natación en piscina",
  open_water_swimming: "Natación en aguas abiertas",
  walk: "Caminata",
  walking: "Caminata",
  hiking: "Senderismo",
  strength_training: "Entrenamiento de fuerza",
  multisport: "Multideporte",
  triathlon: "Triatlón",
  cardio: "Cardio",
  yoga: "Yoga",
  other: "Otro",
};

export function sportLabel(sport?: string | null): string {
  if (!sport) return "Actividad";
  const key = sport.trim().toLowerCase().replace(/[\s-]+/g, "_");
  return SPORT_LABEL[key] ?? sport;
}

export const GARMIN_STATUS_MAP: Record<string, string> = {
  MAINTAINING: "Mantenimiento",
  PRODUCTIVE: "Productivo",
  RECOVERY: "Recuperación",
  UNPRODUCTIVE: "No productivo",
  OVERREACHING: "Sobreesfuerzo",
  DETRAINING: "Desentrenamiento",
  PEAKING: "Pico de forma",
  NO_STATUS: "Sin estado",
};

export function formatGarminStatus(status?: string | null): string {
  if (!status) return "—";
  const upper = status.trim().toUpperCase();
  return GARMIN_STATUS_MAP[upper] ?? status;
}

export function garminActivityUrl(activityId: number): string {
  return `https://connect.garmin.com/modern/activity/${activityId}`;
}

export function formatActivityWhen(startTimeLocal?: string | null): string {
  if (!startTimeLocal) return "—";
  const normalized = startTimeLocal.includes("T")
    ? startTimeLocal
    : startTimeLocal.replace(" ", "T");
  const hasTimezone = /[Zz]|[+-]\d{2}(:?\d{2})?$/.test(normalized);
  const isoUtc = hasTimezone ? normalized : `${normalized}Z`;
  const d = new Date(isoUtc);
  if (Number.isNaN(d.getTime())) return startTimeLocal;
  return d.toLocaleString("es-CO", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
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
