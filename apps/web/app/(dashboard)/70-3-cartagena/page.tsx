import { CARTAGENA703_EVENT, CARTAGENA703_LEGS } from "@/lib/cartagena703";

export const dynamic = "force-static";

const SPORT_COLOR: Record<string, string> = {
  swim: "#06b6d4",
  bike: "#3b82f6",
  run: "#22c55e",
};

export default function Cartagena703Page() {
  return (
    <main>
      <h1>70.3 Cartagena — recorridos</h1>
      <p className="muted">
        Referencia de distancias y notas de carrera para {CARTAGENA703_EVENT.name} ({CARTAGENA703_EVENT.date}).
        Mapas oficiales pueden cambiar; confirma en el athlete guide.
      </p>

      <section className="card">
        <h2>Resumen</h2>
        <p>
          <strong>{CARTAGENA703_EVENT.totalKm} km</strong> totales (70.3 estándar): 1,9 km + 90 km + 21,1 km.
        </p>
        <p className="muted">
          <a href={CARTAGENA703_EVENT.officialCourseUrl} target="_blank" rel="noreferrer">
            Course overview (IRONMAN)
          </a>
          {" · "}
          <a href={CARTAGENA703_EVENT.officialRaceUrl} target="_blank" rel="noreferrer">
            Página del evento
          </a>
        </p>
      </section>

      {CARTAGENA703_LEGS.map((leg) => (
        <section key={leg.sport} className="card course-leg">
          <div className="course-leg-head">
            <span className="course-dot" style={{ background: SPORT_COLOR[leg.sport] }} />
            <h2>
              {leg.label} · {leg.distance}
            </h2>
          </div>
          <p className="muted">{leg.elevationNote}</p>
          <h3>Recorrido</h3>
          <ul>
            {leg.courseNotes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
          <h3>Clima / estrategia</h3>
          <ul>
            {leg.envNotes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}
