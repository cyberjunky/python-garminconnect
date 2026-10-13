const TZ = "America/Bogota";
export const ATHLETE_CITY = "Bogotá";

export function latestTimestamp(...candidates: (string | null | undefined)[]): string | undefined {
  let best: string | undefined;
  let bestMs = -1;
  for (const c of candidates) {
    if (!c) continue;
    const ms = Date.parse(c);
    if (!Number.isNaN(ms) && ms > bestMs) {
      bestMs = ms;
      best = c;
    }
  }
  return best;
}

/** Fecha última actualización: YYYY-MM-dd :: hh:mm:ss :: ciudad */
export function formatLastUpdatedLabel(iso: string | null | undefined, city = ATHLETE_CITY): string {
  if (!iso) return `Fecha última actualización: — :: — :: ${city}`;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return `Fecha última actualización: — :: — :: ${city}`;

  const date = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(d);

  const time = new Intl.DateTimeFormat("en-GB", {
    timeZone: TZ,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(d);

  return `Fecha última actualización: ${date} :: ${time} :: ${city}`;
}

/** Devuelve la fecha YYYY-MM-DD en la zona horaria de Bogotá (UTC-5). */
export function todayBogotaIso(date: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}
