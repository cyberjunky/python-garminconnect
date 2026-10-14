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

/** Formatea una fecha ISO o Date en formato legible con localización es-CO */
export function formatDateEsCO(
  dateInput: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string {
  if (!dateInput) return "—";
  let d: Date;
  if (typeof dateInput === "string") {
    const trimmed = dateInput.trim();
    if (!trimmed) return "—";
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      d = new Date(`${trimmed}T12:00:00Z`);
    } else {
      d = new Date(trimmed);
    }
  } else {
    d = dateInput;
  }
  if (Number.isNaN(d.getTime())) return typeof dateInput === "string" ? dateInput : "—";

  const defaultOptions: Intl.DateTimeFormatOptions = {
    timeZone: TZ,
    day: "numeric",
    month: "short",
    year: "numeric",
    ...options,
  };

  return new Intl.DateTimeFormat("es-CO", defaultOptions).format(d);
}

/** Etiqueta amigable de actualización: "Actualizado hoy a las 11:47" */
export function formatLastUpdatedLabel(
  iso: string | null | undefined,
  baseDate: Date = new Date()
): string {
  if (!iso) return "Sin datos de actualización";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Sin datos de actualización";

  const todayStr = todayBogotaIso(baseDate);
  const targetDateStr = todayBogotaIso(d);

  const timeStr = new Intl.DateTimeFormat("es-CO", {
    timeZone: TZ,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(d);

  if (targetDateStr === todayStr) {
    return `Actualizado hoy a las ${timeStr}`;
  }

  const yesterday = new Date(baseDate.getTime() - 86400000);
  if (targetDateStr === todayBogotaIso(yesterday)) {
    return `Actualizado ayer a las ${timeStr}`;
  }

  const dateStr = formatDateEsCO(d);
  return `Actualizado el ${dateStr} a las ${timeStr}`;
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
