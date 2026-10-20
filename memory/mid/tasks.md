---
schema_version: 1
project_id: python-garminconnect
next_id: 42
source: ies-cli
last_updated: '2026-10-20T19:35:20Z'
---

# Task Ledger

## T-0019 — Sincronización de adaptadores canónicos a IES 0.2.0 y actualización de manifiesto

```yaml
id: T-0019
title: Sincronización de adaptadores canónicos a IES 0.2.0 y actualización de manifiesto
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: ready
input: Sincronizar los 9 adaptadores desactualizados del proyecto utilizando el intérprete
  Python del framework (/Users/alarcondiegof/ies-projects/ies-framework/.venv/bin/python)
  y scripts/sync-adapters.py sin --force. Preservar archivos preexistentes (CLAUDE.md
  y .vscode/settings.json), bindings, tasks.md.lock, evidencias de T-0017/T-0018 y
  metadatos históricos de .ies/project.yaml. Verificar .ies/adapters.json en 0.2.0
  y validar que sync-adapters --check reporte 0 adaptadores desactualizados o con
  drift y únicamente CLAUDE.md y .vscode/settings.json como preexistentes preservados.
expected_output: deliverables/T-XXXX.md con evidencia de antes/después, .ies/adapters.json
  en 0.2.0 y validación de sync-adapters --check
parent_task: null
dependencies: []
priority: medium
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Ejecución mediante Python del framework sobre scripts/sync-adapters.py sin --force
- Sincronización de los 9 adaptadores canónicos a IES 0.2.0
- Preservación de CLAUDE.md y .vscode/settings.json como preexistentes preservados
- Actualización de .ies/adapters.json a framework_version 0.2.0
- Preservación de .ies/project.yaml con framework_version 0.1.0
- Validación de sync-adapters --check reportando exclusivamente CLAUDE.md y .vscode/settings.json
  como preexistentes (código 3)
- Preservación íntegra de tasks.md, deliverables/T-0018.md, deliverables/T-0017.md
  y tasks.md.lock
allowlist:
- .agents/rules/ies.md
- .agents/workflows/sdd-autonomous.md
- .agents/workflows/sdd-implement.md
- .agents/workflows/sdd-plan.md
- .agents/workflows/sdd-verify.md
- .cursor/rules/00-ies-sdd.mdc
- .github/copilot-instructions.md
- AGENTS.md
- GEMINI.md
- .ies/adapters.json
created_at: '2026-10-14T17:37:15Z'
started_at: null
completed_at: null
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics: {}
edits: []
```

## T-0021 — Especificar correccion visual y responsive de Tri-Coach (SPEC-002)

```yaml
id: T-0021
title: Especificar correccion visual y responsive de Tri-Coach (SPEC-002)
project_id: python-garminconnect
origin: coordinator
destination: planner
status: ready
input: 'Preparar exclusivamente la propuesta completa de SPEC-002 layout-responsive
  y PLAN-002 para corregir la distribucion a la izquierda de Tri-Coach reportada por
  el humano en Safari. Aprobacion recibida: ''Aprobado, HITL por gate hasta nueva
  orden''. Esta etapa termina con entrega de planner y gate humano; no implementacion,
  cierre automatico, merge, push ni deploy. Baseline observada aeaa5da, checkout limpio
  antes de crear la spec. Causa probable: apps/web/app/globals.css main max-width:880px
  y margin:0; dashboard comparte layout y chat usa layout separado. Antecedente Safari
  reportado por otro chat: produccion v0.3.0 aeaa5da, viewport 1280, espacio izquierdo
  28px y derecho 188px; no es verificacion independiente ni prueba de defecto exclusivo
  Safari. Consultar T-0014/deliverables/T-0014.md solo como evidencia historica Chrome;
  no reabrir sus gates.

  Proponer REQ-001 equilibrio de margenes y ancho util en /, /retos, /mesociclos,
  /70-3-cartagena; REQ-002 responsive sin overflow global ni controles recortados
  (conservar scroll interno intencional de graficas); REQ-003 preservar chat independiente,
  navegacion y controles; REQ-004 evidencia visual Safari real antes/despues y regresion
  focalizada; REQ-005 SemVer/CHANGELOG y trazabilidad. Definir umbrales medibles y
  matriz proporcional 375,768,1280,1440 px con capturas Safari reales; distinguir
  WebKit automatizado de Safari. No probar chat con datos de salud ni modificar conversacion
  o datos persistentes: proponer prueba sintetica con respuesta controlada. Planear
  un implementer en worktree y viewer independiente; revisar conflictos de allowlist/version
  con T-0017 y T-0020 (sin modificar esas tasks) y proponer orden explicito sin bloquear
  por deuda ajena. Evaluar al menos dos alternativas CSS/layout, proponer solucion
  minima, requisitos EARS, test por criterio, version objetivo compatible con ramas
  pendientes, ADR propuesto, rollback y entrega humana a produccion. Ninguna dependencia
  nueva ni refactor backend. Parar y reportar si requiere ampliar alcance, secretos
  o mutaciones de datos. Lee codigo solo para planificacion, sin arrancar servicios,
  ejecutar builds ni navegador en esta fase.

  Tu unica escritura es deliverables/T-0021.md (envelope canonico y SDLC), incluyendo
  contenido completo propuesto de spec.md, plan.md y ADR dentro de la entrega. Mantener
  specs/002-layout-responsive en draft sin editarlos: coordinator materializara el
  contenido tras aprobacion humana. No generar otras tasks, no subagentes, no editar
  memoria/ledger.'
expected_output: deliverables/T-0021.md con SPEC-002 y PLAN-002 completos propuestos,
  ADR, matriz REQ-test, tasks hijas con allowlists/dependencias y decision humana
  requerida; sin codigo ni aprobaciones
parent_task: null
dependencies: []
priority: medium
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/architecture.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- mid/decisions.md
- mid/risks.md
- mid/open-questions.md
acceptance_criteria:
- 'REQ-001/002: especificar geometria y responsive medibles para las cuatro vistas
  dashboard y chat separado.'
- 'REQ-003/004: matriz Safari real antes/despues, pruebas por criterio y regresion
  navegacion/chat sintetica sin datos persistentes.'
- 'REQ-005: plan SemVer/CHANGELOG, resolucion de solapes T-0017/T-0020, rollback y
  procedimiento humano de release.'
- 'SPEC-002/PLAN-002: alternativas, ADR propuesto, tasks con REQ/input/output/allowlist/dependencias,
  SDLC y HITL por gate; entrega unica sin modificar implementacion.'
allowlist:
- deliverables/T-0021.md
created_at: '2026-10-16T20:53:29Z'
started_at: null
completed_at: null
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics: {}
edits: []
```

## T-0022 — Plan integral de centrado Safari, historial sincronizado y GPT-6 Luna High (SPEC-002)

```yaml
id: T-0022
title: Plan integral de centrado Safari, historial sincronizado y GPT-6 Luna High
  (SPEC-002)
project_id: python-garminconnect
origin: coordinator
destination: planner
status: ready
input: 'Preparacion aprobada por humano el 2026-10-17: SI al paquete de planificacion
  ampliado (centrado Safari + historial entre dispositivos), manteniendo HITL por
  gate. Nueva instruccion explicita: HITL es sesion humana de dudas/instrucciones
  a Coordinator; HITL y Coordinator modelo solicitado gpt-6-astra esfuerzo High. Coordinator
  unico agente principal que crea tasks, no implementa. Planner planifica, implementer
  codifica en su worktree, viewer QA/revision. Todos cumplen contratos IES, SDLC,
  EARS, Clean Code, Clean Architecture, HITL y WORKING_DISCIPLINE; multiagentes segun
  necesidad y paralelismo solo independiente. Chat de Tri-Coach usara UNICAMENTE gpt-6-luna
  con esfuerzo high, sin selector ni fallback a otro modelo. Esto es requisito de
  producto, no modelo de todos los subagentes.

  Entrega UNICA de planificacion en deliverables/T-0022.md. Usa T-0021 y deliverables/T-0021.md
  como antecedente no aprobado, sin sobrescribirlos ni repetir auditoria. Completa
  propuesta integral SPEC-002/PLAN-002 o descomposicion documentada en specs si indispensable,
  lista para gate humano, con contenido completo y ADR propuestos dentro de tu entrega.
  Specs actuales quedan draft intactas hasta aprobacion. No codigo, tareas hijas reales,
  servicios, tests runtime, navegador, llamadas de inferencia, cambios de bindings/ledger/memoria,
  Git de escritura, migraciones, backups de datos reales, importacion, merge, push
  ni deploy.

  Evidencia reutilizable: checkout aeaa5da; modificaciones previas solo ledger T-0021,
  draft specs/002-layout-responsive y entrega T-0021. Safari real abierto el 2026-10-17
  en https://web-chi-eight-31.vercel.app/ confirma v0.3.0 aeaa5da, dashboard concentrado
  a izquierda, pantalla amplia. Una conversacion del 16 permanece con pregunta/respuesta;
  no copiar contenido personal. CSS main max-width880 y margin0; chat separado. coachStorage.ts
  MAX_CHATS4, slice en lectura/escritura/upsert, localStorage sin sincronizacion,
  lectura fallida => [] y escritura sin manejo robusto. Limite proviene del commit
  eba5365. API chat recibe mensajes, devuelve respuesta, no persiste historial de
  app. No atribuir la perdida particular del humano a una causa no reproducida ni
  prometer recuperar datos ya descartados.

  Nuevo alcance: historial duradero sincronizado por identidad autenticada, acceso
  exclusivo por usuario y validacion server-side/RLS; no usar UUID MVP compartido
  como identidad ni confiar en user_id de payload. Migracion idempotente y conservadora
  de conversaciones locales sobrevivientes a cuenta confirmada, sin borrado ni sobrescritura
  ni importacion automatica a cuenta equivocada, control de fallos/cuota/concurrencia
  y feedback de guardado, paginacion sin truncado destructivo. Definir retencion sin
  borrado automatico; distinguir retencion de mensajes de ventana de contexto al modelo.
  Especificar pruebas >4 chats, recargar/reabrir, dos navegadores misma cuenta, aislamiento
  dos usuarios, errores escritura/red y reintentos sin duplicados. Minimizar acceso
  a datos existentes; auth/configuracion cloud/migraciones/importacion real y despliegue
  tienen gates humanos propios, solo se planifican. El schema MVP local tiene policies
  USING(true) sobre tablas existentes y user fijo: no asumir que live tiene igual
  politica ni reutilizar ese patron para historial; no ampliar a auditoria/refactor
  general. Si asegurar contexto de salud del chat requiere identidad del usuario MVP,
  declarar ese vinculo acotado como requisito, no permitir acceso arbitrario tras
  login.

  Centrado: conservar propuesta 1120px de T-0021 como decision no aceptada, revisar
  viewport amplio observado ademas de movil, mediciones centradas respecto a area
  principal y evidencia Safari real; validacion proporcional, no repetir 40 capturas
  o construir proxy/harness grande por inercia. Cambia la antigua prohibicion de persistencia
  de fixtures: nuevos tests DEBEN probar persistencia sintetica real en almacenamiento
  de test aislado, autorizacion de esta planificacion NO toca datos de usuario. Separar
  pruebas backend/API, Safari y UI, sin inferencia cloud real en esta fase.

  Modelo app: documentacion oficial obtenida por coordinator https://developers.openai.com/api/docs/models/gpt-6-luna
  confirma ID gpt-6-luna, high soportado, endpoints responses y chat_completions;
  function calling en Chat Completions solo reasoning_effort none (no hay tools en
  route actual). Especificar parametro high segun endpoint elegido y verificacion
  del payload en servidor, sin temperature/top_p incompatibles, no aceptar modelo/esfuerzo
  arbitrario del cliente/env/preferencia vieja; fallo visible si modelo no disponible,
  no sustitucion. Acceso de la cuenta a modelo NO_VERIFICADO hasta gate de prueba
  autorizado. El actual lib/openaiModels.ts mezcla modelos de env/API y acepta requested
  probable, y route no envia reasoning effort.

  Gobernanza: .ies/models.yaml y .ies/environment.yaml aun declaran Gemini/Antigravity.
  Registrar discrepancia con Astra6 High/Codex solicitado, preparar propuesta acotada
  de alineacion (fuentes canonicas/CLI; no editar adaptadores generados ni contratos
  framework). No afirmar que configuracion deseada cambie modelo efectivo de sesiones.
  HITL no es rol ejecutor que se agregue arbitrariamente al registry. Modelos de planner/implementer/viewer
  NO fueron fijados por el humano: no inventar cambio masivo, proponer conservar bindings
  o herencia observada con divergencia declarada. Esta discrepancia de identidad sola
  NON_BLOCKING para planificar.

  Resolver version/orden frente T-0017/T-0020 sin modificarlas ni integrarlas, considerando
  si alcance historial/modelo corresponde MINOR en vez de simple PATCH0.3.2. Dimensionar
  tareas/allowlists disjuntas o seriales, un implementer por task, viewer independiente;
  REQ EARS por comportamiento, criterios ejecutables, tests-first, backups/rollback
  no destructivos, gates por fase. Respetar CleanArchitecture al tocar lib/openaiModels.ts/supabase.ts
  (ADR002), separar dominio/infra/presentacion solo lo necesario. Una aprobacion del
  futuro plan no aprueba automaticamente implementacion, viewer, cambios cloud o deploy:
  indicar con precision que gate aprueba cada accion. Entrega concisa y ejecutable,
  no perfeccionamiento documental; para preguntas materiales ofrecer recomendacion
  y gate claro. Termina con decision requerida.'
expected_output: 'deliverables/T-0022.md: spec y plan integrales propuestos, ADR,
  causas confirmadas vs hipotesis, tasks con allowlists/dependencias, matriz REQ-pruebas,
  migracion conservadora, modelo exclusivo, roles/modelos solicitados vs efectivos,
  gates HITL y decision humana; cero implementacion'
parent_task: null
dependencies: []
priority: medium
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/architecture.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- mid/decisions.md
- mid/risks.md
- mid/open-questions.md
acceptance_criteria:
- 'REQ-UI: geometria centrada Safari real, responsive y chat sin regresion; matriz
  proporcional con ancho grande.'
- 'REQ-HIST: identidad autenticada, aislamiento, persistencia entre navegadores, mas
  de4 chats, migracion idempotente preservando originales, fallos y concurrencia;
  test por criterio.'
- 'REQ-MODEL: exclusivamente gpt-6-luna high forzado en servidor, sin selector/fallback/override
  cliente; contrato API y cuenta disponible separados de plan.'
- 'REQ-GOV: roles solicitados y discrepancias de bindings trazadas; todos los gates
  HITL, SDLC/EARS/CleanArchitecture; tareas separables con allowlist y dependencia.'
- 'REQ-RELEASE: version/orden coherentes con T-0017/T-0020, rollback y gate de datos/cloud;
  entrega completa propuesta sin cambios fuera de allowlist.'
allowlist:
- deliverables/T-0022.md
created_at: '2026-10-17T12:04:35Z'
started_at: null
completed_at: null
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics: {}
edits: []
```

## T-0023 — Alinear contexto Codex y conservar seleccion Gemini para Antigravity

```yaml
id: T-0023
title: Alinear contexto Codex y conservar seleccion Gemini para Antigravity
project_id: python-garminconnect
origin: human
destination: coordinator
status: ready
input: 'Instruccion humana explicita del 2026-10-17: al usar Antigravity conservar
  Gemini; al usar Codex aplicar normas acordadas, actualizar para evitar bloqueos/ambiguedades.
  Scope administrativo de coordinator: activar Codex mediante ies env set con principal
  gpt-6-astra/high, subagentes predeterminado heredado gpt-6-astra/high sin imponer
  un modelo distinto por rol (ajustable mediante gate de task), autonomy hitl; conservar/restaurar
  seleccion Antigravity gemini-3.8-flash/high para principal/subagentes mediante comando
  canonico documentado. Respaldar primero environment/models y comprobar que roles
  no SDD, tier, modos, max_iterations, especialistas y fuentes generadas conservan
  contenido. No nueva fuente paralela de bindings: unica autoridad .ies/models.yaml,
  environment como configurador; decisiones/ADR contienen politica y receta de seleccion,
  no autocambio nativo ficticio. Documentar un entorno activo compartido, cambio deliberado
  por Coordinator, no conmutacion concurrente durante una task; prompts emitidos preservan
  contexto de origen. Registrar en DEC-008, ADR-006 de proyecto y handoff la separacion
  HITL/Coordinator/planner/implementer/viewer, herencia subagentes, SDLC/EARS/CleanCode/CleanArchitecture/WorkingDiscipline
  y HITL por gate, multiactor solo por tasks canónicas con worktrees. Distinguir binding
  de modelo efectivo de sesion, diferencia aislada NON_BLOCKING; metadato native_subagents
  false heredado del catalogo IES no impide herramientas nativas observadas. No editar
  framework/adaptadores a mano ni cambiar API de producto: requisito gpt-6-luna/high
  queda pendiente de implementar segun T-0022, no se migra a Astra. No aprobar SPEC002
  ni disparar implementers/viewers de producto. Validar ies models validate, memory
  validate, doctor, constitution task, Git scope y prompts coordinator/planner compilados
  con modelo correcto. Verificar retorno Gemini en copia temporal con CLI sin alternar
  el repo vivo. Sin inferencia ni evaluacion de calidad, sin secretos, commit/push/merge/deploy;
  reportar limitacion de evals y selector vivo en entrega. Si CLI fuerza cambio fuera
  de scope o permiso requerido, detener esa parte y conservar evidencia. Unica entrega
  deliverables/T-0023.md; no cerrar task automaticamente.'
expected_output: Configuracion Codex activa con gpt-6-astra/high y HITL; politica
  persistida Antigravity Gemini, evidencia CLI/validacion/prompt, respaldo y vuelta
  verificable, roles ajenos preservados; deliverables/T-0023.md.
parent_task: null
dependencies: []
priority: medium
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- mid/decisions.md
- long/constitution.md
- immediate/handoff.md
acceptance_criteria:
- 'REQ-CTX-001: Codex principal Astra6 High y herencia subagentes, Antigravity Gemini
  conservado/restaurable por CLI; no afirmar autodeteccion.'
- 'REQ-CTX-002: roles, HITL, gates y responsabilidades persistidos; ninguna aprobacion
  de producto inferida.'
- 'REQ-CTX-003: modelos/memoria/doctor y compilacion coherentes; scope verificado
  y backup, sin cambios en app/framework.'
allowlist:
- .ies/models.yaml
- .ies/environment.yaml
- memory/mid/decisions.md
- memory/immediate/handoff.md
- memory/long/adr/ADR-006-tool-context-models.md
- deliverables/T-0023.md
created_at: '2026-10-17T12:11:20Z'
started_at: null
completed_at: null
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics: {}
edits: []
```

## T-0024 — Materializar aprobacion G0 de SPEC-002 y PLAN-002

```yaml
id: T-0024
title: Materializar aprobacion G0 de SPEC-002 y PLAN-002
project_id: python-garminconnect
origin: human
destination: coordinator
status: ready
input: 'El humano aprobo el plan integral con Adelante, aprobado tras confirmar el
  siguiente gate. Ejecutar solo G0 de deliverables/T-0022.md: materializar SPEC-002/PLAN-002
  y ADR003/004/005, actualizar standards segun ADR004, registrar DEC009 y aprobacion
  con ies spec approve. Incorporar como precedencia explicita DEC008/ADR006/T0023
  ya aceptados para evitar reabrir G1 o contradecir herencia de modelos. Preservar
  identidad/version/estado de specs hasta CLI; no modificar estado a mano. Prohibido
  codigo, despacho implementer/viewer, cloud, inferencia, commits, merge, push y deploy.
  Validar fidelidad de 22 requisitos y pruebas, memoria, constitucion y aprobacion
  CLI. Detener ante contradiccion material del alcance aprobado; resolver solo ajustes
  documentales. Preparar propuesta cerrada I-UI para siguiente gate, sin ejecutarla.'
expected_output: SPEC-002 y PLAN-002 materializados y approved por CLI; ADR003/004/005
  aceptados; standards y DEC009/handoff consistentes; deliverable propia con evidencia
  y siguiente gate I-UI.
parent_task: T-0022
dependencies: []
priority: medium
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/standards.md
- mid/decisions.md
- immediate/handoff.md
acceptance_criteria:
- 'REQ-G0-001: 22 requisitos EARS y P01-P22 preservados con trazabilidad y gates HITL;
  sin codigo.'
- 'REQ-G0-002: decision humana trazable, aprobacion por CLI, memoria valida y modelos
  no alterados.'
allowlist:
- specs/002-layout-responsive
- memory/long/adr/ADR-003-centered-container.md
- memory/long/adr/ADR-004-private-history.md
- memory/long/adr/ADR-005-exclusive-chat-model.md
- memory/long/standards.md
- memory/mid/decisions.md
- memory/immediate/handoff.md
- deliverables/T-0024.md
created_at: '2026-10-17T12:16:09Z'
started_at: null
completed_at: null
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics: {}
edits: []
```

## T-0040 — Privacidad de logs CI, logging en login_client, origen del restore y deploy script (pendiente de T-0017)

```yaml
id: T-0040
title: Privacidad de logs CI, logging en login_client, origen del restore y deploy
  script (pendiente de T-0017)
project_id: python-garminconnect
origin: human
destination: implementer
status: ready
input: 'Recoge lo pendiente de T-0017 (cancelada por decision de Diego, ''Ok, adelante
  con A''); el ruff lo cubre T-0039. Partir de master tras T-0039; la rama local task/T-0017
  (f3fc13a) sirve de referencia, no se mezcla tal cual. 1. Sustituir los except Exception:
  pass de scripts/garmin_auth.py:login_client por _LOGGER.warning sin volcar la excepcion
  sin sanitizar (REQ-005). 2. persist_tokens_to_supabase: un fallo de persistencia
  debe avisar (hoy retorna False sin warning). 3. Registrar en el log del workflow
  la fuente de restauracion del token (supabase | b64_fallback). 4. Ajustar scripts/deploy_web_vercel.sh
  para Root Directory = apps/web de Vercel. 5. DEC-004: en coaching-daily-collect.yml
  el JSON final solo incluye upsert ok/fallo, tokens_persisted y fuente del restore;
  quitar zone, acwr, guards y last_activity; ningun print/log del collector (garmin_coaching/,
  services/collector/, scripts/garmin_auth.py) emite metricas, nombres de actividad
  ni coordenadas en Actions. 6. Pruebas web: sin --test-skip-pattern ni fallos de
  node --test lib/*.test.mjs (hallazgos de T-0018). 7. Version PATCH siguiente a la
  de T-0039 en apps/web/package.json y lock + apps/web/CHANGELOG.md (ADR-009).'
expected_output: deliverables/<task>.md con logging, trazabilidad de restore, sanitizacion
  de logs de Actions, deploy script validado y version PATCH
parent_task: null
dependencies:
- T-0039
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Excepciones en login_client logueadas con _LOGGER.warning sin datos sensibles
- Un fallo de persist_tokens_to_supabase deja un warning
- Workflow reporta en log la fuente de restauracion del token (supabase | b64_fallback)
- scripts/deploy_web_vercel.sh verificado con Root Directory de Vercel
- El log de un run de Coaching Daily Collect no contiene metricas de salud, nombres
  de actividad ni ubicacion; verificado en un run real despues del merge
- ruff check . y ruff format --check . siguen limpios; pruebas web sin skips
- Version PATCH con entrada en apps/web/CHANGELOG.md (ADR-009)
allowlist:
- scripts/garmin_auth.py
- scripts/deploy_web_vercel.sh
- services/collector
- garmin_coaching
- .github/workflows/coaching-daily-collect.yml
- tests
- apps/web/CHANGELOG.md
- apps/web/package.json
- apps/web/package-lock.json
created_at: '2026-10-20T18:43:53Z'
started_at: null
completed_at: null
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics: {}
edits: []
```

## T-0041 — Gate arquitectura: import-linter y dependency-cruiser (ADR-002)

```yaml
id: T-0041
title: 'Gate arquitectura: import-linter y dependency-cruiser (ADR-002)'
project_id: python-garminconnect
origin: human
destination: implementer
status: ready
input: 'Recreacion de T-0020 (cancelada por decision de Diego, ''Ok, adelante con
  A'') con la dependencia actualizada. Python: anadir import-linter a las dependencias
  de desarrollo en pyproject.toml y un archivo .importlinter con el contrato ''garmin_coaching
  independiente de garminconnect, services, supabase, fastapi, requests'' (ADR-002
  §2 y §5). Web: anadir dependency-cruiser en apps/web/package.json con apps/web/.dependency-cruiser.cjs
  que prohiba que lib/** (salvo lib/infra/**) importe @supabase/* u openai (ADR-002
  §3). Registrar en .ies/gate.yaml dos comandos cuyo nombre contenga ''arquitectura''
  (lint-imports; npx depcruise en apps/web), sdlc: pruebas. No mover supabase.ts ni
  openaiModels.ts: si hoy violan la regla, el contrato web los exime por ruta y se
  anota como deuda en el deliverable. Depende de T-0040 (ambas tocan apps/web/package.json),
  que depende de T-0039 (pyproject.toml).'
expected_output: Ambos linters en verde, comandos de arquitectura en .ies/gate.yaml,
  ies constitution check sin VII-08 y deliverable con la salida del gate y la deuda
  registrada.
parent_task: null
dependencies:
- T-0040
priority: medium
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills:
- verification-gates
memory_refs:
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- long/standards.md
acceptance_criteria:
- ies gate --task T-XXXX en PASS con los comandos de arquitectura ejecutados
- ies constitution check no reporta VII-08
- un import sintetico de garminconnect dentro de garmin_coaching hace fallar lint-imports
allowlist:
- pyproject.toml
- .importlinter
- apps/web/package.json
- apps/web/package-lock.json
- apps/web/.dependency-cruiser.cjs
- .ies/gate.yaml
created_at: '2026-10-20T18:44:04Z'
started_at: null
completed_at: null
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics: {}
edits: []
```
