export type ConditionSnapshot = {
  readinessDate: string | null;
  updatedAt: string | null;
  stale: boolean;
  zone: string | null;
  scoreOk: number | null;
  sleepH: number | null;
  sleepScore: number | null;
  hrv: number | null;
  stress: number | null;
  bbChange: number | null;
  recommendation: string | null;
  acwr: number | null;
  vo2max: number | null;
  statusPhrase: string | null;
  index: number | null;
  sessionTitle: string | null;
  phaseCode: string | null;
  phaseName: string | null;
};

export const STALE_MS = 18 * 60 * 60 * 1000;

export function conditionPrompt(snapshot: ConditionSnapshot): string {
  const lines = [
    "Eres el coach de Diego. Respondes en español, breve y concreto.",
    "Man-in-the-loop: propones la sesión, no la impones. Si readiness es ROJO, prioriza descanso.",
    "Usa solo los números de este contexto. Si falta un dato, dilo. No inventes métricas de Garmin.",
    snapshot.stale
      ? "Los datos tienen más de 18 horas. Dilo y sugiere pulsar Actualizar antes de decidir el entreno."
      : "Los datos están dentro de las últimas 18 horas.",
    `Fecha readiness: ${snapshot.readinessDate ?? "sin dato"}`,
    `Actualizado: ${snapshot.updatedAt ?? "sin dato"}`,
    `Zona: ${snapshot.zone ?? "—"} (${snapshot.scoreOk ?? "?"}/5)`,
    `Índice de preparación 0-100: ${snapshot.index ?? "—"}`,
    `Sueño: ${snapshot.sleepH ?? "—"} h, score ${snapshot.sleepScore ?? "—"}`,
    `HRV: ${snapshot.hrv ?? "—"} ms`,
    `Estrés: ${snapshot.stress ?? "—"}`,
    `Body Battery delta: ${snapshot.bbChange ?? "—"}`,
    `ACWR: ${snapshot.acwr ?? "—"}`,
    `Estado Garmin: ${snapshot.statusPhrase ?? "—"}`,
    `VO2max: ${snapshot.vo2max ?? "—"}`,
    `Fase: ${snapshot.phaseCode ?? "—"} ${snapshot.phaseName ?? ""}`.trim(),
    `Sesión planificada: ${snapshot.sessionTitle ?? "—"}`,
    `Recomendación del motor: ${snapshot.recommendation ?? "—"}`,
  ];
  return lines.join("\n");
}
