/**
 * Synthetic fixtures for isolated layout-responsive verification (SPEC-002).
 * Contains strictly synthetic, non-personal test data.
 */

export const SYNTHETIC_USER_ID = "00000000-0000-0000-0000-000000000001";

export const SYNTHETIC_READINESS_LATEST = {
  readiness_date: "2026-10-17",
  updated_at: "2026-10-17T12:00:00Z",
  zone: "VERDE",
  score_ok: 4,
  hrv: 62,
  bb_change: 38,
  sleep_h: 7.8,
  sleep_score: 84,
  stress: 22,
  recommendation: "Fixture sintética: sesión aeróbica controlada en Z2 según plan de prueba.",
  thresholds: {
    sleep_h: 7.5,
    sleep_score: 75,
    hrv: 55,
    stress_max: 30,
    bb_change: 30,
  },
};

export const SYNTHETIC_READINESS_HISTORY = Array.from({ length: 14 }, (_, idx) => {
  const day = String(17 - idx).padStart(2, "0");
  const zones = ["VERDE", "VERDE", "AMARILLO", "VERDE", "ROJO"];
  return {
    readiness_date: `2026-10-${day}`,
    zone: zones[idx % zones.length],
    score_ok: idx % 5 === 4 ? 2 : 4,
    hrv: 58 + (idx % 6),
    bb_change: 32 + (idx % 10),
    sleep_h: 7.4 + (idx % 3) * 0.2,
    sleep_score: 80 + (idx % 5),
    stress: 21 + (idx % 6),
    thresholds: SYNTHETIC_READINESS_LATEST.thresholds,
  };
});

export const SYNTHETIC_TRAINING_LOAD = Array.from({ length: 14 }, (_, idx) => {
  const day = String(17 - idx).padStart(2, "0");
  return {
    load_date: `2026-10-${day}`,
    acwr: Number((1.05 + (idx % 4) * 0.04).toFixed(2)),
    vo2max: 52,
    status_phrase: "PRODUCTIVE",
  };
});

export const SYNTHETIC_SNAPSHOT = {
  snapshot_date: "2026-10-17",
  updated_at: "2026-10-17T12:00:00Z",
  payload: {
    date: "2026-10-17",
    macrocycle: {
      code: "F2",
      name: "Construcción Aeróbica (Fixture Sintética)",
      focus: "Resistencia aeróbica Z2 y control de carga semanal sintética",
      hr_cap: 148,
      start: "2026-09-28",
      end: "2026-11-15",
      target_date: "2026-11-29",
    },
    milestones: [
      { code: "M1", days_remaining: 21 },
      { code: "M2", days_remaining: 43 },
    ],
    session: {
      title: "Rodaje Z2 + Técnica (Fixture Sintética)",
      action: "Mantener cadencia estable sin superar techo aeróbico",
      sport: "running",
      duration_min: 55,
      hr_cap: 145,
      guard_flags: [],
      details: [
        "10 min calentamiento progresivo Z1",
        "35 min continuo Z2 controlado",
        "10 min vuelta a la calma y movilidad",
      ],
    },
    training_load: {
      status_phrase: "PRODUCTIVE",
      acwr: 1.08,
      acwr_status: "OPTIMAL",
      vo2max: 52,
    },
    last_activity: {
      activity_id: 9000001,
      name: "Sesión Sintética de Ciclismo Z2",
      sport: "cycling",
      type_key: "road_biking",
      type_label: "Ciclismo de ruta (Fixture)",
      start_time_local: "2026-10-16 07:30:00",
      start_time_gmt: "2026-10-16T12:30:00Z",
      duration_min: 75,
      distance_km: 36.4,
      elevation_gain_m: 310,
      avg_hr: 136,
      max_hr: 151,
      calories: 640,
      training_load: 82,
    },
    readiness: {
      recommendation: SYNTHETIC_READINESS_LATEST.recommendation,
    },
    thresholds: SYNTHETIC_READINESS_LATEST.thresholds,
  },
};

export const SYNTHETIC_WEEKLY_SPORT_LOAD = [
  {
    week_start: "2026-10-12",
    block_index: 2,
    week_in_block: 3,
    kind: "load",
    phase_code: "F2",
    planned_run_min: 180,
    planned_bike_min: 240,
    planned_swim_min: 120,
    planned_walk_min: 0,
    planned_total_min: 540,
    executed_run_min: 145,
    executed_bike_min: 210,
    executed_swim_min: 95,
    executed_walk_min: 0,
    executed_total_min: 450,
  },
  {
    week_start: "2026-10-05",
    block_index: 2,
    week_in_block: 2,
    kind: "load",
    phase_code: "F2",
    planned_run_min: 170,
    planned_bike_min: 225,
    planned_swim_min: 110,
    planned_walk_min: 0,
    planned_total_min: 505,
    executed_run_min: 170,
    executed_bike_min: 230,
    executed_swim_min: 110,
    executed_walk_min: 0,
    executed_total_min: 510,
  },
  {
    week_start: "2026-09-28",
    block_index: 2,
    week_in_block: 1,
    kind: "recovery",
    phase_code: "F2",
    planned_run_min: 120,
    planned_bike_min: 150,
    planned_swim_min: 80,
    planned_walk_min: 0,
    planned_total_min: 350,
    executed_run_min: 118,
    executed_bike_min: 155,
    executed_swim_min: 82,
    executed_walk_min: 0,
    executed_total_min: 355,
  },
];

export const SYNTHETIC_CHATS_STORAGE = [
  {
    id: "layout-synthetic",
    title: "Prueba de interfaz sintética (SPEC-002)",
    updatedAt: "2026-10-17T12:00:00Z",
    messages: [
      {
        role: "user",
        content: "Prueba de interfaz, sin información personal: ¿cómo distribuir la sesión aeróbica sintética de hoy?",
      },
      {
        role: "assistant",
        content:
          "Respuesta sintética de prueba de interfaz: mantén el bloque principal en Z2 durante 35 minutos con hidratación constante y verifica que el compositor permanezca centrado hasta 880px.",
      },
    ],
  },
  {
    id: "layout-synthetic-history-2",
    title: "Consulta sintética de transición T2",
    updatedAt: "2026-10-16T15:30:00Z",
    messages: [
      {
        role: "user",
        content: "Segunda conversación sintética para validar navegación de historial.",
      },
      {
        role: "assistant",
        content: "Respuesta sintética almacenada en fixture local para la segunda conversación.",
      },
    ],
  },
];
