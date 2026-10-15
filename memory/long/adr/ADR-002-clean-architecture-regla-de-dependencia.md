# ADR-002: Clean Architecture (regla de dependencia) en lugar de `layered`; presentacion sin MVVM

- Estado: propuesto (pendiente de decision humana en `memory/mid/decisions.md`)
- Fecha: 2026-10-15
- Relacionado: ADR-018 del framework; ADR-001 (layered en apps/web frente a MVVM); constitucion Articulo VII

## Contexto

ADR-018 retira `layered` de los valores admitidos: era un nombre sin
principio comprobable. El Articulo VII.2 fija ahora la regla de dependencia y
el VII.3 deja MVVM como patron de presentacion obligatorio con UI salvo ADR.
`ies constitution check` reporta VII-04 (`layered` retirado).

Prueba del Articulo VII.2: el proyecto despliega `apps/web` (Tri-Coach,
Vercel) y `services/collector` (FastAPI, Railway) e instala la libreria
`garminconnect`. Aplica.

Estado del codigo: `garmin_coaching/` (readiness, macrocycle, mesocycle,
session_planner, guards, messages) importa solo stdlib y a si mismo: ya es un
dominio puro. `services/collector/main.py` orquesta `garmin_auth`,
`garmin_coaching` y `supabase_client`. En `apps/web`, `lib/` mezcla calculos
(preparation, condition, dashboard, mesocycle) con clientes (`supabase.ts`,
`openaiModels.ts`); `app/` y `components/` son Server y Client Components.

## Decision

1. `patron_arquitectonico: clean-architecture`, `tiene_ui: si`,
   `patron_presentacion: n/a`.
2. Capas Python: dominio `garmin_coaching/`; aplicacion
   `services/collector/main.py`; infraestructura `garminconnect/`,
   `garmin_auth.py`, `services/collector/supabase_client.py`. Regla:
   `garmin_coaching` nunca importa `garminconnect`, `supabase`, `fastapi` ni
   `requests`.
3. Capas web: dominio `apps/web/lib/` (calculos y modelos); presentacion
   `apps/web/app/` y `apps/web/components/`. `lib/supabase.ts` y
   `lib/openaiModels.ts` son infraestructura mal ubicada: se mueven a
   `lib/infra/` cuando se toquen; ningun modulo de calculo de `lib/` los
   importa.
4. Presentacion sin MVVM: se mantiene la justificacion de ADR-001 (Server
   Components con pantallas mayoritariamente estaticas; ViewModels
   desacoplados serian boilerplate). El criterio de revision de ADR-001 sigue
   vivo: si el estado bidireccional en cliente crece, nuevo ADR con
   `patron_presentacion: mvvm`.
5. Comprobacion de maquina pendiente: comando `arquitectura` en
   `.ies/gate.yaml` con import-linter (contrato: `garmin_coaching`
   independiente de `garminconnect`, `services`, `supabase`, `fastapi`) y
   dependency-cruiser en `apps/web` (`lib/**` salvo `lib/infra/**` no importa
   `@supabase/*` ni `openai`). Task propia; hasta entonces VII-08.

## Alternativas rechazadas

- **`n/a`**: hay tres artefactos desplegables; seria falso.
- **MVVM en `apps/web`**: rechazado en ADR-001 por costo sin beneficio en
  Server Components; nada ha cambiado.
- **Mover `supabase.ts` y `openaiModels.ts` ahora**: cambio sin spec; se hace
  al tocar (Articulo V).

## Consecuencias

- Desbloquea `ies task done` (VII-04 desaparece); VII-06 queda en INFO por
  este ADR; VII-08 hasta que exista el comando de arquitectura.
- Followup: task "gate arquitectura import-linter + dependency-cruiser"
  (allowlist `pyproject.toml`, `.importlinter`, `apps/web/package.json`,
  `apps/web/.dependency-cruiser.cjs`, `.ies/gate.yaml`).
