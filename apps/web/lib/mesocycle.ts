/** Client-side mesocycle plan (mirrors garmin_coaching/mesocycle.py). */

export const MESOCYCLE_ANCHOR = "2026-09-21";

const PHASE_WEEKLY_BASE: Record<string, Record<string, number>> = {
  R0: { run: 60, bike: 30, swim: 0, walk: 120 },
  R1: { run: 200, bike: 150, swim: 0, walk: 45 },
  R2: { run: 280, bike: 60, swim: 0, walk: 30 },
  R3: { run: 320, bike: 40, swim: 0, walk: 30 },
  R4: { run: 180, bike: 0, swim: 0, walk: 60 },
  R5: { run: 90, bike: 280, swim: 0, walk: 30 },
  R6: { run: 60, bike: 320, swim: 0, walk: 30 },
  R7: { run: 150, bike: 200, swim: 120, walk: 30 },
};

const PHASES: { code: string; start: string; end: string; name: string }[] = [
  { code: "R0", start: "2026-09-20", end: "2026-10-05", name: "Recuperacion" },
  { code: "R1", start: "2026-10-06", end: "2026-12-31", name: "Base aerobica" },
  { code: "R2", start: "2027-01-01", end: "2027-03-31", name: "Construccion" },
  { code: "R3", start: "2027-04-01", end: "2027-07-24", name: "Especifico 21K" },
  { code: "R4", start: "2027-07-25", end: "2027-07-25", name: "Carrera mmB" },
  { code: "R5", start: "2027-08-01", end: "2027-08-31", name: "Transicion ciclismo" },
  { code: "R6", start: "2027-09-01", end: "2027-09-13", name: "Reto Letras" },
  { code: "R7", start: "2027-10-01", end: "2027-11-28", name: "Especifico 70.3" },
];

const LOAD_WEEK_SCALE = [0.85, 1.0, 1.1];
const RECOVERY_WEEK_SCALE = 0.65;

export function mondayOf(isoDate: string): string {
  const d = new Date(isoDate + "T12:00:00");
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  return d.toISOString().slice(0, 10);
}

function activePhaseCode(isoDate: string): string {
  for (const p of PHASES) {
    if (isoDate >= p.start && isoDate <= p.end) return p.code;
  }
  if (isoDate < PHASES[0].start) return PHASES[0].code;
  return PHASES[PHASES.length - 1].code;
}

export function weekMeta(weekStart: string) {
  const ws = mondayOf(weekStart);
  const anchor = new Date(MESOCYCLE_ANCHOR + "T12:00:00");
  const cur = new Date(ws + "T12:00:00");
  const days = Math.floor((cur.getTime() - anchor.getTime()) / 86400000);
  let blockIndex = 0;
  let weekInBlock = 0;
  if (days >= 0) {
    const weekIndex = Math.floor(days / 7);
    blockIndex = Math.floor(weekIndex / 4);
    weekInBlock = weekIndex % 4;
  }
  const kind = weekInBlock === 3 ? "recovery" : "load";
  return { week_start: ws, block_index: blockIndex, week_in_block: weekInBlock, kind, phase_code: activePhaseCode(ws) };
}

export function plannedWeeklySports(weekStart: string) {
  const meta = weekMeta(weekStart);
  const base = { ...(PHASE_WEEKLY_BASE[meta.phase_code] ?? PHASE_WEEKLY_BASE.R0) };
  const scale = meta.week_in_block === 3 ? RECOVERY_WEEK_SCALE : LOAD_WEEK_SCALE[meta.week_in_block];
  return {
    run: Math.round(base.run * scale * 10) / 10,
    bike: Math.round(base.bike * scale * 10) / 10,
    swim: Math.round(base.swim * scale * 10) / 10,
    walk: Math.round(base.walk * scale * 10) / 10,
  };
}

export type WeeklySportRow = {
  week_start: string;
  block_index: number | null;
  week_in_block: number | null;
  kind: string | null;
  phase_code: string | null;
  planned_run_min: number | null;
  planned_bike_min: number | null;
  planned_swim_min: number | null;
  planned_walk_min: number | null;
  planned_total_min: number | null;
  executed_run_min: number | null;
  executed_bike_min: number | null;
  executed_swim_min: number | null;
  executed_walk_min: number | null;
  executed_total_min: number | null;
};

export function mergePlannedExecuted(row: WeeklySportRow): WeeklySportRow {
  const planned = plannedWeeklySports(row.week_start);
  const plannedTotal = planned.run + planned.bike + planned.swim + planned.walk;
  const meta = weekMeta(row.week_start);
  return {
    ...row,
    ...meta,
    planned_run_min: row.planned_run_min ?? planned.run,
    planned_bike_min: row.planned_bike_min ?? planned.bike,
    planned_swim_min: row.planned_swim_min ?? planned.swim,
    planned_walk_min: row.planned_walk_min ?? planned.walk,
    planned_total_min: row.planned_total_min ?? plannedTotal,
    executed_run_min: row.executed_run_min ?? 0,
    executed_bike_min: row.executed_bike_min ?? 0,
    executed_swim_min: row.executed_swim_min ?? 0,
    executed_walk_min: row.executed_walk_min ?? 0,
    executed_total_min: row.executed_total_min ?? 0,
  };
}

/* =========================================================================
   Macrociclo en 4 bloques (SPEC-003, REQ-007..011)
   ========================================================================= */

export type MacrocycleBlockData = {
  definition: {
    title: string;
    text: string;
  };
  currentPhase: {
    code: string;
    name: string;
    focus: string;
    sport: string;
    hrCap: number;
    maxDurationMin: number;
    startDate: string;
    endDate: string;
  };
  howToImprove: {
    title: string;
    recommendation: string;
  };
  timing: {
    phaseEndDateFormatted: string;
    daysRemainingPhase: number;
    milestones: Array<{
      code: string;
      name: string;
      eventDateFormatted: string;
      daysRemaining: number;
    }>;
  };
};

export type MacrocyclePhase = {
  code: string;
  name: string;
  start: string;
  end: string;
  focus: string;
  sport: string;
  hrCap: number;
  maxDurationMin: number;
};

export const MACROCYCLE_DEFINITION = {
  title: "Definición y propósito",
  text: "El macrociclo es la estructura estratégica de periodización plurianual que organiza la temporada hacia los objetivos mayores (Media Maratón Bogotá 2027, Reto Letras 2027 e Ironman 70.3 Cartagena 2027). Divide el año en fases sucesivas de adaptación fisiológica —desde la base mitocondrial y volumen controlado hasta la potencia y el pico de rendimiento— para maximizar adaptaciones aeróbicas y prevenir sobrecargas.",
};

export const PHASES_CATALOG: MacrocyclePhase[] = [
  { code: "R0", name: "Recuperación", start: "2026-09-20", end: "2026-10-05", focus: "ACWR < 1.0", sport: "walk/off", hrCap: 128, maxDurationMin: 45 },
  { code: "R1", name: "Base aeróbica", start: "2026-10-06", end: "2026-12-31", focus: "80/20 Z1-Z2", sport: "run+bike", hrCap: 135, maxDurationMin: 75 },
  { code: "R2", name: "Construcción", start: "2027-01-01", end: "2027-03-31", focus: "Volumen + 1 tempo/sem", sport: "run", hrCap: 141, maxDurationMin: 90 },
  { code: "R3", name: "Específico 21K", start: "2027-04-01", end: "2027-07-24", focus: "Long run + ritmo mmB", sport: "run", hrCap: 155, maxDurationMin: 120 },
  { code: "R4", name: "Carrera mmB", start: "2027-07-25", end: "2027-07-25", focus: "Taper + carrera", sport: "race", hrCap: 182, maxDurationMin: 150 },
  { code: "R5", name: "Transición ciclismo", start: "2027-08-01", end: "2027-08-31", focus: "Fuerza + bici subida", sport: "bike", hrCap: 141, maxDurationMin: 120 },
  { code: "R6", name: "Reto Letras", start: "2027-09-01", end: "2027-09-13", focus: "Ascenso + taper", sport: "bike", hrCap: 155, maxDurationMin: 180 },
  { code: "R7", name: "Específico 70.3", start: "2027-10-01", end: "2027-11-28", focus: "Brick + volumen tri", sport: "tri", hrCap: 155, maxDurationMin: 180 },
];

export type EventMilestone = {
  code: string;
  name: string;
  eventDate: string;
};

export const MILESTONES_CATALOG: EventMilestone[] = [
  { code: "bogota_21k_2026", name: "vChallenges 21K", eventDate: "2026-12-26" },
  { code: "mmb_2027", name: "Media Maratón Bogotá 2027", eventDate: "2027-07-25" },
  { code: "reto_letras_2027", name: "Reto Mariquita Letras 2027", eventDate: "2027-09-13" },
  { code: "cartagena_703_2027", name: "Ironman 70.3 Cartagena 2027", eventDate: "2027-11-29" },
];

export function daysBetween(fromIso: string, toIso: string): number {
  const [y1, m1, d1] = fromIso.split("-").map(Number);
  const [y2, m2, d2] = toIso.split("-").map(Number);
  const utc1 = Date.UTC(y1, m1 - 1, d1);
  const utc2 = Date.UTC(y2, m2 - 1, d2);
  return Math.round((utc2 - utc1) / (1000 * 60 * 60 * 24));
}

export function formatPhaseDateEsCO(isoDate: string): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  const date = new Date(Date.UTC(y, m - 1, d, 12, 0, 0));
  return new Intl.DateTimeFormat("es-CO", {
    timeZone: "America/Bogota",
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

export function getMacrocycleDetails(
  onDateIso: string,
  payloadMacrocycle?: {
    code?: string;
    name?: string;
    focus?: string;
    hr_cap?: number;
    start?: string;
    end?: string;
    target_date?: string;
  },
  milestones?: { code: string; days_remaining: number }[],
  readinessZone?: string,
  acwr?: number | null
): MacrocycleBlockData {
  let phase = PHASES_CATALOG.find((p) => onDateIso >= p.start && onDateIso <= p.end);
  if (!phase) {
    if (onDateIso < PHASES_CATALOG[0].start) phase = PHASES_CATALOG[0];
    else phase = PHASES_CATALOG[PHASES_CATALOG.length - 1];
  }

  const code = payloadMacrocycle?.code || phase.code;
  const name = payloadMacrocycle?.name || phase.name;
  const focus = payloadMacrocycle?.focus || phase.focus;
  const hrCap = payloadMacrocycle?.hr_cap ?? phase.hrCap;
  const sport = phase.sport;
  const maxDurationMin = phase.maxDurationMin;
  const startDate = payloadMacrocycle?.start || phase.start;
  const endDate = payloadMacrocycle?.end || phase.end;

  const isFatigued =
    readinessZone === "ROJO" || readinessZone === "AMARILLO" || (acwr != null && acwr > 1.3);

  let recommendationTitle: string;
  let recommendationText: string;

  if (isFatigued) {
    recommendationTitle = "Optimización práctica ante fatiga acumulada";
    recommendationText =
      "Estado de fatiga o carga elevada detectada. Prioriza asimilar el trabajo previo: realiza rodajes regenerativos o recuperación activa en Z1 manteniendo la frecuencia cardíaca muy por debajo del techo, o toma descanso total si el estrés es agudo, antes de retomar el volumen programado.";
  } else {
    recommendationTitle = `Pauta de ejecución en ${name.toLowerCase()}`;
    switch (code) {
      case "R0":
        recommendationText =
          "Enfócate en caminatas ligeras o descanso activo. Mantén el ratio ACWR < 1.0 y la frecuencia cardíaca bajo 128 bpm para restaurar los depósitos energéticos y el sistema neuromuscular.";
        break;
      case "R1":
        recommendationText =
          "Disciplina estricta en Z1-Z2: mantén la frecuencia cardíaca siempre por debajo de 135 bpm para maximizar la biogénesis mitocondrial y la eficiencia aeróbica sin acumular lactato. Prioriza el volumen suave continuo sobre la velocidad.";
        break;
      case "R2":
        recommendationText =
          "Consolida el volumen aeróbico incorporando una sesión de tempo semanal sin rebasar 141 bpm. Asegura una cadencia eficiente de carrera y respeta los días de descarga entre estímulos de calidad.";
        break;
      case "R3":
        recommendationText =
          "Enfócate en tiradas largas progresivas y bloques a ritmo específico de Media Maratón Bogotá con techo en 155 bpm. Entrena la nutrición e hidratación en ruta tal como en competencia.";
        break;
      case "R4":
        recommendationText =
          "Semana de taper y afinamiento competitivo: mantén la activación con toques cortos de ritmo, descansa intensamente y ejecuta la estrategia de ritmo conservador en los primeros 10 km.";
        break;
      case "R5":
        recommendationText =
          "Traslada la carga principal a la bicicleta con énfasis en cadencia en subida y fuerza submáxima bajo 141 bpm. Permite que las piernas se adapten a la exigencia neuromuscular del pedaleo en pendiente.";
        break;
      case "R6":
        recommendationText =
          "Simulaciones de ascenso prolongado y gestión pacing en pendientes sostenidas con techo en 155 bpm. Practica ingesta constante de carbohidratos (60-90 g/h) y taper final pre-evento.";
        break;
      case "R7":
        recommendationText =
          "Sesiones combinadas (brick) de bici y carrera con techo de 155 bpm. Optimiza la posición aerodinámica, las transiciones T1/T2 y el plan nutricional para la temperatura y humedad de Cartagena.";
        break;
      default:
        recommendationText =
          "Respeta los techos de frecuencia cardíaca y volumen estipulados para la fase activa, asegurando una recuperación adecuada entre sesiones exigentes.";
    }
  }

  const daysRemainingPhase = daysBetween(onDateIso, endDate);
  const phaseEndDateFormatted = formatPhaseDateEsCO(endDate);

  const calculatedMilestones = MILESTONES_CATALOG.map((m) => {
    const payloadMs = (milestones || []).find((pms) => pms.code === m.code);
    const calculatedDays = daysBetween(onDateIso, m.eventDate);
    return {
      code: m.code,
      name: m.name,
      eventDateFormatted: formatPhaseDateEsCO(m.eventDate),
      daysRemaining: payloadMs ? payloadMs.days_remaining : calculatedDays,
    };
  });

  return {
    definition: MACROCYCLE_DEFINITION,
    currentPhase: {
      code,
      name,
      focus,
      sport,
      hrCap,
      maxDurationMin,
      startDate,
      endDate,
    },
    howToImprove: {
      title: recommendationTitle,
      recommendation: recommendationText,
    },
    timing: {
      phaseEndDateFormatted,
      daysRemainingPhase,
      milestones: calculatedMilestones,
    },
  };
}
