import { MVP_USER_ID, supabase } from "@/lib/infra/supabase";
import { formatDateEsCO } from "./lastUpdated";

export type MonthlyTrendRow = {
  date: string; // YYYY-MM-DD
  dateFormatted: string; // Formato es-CO: "17 oct 2026"
  zone: "VERDE" | "AMARILLO" | "ROJO" | string;
  scoreOk: number | null;
  hrv: number | null;
  sleepHours: number | null;
  sleepScore: number | null;
  stress: number | null;
  bbChange: number | null;
  acwr: number | null;
  vo2max: number | null;
};

export type MonthlyZoneDistribution = {
  totalDays: number;
  counts: { VERDE: number; AMARILLO: number; ROJO: number };
  percentages: { VERDE: number; AMARILLO: number; ROJO: number };
};

export type MetricSummaryItem = {
  label: string;
  averageValue: number | null;
  unit: string;
  target?: string;
  statusLabel: string;
};

export type MonthlySummary = {
  totalEvaluatedDays: number;
  zoneCompliancePct: number; // % de días en VERDE
  hrv: MetricSummaryItem;
  sleepHours: MetricSummaryItem;
  sleepScore: MetricSummaryItem;
  bodyBatteryChange: MetricSummaryItem;
  stress: MetricSummaryItem;
  acwr: MetricSummaryItem;
  vo2max: MetricSummaryItem;
};

type ReadinessDailyDbRow = {
  readiness_date: string;
  zone: string;
  score_ok: number | null;
  hrv: number | null;
  bb_change: number | null;
  sleep_h: number | null;
  sleep_score: number | null;
  stress: number | null;
  thresholds: Record<string, number> | null;
};

type TrainingLoadDbRow = {
  load_date: string;
  acwr: number | null;
  vo2max: number | null;
  status_phrase: string | null;
};

/**
 * Calcula la distribución porcentual y conteo de zonas (VERDE, AMARILLO, ROJO).
 * Función pura sin dependencias de I/O.
 */
export function calculateMonthlyZoneDistribution(
  rows: Array<{ zone: string }>
): MonthlyZoneDistribution {
  const counts = { VERDE: 0, AMARILLO: 0, ROJO: 0 };
  const totalDays = rows.length;

  for (const row of rows) {
    const normalized = (row.zone || "").trim().toUpperCase();
    if (normalized === "VERDE") {
      counts.VERDE += 1;
    } else if (normalized === "AMARILLO") {
      counts.AMARILLO += 1;
    } else if (normalized === "ROJO") {
      counts.ROJO += 1;
    }
  }

  const calcPct = (count: number): number => {
    if (totalDays === 0) return 0;
    return Math.round((count / totalDays) * 100);
  };

  return {
    totalDays,
    counts,
    percentages: {
      VERDE: calcPct(counts.VERDE),
      AMARILLO: calcPct(counts.AMARILLO),
      ROJO: calcPct(counts.ROJO),
    },
  };
}

function computeAverage(values: (number | null | undefined)[], decimals = 1): number | null {
  const valid = values.filter((v): v is number => typeof v === "number" && !Number.isNaN(v));
  if (valid.length === 0) return null;
  const sum = valid.reduce((acc, curr) => acc + curr, 0);
  const factor = Math.pow(10, decimals);
  return Math.round((sum / valid.length) * factor) / factor;
}

/**
 * Consolida las métricas fisiológicas de 30 días, promediando valores válidos
 * y comparándolos contra umbrales de ciencia deportiva.
 * Función pura sin dependencias de I/O.
 */
export function calculateMonthlySummary(
  rows: MonthlyTrendRow[],
  thresholds?: Record<string, number>
): MonthlySummary {
  const totalEvaluatedDays = rows.length;
  const th = thresholds || {};
  const thHrv = th.hrv ?? 48;
  const thSleepH = th.sleep_h ?? 7.0;
  const thSleepScore = th.sleep_score ?? 75;
  const thBbChange = th.bb_change ?? 30;
  const thStressMax = th.stress_max ?? 35;

  const distribution = calculateMonthlyZoneDistribution(rows);
  const zoneCompliancePct = distribution.percentages.VERDE;

  const avgHrv = computeAverage(
    rows.map((r) => r.hrv),
    1
  );
  const avgSleepHours = computeAverage(
    rows.map((r) => r.sleepHours),
    1
  );
  const avgSleepScore = computeAverage(
    rows.map((r) => r.sleepScore),
    1
  );
  const avgBbChange = computeAverage(
    rows.map((r) => r.bbChange),
    1
  );
  const avgStress = computeAverage(
    rows.map((r) => r.stress),
    1
  );
  const avgAcwr = computeAverage(
    rows.map((r) => r.acwr),
    2
  );
  const avgVo2max = computeAverage(
    rows.map((r) => r.vo2max),
    1
  );

  return {
    totalEvaluatedDays,
    zoneCompliancePct,
    hrv: {
      label: "HRV promedio",
      averageValue: avgHrv,
      unit: "ms",
      target: `≥ ${thHrv} ms`,
      statusLabel:
        avgHrv === null
          ? "Sin datos"
          : avgHrv >= thHrv
            ? "En rango óptimo"
            : "Tono vagal deprimido",
    },
    sleepHours: {
      label: "Sueño promedio",
      averageValue: avgSleepHours,
      unit: "h",
      target: `≥ ${thSleepH.toFixed(1)} h`,
      statusLabel:
        avgSleepHours === null
          ? "Sin datos"
          : avgSleepHours >= thSleepH
            ? "En meta"
            : "Déficit acumulado",
    },
    sleepScore: {
      label: "Puntuación de sueño",
      averageValue: avgSleepScore,
      unit: "pts",
      target: `≥ ${thSleepScore}`,
      statusLabel:
        avgSleepScore === null
          ? "Sin datos"
          : avgSleepScore >= thSleepScore
            ? "Recuperación alta"
            : "Recuperación baja",
    },
    bodyBatteryChange: {
      label: "Recarga Body Battery",
      averageValue: avgBbChange,
      unit: "pts",
      target: `≥ +${thBbChange}`,
      statusLabel:
        avgBbChange === null
          ? "Sin datos"
          : avgBbChange >= thBbChange
            ? "Recarga óptima"
            : "Recarga insuficiente",
    },
    stress: {
      label: "Estrés promedio",
      averageValue: avgStress,
      unit: "pts",
      target: `≤ ${thStressMax}`,
      statusLabel:
        avgStress === null
          ? "Sin datos"
          : avgStress <= thStressMax
            ? "Bajo control"
            : "Estrés elevado",
    },
    acwr: {
      label: "Carga aguda:crónica (ACWR)",
      averageValue: avgAcwr,
      unit: "",
      target: "< 1.3 (Gabbett)",
      statusLabel:
        avgAcwr === null
          ? "Sin datos"
          : avgAcwr <= 1.3
            ? "Rango seguro"
            : "Sobrecarga / riesgo alto",
    },
    vo2max: {
      label: "VO₂max",
      averageValue: avgVo2max,
      unit: "ml/kg/min",
      target: "≥ 50",
      statusLabel: avgVo2max === null ? "Sin datos" : "Base conservada",
    },
  };
}

/**
 * Adaptador de infraestructura para obtener los últimos 30 días de métricas fisiológicas
 * desde Supabase y construir el resumen y distribución de zonas mensual.
 */
export async function fetchMonthlyTrend(
  userId: string = MVP_USER_ID
): Promise<{
  rows: MonthlyTrendRow[];
  distribution: MonthlyZoneDistribution;
  summary: MonthlySummary;
  error?: string | null;
}> {
  try {
    const [readinessRes, loadRes] = await Promise.all([
      supabase
        .from("readiness_daily")
        .select(
          "readiness_date, zone, score_ok, hrv, bb_change, sleep_h, sleep_score, stress, thresholds"
        )
        .eq("user_id", userId)
        .order("readiness_date", { ascending: false })
        .limit(30),
      supabase
        .from("training_load")
        .select("load_date, acwr, vo2max, status_phrase")
        .eq("user_id", userId)
        .order("load_date", { ascending: false })
        .limit(60),
    ]);

    if (readinessRes.error) {
      const emptyDist = calculateMonthlyZoneDistribution([]);
      const emptySummary = calculateMonthlySummary([]);
      return {
        rows: [],
        distribution: emptyDist,
        summary: emptySummary,
        error: readinessRes.error.message,
      };
    }

    const loadByDate = new Map<string, TrainingLoadDbRow>();
    for (const loadRow of (loadRes.data || []) as TrainingLoadDbRow[]) {
      loadByDate.set(loadRow.load_date, loadRow);
    }

    const readinessRows = (readinessRes.data || []) as ReadinessDailyDbRow[];

    const rows: MonthlyTrendRow[] = readinessRows.map((r) => {
      const load = loadByDate.get(r.readiness_date);
      return {
        date: r.readiness_date,
        dateFormatted: formatDateEsCO(r.readiness_date),
        zone: r.zone,
        scoreOk: r.score_ok,
        hrv: r.hrv,
        sleepHours: r.sleep_h,
        sleepScore: r.sleep_score,
        stress: r.stress,
        bbChange: r.bb_change,
        acwr: load?.acwr ?? null,
        vo2max: load?.vo2max ?? null,
      };
    });

    const latestThresholds = readinessRows[0]?.thresholds || undefined;
    const distribution = calculateMonthlyZoneDistribution(rows);
    const summary = calculateMonthlySummary(rows, latestThresholds);

    return {
      rows,
      distribution,
      summary,
      error: null,
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Error desconocido consultando tendencias";
    const emptyDist = calculateMonthlyZoneDistribution([]);
    const emptySummary = calculateMonthlySummary([]);
    return {
      rows: [],
      distribution: emptyDist,
      summary: emptySummary,
      error: message,
    };
  }
}
