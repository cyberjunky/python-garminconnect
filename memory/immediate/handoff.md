---
schema_version: 1
project_id: python-garminconnect
layer: immediate
last_updated: '2026-10-17T13:14:00Z'
source: instruccion humana en HITL - Tri-Coach (cola de 3 actualizaciones de producto + ratificacion de 8 reglas de Working Discipline y modelos)
confidence: alta para configuracion y evidencia declaradas; runtime de modelos no verificado
---

# Handoff

## Pausa y traslado a Antigravity

- Sesion Codex pausada por instruccion humana tras guardar estado y handoff.
  No iniciar G2 ni otros trabajos desde esta sesion hasta nueva instruccion.
- Continuacion designada: Coordinator de Antigravity en
  `/Users/alarcondiegof/ies-projects/python-garminconnect`.
- G0 registrado y configuracion G1 aceptada. G2 I-UI no ejecutado: no hay nueva
  task implementer, prompt despachado, checkpoint o worktree para este gate.
- El mensaje de transporte preparado en la conversacion contiene la aprobacion
  acotada para G2 al pegarlo el humano en destino. No se ha enviado a otra sesion
  ni verificado su recepcion. Esta orden de guardar/pausar solo persiste contexto.
- Fuente del paquete G2: `deliverables/T-0024.md`, seccion «Propuesta cerrada
  para G2 I-UI»; fuentes aprobadas: SPEC-002/PLAN-002 y DEC-009.
- En destino verificar la raiz y el contexto; seleccionar Antigravity/Gemini
  3.8 Flash High por receta ADR-006 antes de compilar prompts, si hace falta y
  sin concurrencia sobre el registro. El entorno guardado aun es Codex/Astra:
  esta pausa no conmuta configuracion ni cambia selectores de sesiones.
- Coordinator crea la task por CLI y delega a Implementer; no codifica.
  Conservar allowlist, worktree aislado, reserva serial frente a T-0017/T-0020,
  pruebas Safari reales con fixtures y version candidata 0.4.0-rc.1. Viewer G3
  mantiene aprobacion independiente. Historial/Auth/Luna van en etapas posteriores.
- Persistencia realizada con `IES_ACTOR=coordinator ies update`: current-status
  actualizado, memoria/modelos validados. Cambios documentales y ledger siguen
  sin commit; `memory/mid/current-status.md` tambien cambio por esta persistencia.
  Revisar la lista completa del snapshot documental antes del checkpoint; no
  usar `git add -A` ni incorporar cambios ajenos. No se hizo staging, commit,
  push, merge, despliegue, inferencia ni cambios de datos reales al guardar.
- Avisos existentes de update: T-0011 sin allowlist historica; architecture.md
  pendiente de sintesis; VII-08 pendiente ligado a T-0020; CLAUDE.md y
  .vscode/settings.json conservados como excepciones no gestionadas. Guardar
  no autoriza corregirlos ni crear tasks adicionales por esos avisos.

## Contexto de herramienta y roles

Decision vigente: `memory/mid/decisions.md#DEC-008` y
`memory/long/adr/ADR-006-tool-context-models.md`.

- Entorno activo: Codex. Seleccion solicitada HITL/Coordinator: GPT-6 Astra / High.
  Equipo SDD sin override: predeterminado del principal. Bindings activos en
  `.ies/models.yaml`; herramienta/esfuerzo en `.ies/environment.yaml`.
- Al trabajar en Antigravity, conservar Gemini mediante la receta de ADR-006.
  No asumir autodeteccion ni conmutar el registro compartido durante tareas en curso.
- HITL es la sesion humana de consulta e instrucciones, sin creacion de tasks.
  Coordinator es el unico generador de tasks/prompts; Planner planifica,
  Implementer codifica en su worktree y Viewer hace revision/QA independiente.
- HITL por gate hasta nueva orden. SDLC/EARS/Clean Code/Clean Architecture y
  Working Discipline siguen aplicando. Multiagentes solo via tasks/prompts;
  paralelismo requiere alcances y worktrees independientes.
- El indicador historico `native_subagents: false` no invalida las delegaciones
  nativas observadas en Codex. Comprobar capacidad e aislamiento efectivos antes
  de codificar; un nombre de modelo distinto no es bloqueo por si solo.
- Configuracion deseada no prueba el modelo efectivo del selector de una sesion.

## Estado de producto y proximo ciclo

SPEC-002 y PLAN-002 completados al 100%, auditados por Viewer independiente con
veredicto APROBAR e integrados en `master` mediante merge humano en commit `26de2fb`.
- T-0025 / T-0026 (I-UI / V-UI): Centrado responsive en Safari y 0.4.0-rc.1 (done 🟢).
- T-0027 / T-0028 (I-SERVER / V-SERVER): Backend de historial privado, auth RLS, modelo exclusivo gpt-6-luna High, Clean Architecture P22 y 0.4.0-rc.2 (done 🟢).
- T-0029 / T-0030 (I-CLIENT / V-INTEGRAL): ViewModel MVVM desacoplado, UI de chat sincronizado, login Supabase Auth OTP, importación opt-in con preservación byte a byte de localStorage, retiro de selectores de modelos y versión final 0.4.0 (done 🟢).
- 58/58 tests pasando, build Next.js 15 código 0 y 0 drift de allowlist.

Siguiente ciclo de desarrollo: Creación y especificación formal de `SPEC-003` (versión 0.5.0 MINOR) para implementar la cola de producto solicitada en este handoff («Qué atender», tarjeta «Macrociclo» de 4 bloques y nueva ruta `/tendencia`).

Despliegue de 0.4.0 a producción: Reservado a ejecución humana siguiendo PLAN-002 §8 (migración SQL en Supabase cloud, configuración de OTP por invitación y despliegue a Vercel con OPENAI_API_KEY).

## Cola de actualizaciones solicitadas por el humano (2026-10-17)

Instruccion humana recibida en sesion HITL para incluir en cola y entregar a
Coordinator:

1. **Qué atender (`apps/web/app/(dashboard)/retos/page.tsx` y `apps/web/lib/dashboard.ts`)**:
   - Incluir para cada alerta/indicador en «Qué atender» una recomendacion accionable en una frase corta fundamentada en investigacion de ciencia deportiva (modulacion parasimpatica/HRV, higiene y deuda de sueno, recarga autonomica/Body Battery, control de ratio de carga aguda:cronica ACWR < 1.3 para prevencion de lesiones, y descarga ante sobreesfuerzo/overreaching).
2. **Macrociclo (`apps/web/app/(dashboard)/retos/page.tsx` y logica de dominio asociada)**:
   - Ampliar la tarjeta «Macrociclo» para que incluya cuatro bloques claros:
     a) breve descripcion de que es un macrociclo;
     b) explicacion del momento/fase actual (`code`, `name`, `focus`, deporte y techo de FC/duracion);
     c) como mejorarlo (recomendacion practica alineada con la fase activa y el estado actual);
     d) cuando termina (fecha de cierre de la fase actual en formato `es-CO`, dias restantes y referencia al cierre del macrociclo).
3. **Tendencia mensual en menu lateral nuevo (`apps/web/components/DashboardNav.tsx`, `apps/web/app/(dashboard)/retos/page.tsx` y nueva ruta `apps/web/app/(dashboard)/tendencia/page.tsx`)**:
   - Retirar la tarjeta «Tendencia 14d» de la vista `/retos`.
   - Incluir un item nuevo «Tendencia» (`/tendencia`) en el menu lateral (`DashboardNav`).
   - Mostrar en una sola hoja (`/tendencia`) los avances del mes (ultimos 30 dias / mes en curso): barra y conteo de distribucion de zonas (`VERDE`, `AMARILLO`, `ROJO`), resumen de avances del mes en metricas clave (HRV, sueno, Body Battery, estres, ACWR/VO2max) y tabla mensual con fechas `es-CO` y `tabular-nums`.

Orden y gobernanza para Coordinator:
- Mantener la disciplina SDD/EARS/Clean Architecture (logica pura en `apps/web/lib/`, presentacion en `app/(dashboard)/` y `components/`) y la reserva serial del grupo `R` (`package.json`, `package-lock.json`, `CHANGELOG.md`, `README.md`, `version.test.mjs`).
- Coordinar el orden respecto a `SPEC-002` (`PLAN-002` G2 `I-UI` ya propuesto en `deliverables/T-0024.md` y creado como `T-0025`): encadenar como nueva spec SDD (`SPEC-003`) o integrar secuencialmente tras el gate activo sin colision de allowlists ni worktrees, verificando que la nueva ruta `/tendencia` cumpla tambien la geometria centrada de `ADR-003`.

## Confirmacion de Working Discipline, roles y modelos vigentes (2026-10-17)

Reglas ratificadas explicitamente por el humano en `HITL - Tri-Coach` para trabajar en adelante:

1. **HITL - Tri-Coach**: sesion humana para clarificar dudas y enviar instrucciones cerradas a Coordinator; modelo preferido **Astra 6 High** (`gpt-6-astra` / `high`). No crea tasks en el ledger ni muta codigo.
2. **Garmin - Coordinator**: Agente Principal con la autorizacion exclusiva para crear tareas (`ies task add`), compilar prompts (`ies prompt`), gestionar checkpoints/worktrees y consolidar entregas:
   - En **Antigravity**: **Gemini 4 Argon Max** (actualizar referencia en `ADR-006` / `.ies/environment.yaml` / `.ies/models.yaml` cuando opere en Antigravity).
   - En **Codex**: **Astra 6 High** (`gpt-6-astra` / `high`).
3. **Implementer**: subagente encargado de codificar y ejecutar pruebas (*tests-first*) dentro de su worktree aislado y su `allowlist`.
4. **Planner**: subagente encargado de la planificacion de detalles (`spec.md` EARS, `plan.md`, ADRs, matriz de pruebas y descomposicion de tasks).
5. **Viewer**: subagente independiente en solo lectura encargado de revisoria y QA (`ies git verify`, `ies constitution check`, `ies gate`, veredicto formal).
6. **Cumplimiento normativo**: cada agente y subagente debe cumplir estrictamente su rol siguiendo **SDLC**, **EARS**, **Clean Code**, **Clean Architecture** (`ADR-002`) y **HITL** por gate.
7. **Multiagentes**: se usaran multiagentes cuando las tareas y la separacion de responsabilidades o paralelismo (con worktrees y allowlists disjuntos) lo requieran.
8. **Working Discipline**: seguir siempre la disciplina descrita en `/Users/alarcondiegof/ies-projects/ies-framework/docs/WORKING_DISCIPLINE.md`.
