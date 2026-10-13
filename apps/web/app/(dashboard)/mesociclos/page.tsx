import { MesocycleVolumeChart } from "@/components/MesocycleVolumeChart";
import { MESOCYCLE_ANCHOR, mergePlannedExecuted, mondayOf, type WeeklySportRow } from "@/lib/mesocycle";
import { MVP_USER_ID, supabase } from "@/lib/supabase";

export const dynamic = "force-dynamic";
export const revalidate = 0;

async function fetchWeeks(): Promise<WeeklySportRow[]> {
  const today = new Date().toISOString().slice(0, 10);
  const { data, error } = await supabase
    .from("weekly_sport_load")
    .select(
      "week_start, block_index, week_in_block, kind, phase_code, planned_run_min, planned_bike_min, planned_swim_min, planned_walk_min, planned_total_min, executed_run_min, executed_bike_min, executed_swim_min, executed_walk_min, executed_total_min"
    )
    .eq("user_id", MVP_USER_ID)
    .gte("week_start", MESOCYCLE_ANCHOR)
    .lte("week_start", mondayOf(today))
    .order("week_start", { ascending: false })
    .limit(16);

  if (error || !data?.length) {
    const ws = mondayOf(today);
    return [mergePlannedExecuted({ week_start: ws } as WeeklySportRow)];
  }

  return data.map((row) => mergePlannedExecuted(row as WeeklySportRow));
}

export default async function MesociclosPage() {
  const weeks = await fetchWeeks();
  const current = weeks[0];

  return (
    <main>
      <h1>Mesociclos 3+1</h1>
      <p className="muted">
        Volumen planificado por fase macrociclo (3 semanas de carga + 1 de recuperación). Lo ejecutado viene de
        actividades Garmin sincronizadas en el collect diario.
      </p>

      {current ? (
        <section className="card">
          <h2>Semana en curso</h2>
          <p>
            <strong>{current.week_start}</strong> · {current.phase_code} ·{" "}
            {current.kind === "recovery" ? "Semana de recuperación del bloque" : "Semana de carga"}
          </p>
          <div className="metric-row">
            <div>
              <div className="muted">Plan run / bike / swim</div>
              <div>
                {Math.round(current.planned_run_min ?? 0)} / {Math.round(current.planned_bike_min ?? 0)} /{" "}
                {Math.round(current.planned_swim_min ?? 0)} min
              </div>
            </div>
            <div>
              <div className="muted">Garmin run / bike / swim</div>
              <div>
                {Math.round(current.executed_run_min ?? 0)} / {Math.round(current.executed_bike_min ?? 0)} /{" "}
                {Math.round(current.executed_swim_min ?? 0)} min
              </div>
            </div>
          </div>
        </section>
      ) : null}

      <MesocycleVolumeChart weeks={weeks} />
    </main>
  );
}
