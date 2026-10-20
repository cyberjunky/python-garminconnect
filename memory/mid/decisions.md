---
schema_version: 1
project_id: python-garminconnect
layer: mid
last_updated: '2026-10-19T20:00:00Z'
source: coordinator
confidence: alta
---

# Decisions

## DEC-011: Aprobacion humana G0 de SPEC-004 y PLAN-004

- **Fecha**: 2026-10-17. **Task**: T-0036.
- **Autoridad**: el humano respondio «Ok, Adelante, Parobado» a la propuesta de aprobacion de Gate G0 presentada por el Coordinator tras la entrega del planificador T-0036. No se transforma HITL en autonomia; cada gate conserva aprobacion propia.
- **Decision**: aceptar SPEC-004/PLAN-004 integralmente para la version 0.5.1 PATCH: (1) correccion de desborde de metricas en TodayCard con minmax 7.5rem, min-width 0, overflow-wrap break-word, line-height 1.25, badge flex-shrink 0 y verificacion geometrica scrollWidth <= clientWidth; (2) CoachChat en primer cuarto superior (~25vh) de Inicio inmediatamente antes de TodayCard con compositor compacto de 2 filas y scroll interno en historial; (3) sincronizacion reactiva de accessToken en useCoachConversation (setAccessToken), captura resiliente de errores HTTP, merge deduplicado con conversaciones locales supervivientes de localStorage en CoachChat y CoachChatScreen con fallback local y respaldo inmediato con upsertChat; (4) Clean Architecture (ADR-002, P22), geometria centrada responsive (ADR-003) y paquete SemVer 0.5.1 PATCH en Grupo R. Aprobar la spec mediante `IES_ACTOR=coordinator ies spec approve 004-patch-layout-chat --decision-ref memory/mid/decisions.md#dec-011-aprobacion-humana-g0-de-spec-004-y-plan-004`.
- **Descomposicion**: autorizar las tasks hijas T-0037 (I-PATCH-051, implementer en worktree aislado) y T-0038 (V-VIEWER-051, viewer en solo lectura).
- **Limites**: G0 no autoriza codigo de aplicacion directo por coordinator ni merge o deploy automatico. Cada implementer opera en su worktree aislado y su allowlist disjunta. Despliegue a produccion queda reservado a ejecucion humana (PLAN-004 seccion 8).
- **Evidencia**: `deliverables/T-0036.md`, `specs/004-patch-layout-chat/spec.md` (9 requisitos EARS REQ-001..009, pruebas P01..P09) y `specs/004-patch-layout-chat/plan.md`.

## DEC-010: Aprobacion humana G0 de SPEC-003 y PLAN-003

- **Fecha**: 2026-10-17. **Task**: T-0031.
- **Autoridad**: el humano respondio «adelante» a la propuesta de aprobacion de Gate G0 presentada por el Coordinator tras la entrega del planificador T-0031. No se transforma HITL en autonomia; cada gate conserva aprobacion propia.
- **Decision**: aceptar SPEC-003/PLAN-003 integralmente: (1) motor de recomendaciones accionables de ciencia deportiva en «Qué atender» basado en fisiologia (HRV, sueno, Body Battery, ACWR < 1.3, sobreesfuerzo); (2) tarjeta «Macrociclo» en 4 bloques (definicion, momento/fase actual con techo FC/duracion, como mejorarla y cierre es-CO); (3) nueva ruta `/tendencia` en menu lateral DashboardNav con barra de zonas VERDE/AMARILLO/ROJO, resumen mensual de metricas clave y tabla tabular-nums centrada; (4) Clean Architecture (ADR-002, P22), contenedor centrado responsive max 1120px (ADR-003) y paquete SemVer 0.5.0 MINOR. Aprobar la spec mediante `IES_ACTOR=coordinator ies spec approve 003-tendencia-macrociclo --decision-ref memory/mid/decisions.md#dec-010-aprobacion-humana-g0-de-spec-003-y-plan-003`.
- **Descomposicion**: autorizar las tasks hijas de implementacion y verificacion: T-0032 (I-DOMAIN-RETOS), T-0033 (I-TENDENCIA-NAV), T-0034 (I-RELEASE-050 con reserva serial de grupo R) y T-0035 (V-INTEGRAL-050, viewer en solo lectura).
- **Limites**: G0 no autoriza codigo de aplicacion directo por coordinator ni merge o deploy automatico. Cada implementer opera en su worktree aislado y su allowlist disjunta. Despliegue a produccion queda reservado a ejecucion humana (PLAN-003 seccion 8).
- **Evidencia**: `deliverables/T-0031.md`, `specs/003-tendencia-macrociclo/spec.md` (20 requisitos EARS REQ-001..020, pruebas P01..P20) y `specs/003-tendencia-macrociclo/plan.md`.

## DEC-009: Aprobacion humana G0 de SPEC-002 y PLAN-002

- **Fecha**: 2026-10-17. **Task**: T-0024, propuesta T-0022.
- **Autoridad**: el humano respondio «Adelante, aprobado» al siguiente gate presentado: aprobar el plan de centrado Safari, historial sincronizado y Luna High exclusivo. Se registra G0 de la propuesta T-0022; no se transforma HITL en autonomia.
- **Decision**: aceptar SPEC-002/PLAN-002 integral, maximo 1120px, Supabase Auth por invitacion/RLS privado, importacion opt-in conservando originales, GPT-6 Luna High fijo, ViewModel de chat y paquete final 0.4.0 con etapas seriales. Aceptar ADR-003/004/005 y actualizar standards segun ADR-004. Materializar documentos y registrar con `IES_ACTOR=coordinator ies spec approve 002-layout-responsive --decision-ref memory/mid/decisions.md#dec-009-aprobacion-humana-g0-de-spec-002-y-plan-002`.
- **Precedencia**: DEC-008/ADR-006 y configuracion T-0023 ya aceptados resuelven C-GOV/G1; se conserva seleccion Codex/Astra y Antigravity/Gemini, incluida herencia declarada. No repetir configuracion ni inferir modelo efectivo de sesiones.
- **Limites**: G0 no despacha implementers ni viewers. G2 por implementer, G3 viewer, G4 aceptacion/merge humano, G5 datos/Auth, G6 prueba sintetica modelo, G7 release humano y G8 importacion por usuario conservan gates propios. No se autorizan codigo, cloud, inferencia, commits, merge, push ni deploy en T-0024.
- **Versionado**: prioridad al paquete; R serial. T-0017/T-0020 quedan fuera; antes de retomarlos resolver su version por gate propio, sin downgrade desde 0.4.x.
- **Evidencia**: `deliverables/T-0024.md`; 22 requisitos y pruebas P01-P22 conservados, aprobacion de specs por CLI. El producto sigue pendiente de implementacion.

## DEC-008: Seleccion de entorno Codex / Antigravity y separacion de roles

- **Fecha**: 2026-10-17. **Task**: T-0023. **ADR**: `memory/long/adr/ADR-006-tool-context-models.md`.
- **Autoridad**: instruccion humana de conservar Gemini al usar Antigravity y aplicar las normas acordadas al usar Codex, con actualizacion explicita para evitar ambiguedades. No aprueba SPEC-002 ni su implementacion.
- **Decision**: usar el contexto de herramienta, no sustituir globalmente Gemini por Astra. En Codex, HITL y Coordinator usan la seleccion solicitada GPT-6 Astra / High; los subagentes sin override tienen como predeterminado la misma seleccion del principal. En Antigravity se conserva Gemini 3.8 Flash / High para principal y equipo SDD. La herencia de subagentes Codex es un predeterminado operativo, no una eleccion humana de modelos distintos por rol; cualquier override por task se declara bajo Working Discipline.
- **Fuentes**: `.ies/models.yaml` contiene los bindings activos; `.ies/environment.yaml` declara herramienta y esfuerzo. IES solo tiene un entorno activo por proyecto: la seleccion requiere `ies env set`, no autodetecta la aplicacion. Las recetas exactas de cambio y retorno estan en ADR-006. El Coordinator es el unico escritor de esa configuracion y no la conmuta durante tareas concurrentes; prompts emitidos conservan su contexto y no se reejecutan por un cambio de entorno.
- **Roles**: HITL aclara y transmite instrucciones, no genera tasks. Coordinator crea tasks y prompts canonicos, delega y consolida, no codifica. Planner especifica; Implementer codifica/tests en su worktree; Viewer revisa y hace QA independiente. Todos cumplen SDLC segun contrato, EARS, Clean Code, Clean Architecture y Working Discipline. HITL por gate hasta nueva orden. Multiagentes por task y paralelismo solo con allowlists y worktrees independientes.
- **Capacidad efectiva**: el catalogo IES conserva `native_subagents: false` para Codex. Es metadato descriptivo desactualizado respecto a las delegaciones nativas T-0021/T-0022 observadas; no es prohibicion de usar el transporte disponible ni prueba de aislamiento. La identidad de modelo distinta o no observable se declara NON_BLOCKING; una carencia real de herramienta, permiso o aislamiento conserva sus gates. El YAML no cambia el selector de sesiones abiertas.
- **Producto separado**: el chat de Tri-Coach debe usar exclusivamente GPT-6 Luna / High segun T-0022; esta actualizacion no implementa ese requisito ni cambia produccion.
- **Evidencia**: Codex activado por CLI; compilacion coordinator/planner emite `openai/gpt-6-astra`, High. Retorno Antigravity ensayado por CLI en copia temporal recupera exactamente los bindings previos. Roles no SDD, contratos, proveedores, MLX y 64 archivos de adaptadores/protegidos intactos. No se realizaron inferencias ni evals comparativas de calidad; no se declara equivalencia de calidad ni modelo efectivo de las sesiones. Ver `deliverables/T-0023.md`.

## DEC-001: Aprobación de entrega T-0008 y política estricta contra amend + force-push

- **Fecha**: 2026-10-13
- **Contexto**: El implementer en T-0008 ejecutó `git push --force-with-lease` reemplazando su propio merge `96fceb8` por `7c19924` para incluir `memory/mid/tasks.md` mediante `--amend`, a pesar de que el input de la task prohibía el force-push. No hubo pérdida de información y el merge resultante (`7c19924`) es correcto (padres `e518808` + `b13aa16`, sin conflictos, sin `.lock`, workflow íntegro, PR 1 mergeable en draft).
- **Decisión**: Aprobar la entrega de T-0008 y ratificar la regla operativa: si se requiere corregir un commit ya empujado, se hace con un commit nuevo hacia adelante, nunca con `amend` + `force-push`.

## DEC-002: Corrección del veredicto de T-0009 y estado real de migración en producción (REQ-001, REQ-002)

- **Fecha**: 2026-10-13
- **Contexto**: Tras la entrega de T-0009, la verificación humana contra la API REST de Supabase en producción (utilizando claves anon y service_role) devolvió HTTP 404 `PGRST205` ("Could not find the table 'public.garmin_tokens'"), confirmando que la migración `supabase/migrations/20261011_garmin_tokens.sql` NO fue aplicada en la base de datos de producción (la tabla `public.users` y el usuario FK sí existen, y `daily_snapshots` responde 200). Las tasks T-0002 y T-0005 dieron por aplicada la migración sin haberla verificado efectivamente en el entorno cloud.
- **Consecuencia**: REQ-001 y REQ-002 de SPEC-001 NO se cumplen en producción actualmente. Aunque el merge de PR 1 no rompe el pipeline (el paso de restore cae limpiamente al fallback de contingencia `GARMINTOKENS_B64`), la persistencia automática de tokens (`persist_tokens_to_supabase`) seguiría fallando silenciosamente por los bloques `except Exception: pass` en `garmin_auth.py`.
- **Decisión**: Aprobar el cierre de T-0009 como `done` incorporando esta corrección formal. Condicionar la aprobación formal de SPEC-001 (`ies spec approve`) a la ejecución manual de la migración en producción, la fusión de PR 1 y la verificación en vivo del primer run de `Coaching Daily Collect` con `tokens_persisted: true` y fila creada en `garmin_tokens`.

## DEC-003: Verificación integral en producción de SPEC-001 y aprobación retroactiva

- **Fecha**: 2026-10-13
- **Contexto**: Tras la fusión del PR 1 hacia `master` (commit `0d81139`), se completó la verificación en vivo en el entorno productivo:
  1. **Migración Supabase (REQ-001)**: Aplicada en producción; `service_role` lee `garmin_tokens` con HTTP 200, rol `anon` estrictamente bloqueado en lectura e inserción (HTTP 401).
  2. **Persistencia y Rotación Cloud (REQ-002)**: Run `38450120206` del workflow `coaching-daily-collect.yml` sobre `0d81139` finalizó con éxito (`success`), log reporta `"tokens_persisted": true`, 1 fila persistida en `public.garmin_tokens` para el usuario `00000000-0000-0000-0000-000000000001` (`updated_at: 2026-10-13T18:52Z`, `di_token` presente).
  3. **Sincronización Local (REQ-003)**: Cumple exclusivamente por cobertura de tests unitarios locales. La verificación en vivo desde el Mac queda pendiente hasta el próximo refresh local de sesión Garmin.
  4. **Aplicación Web en Vercel (REQ-004)**: Configurado `Root Directory = apps/web` en el dashboard del proyecto; build y deploy de producción sobre `0d81139` completados con éxito (`Ready`, HTTP 200), reflejando versión `v0.1.0` y datos frescos.
  5. **Manejo Seguro de Errores (REQ-005)**: Confirmada ausencia de tokens o secretos en los logs del runner de Actions; guards de no-sobreescritura protegen la base de datos ante payloads vacíos.
  6. **Observación operativa**: En esta primera corrida, al estar la tabla de Supabase recién creada y vacía, el workflow restauró desde el fallback `GARMINTOKENS_B64`. La restauración primaria desde Supabase entra en vigencia a partir del próximo run (la trazabilidad en log de la fuente de restauración se atiende en T-0010).
- **Decisión**: Declarar formalmente cumplidos en producción los requisitos `REQ-001`, `REQ-002`, `REQ-004` y `REQ-005` (con `REQ-003` cumplido por tests y pendiente de prueba en vivo en el Mac). Autorizar la aprobación oficial de `SPEC-001` mediante `ies spec approve`.
- **Carácter retroactivo**: Se deja constancia de que la aprobación de `SPEC-001` es formalmente retroactiva, dado que las tasks de implementación y verificación inicial (`T-0002` a `T-0007`) se ejecutaron en el ledger antes de que la especificación superara el gate formal de aprobación humana (`ies spec approve`), contraviniendo el orden estricto de SDD.

## DEC-004: Privacidad en logs públicos de CI/CD (Coaching Daily Collect)

- **Fecha**: 2026-10-13
- **Contexto**: El repositorio `dalarconics/python-garminconnect` es público (fork de `cyberjunky`), lo que hace que los logs de ejecución de GitHub Actions sean accesibles públicamente. En `.github/workflows/coaching-daily-collect.yml`, el step `Collect and upsert to Supabase` imprimía en stdout un payload JSON con métricas de salud (`readiness.zone`, `training_load.acwr`, `session.guard_flags`) y el nombre y ubicación geográfica de la última actividad deportiva (`last_activity.name`, ej. "Bogota, D.C. - Base").
- **Decisión**:
  1. El repositorio permanece público.
  2. Los workflows de GitHub Actions tienen estrictamente prohibido imprimir en stdout/stderr datos personales de salud, métricas fisiológicas, nombres de actividad o coordenadas de ubicación.
  3. La salida en logs de CI/CD debe limitarse exclusivamente a metadatos técnicos de ejecución: resultado de la operación (`upsert: ok/fallo`), confirmación técnica de tokens (`tokens_persisted: true/false`), conteos y fuente del token restaurado (`source: supabase` o `source: b64_fallback`).
  4. La auditoría y sanitización de prints/logs aplica a todo el árbol de recolección (`garmin_coaching/`, `services/collector/`, `scripts/garmin_auth.py`).

## DEC-005: Aprobación de entrega T-0012 y verificación de migración updated_at en producción

- **Fecha**: 2026-10-13
- **Contexto**: Se completó la revisión humana de la entrega de `T-0012` ([deliverables/T-0012.md](file:///Users/alarcondiegof/ies-projects/python-garminconnect/deliverables/T-0012.md)) contra el código fuente, la base de datos Supabase y la aplicación web local en viewport 375×812, validando los 8 puntos P1 de [docs/ux-audit-2026-10-13.md](file:///Users/alarcondiegof/ies-projects/python-garminconnect/docs/ux-audit-2026-10-13.md).
- **Verificación en producción**: La migración `supabase/migrations/20261013_updated_at_triggers.sql` fue aplicada exitosamente en la base de datos de producción de Supabase y verificada en vivo: un update sin cambio de datos en la tabla `training_load` avanzó `updated_at` de 16:47:54 a 19:44:42 UTC.
- **Decisión**: Aprobar la entrega de `T-0012`, cerrarla como `done` y autorizar el paso a `T-0013`. Dejar constancia formal verificada de la migración en base de datos para preservar la trazabilidad operacional.

## DEC-006: Adopción del patrón Layered en apps/web y justificación frente a MVVM (Art. VII)

- **Fecha**: 2026-10-14
- **Contexto**: La migración ADR-010 del framework incorporó el Artículo VII en la constitución, exigiendo declarar en `memory/long/standards.md` el patrón arquitectónico (`patron_arquitectonico`) y si el proyecto tiene UI (`tiene_ui`). El Artículo VII.3 exige MVVM para aplicaciones con UI, salvo justificación explícita por ADR en `memory/long/adr/` (Art. VII.4). `ies constitution check` señalaba el hallazgo `VII-07` por tener `patron_arquitectonico: n/a` con tasks de implementer existentes.
- **Decisión**:
  1. Declarar en `memory/long/standards.md`: `patron_arquitectonico: layered` y `tiene_ui: si`.
  2. Aprobar `ADR-001` en `memory/long/adr/ADR-001-patron-layered-apps-web.md`, justificando el uso de una arquitectura por capas (`layered`) en Next.js 15 App Router: páginas Server Components actúan como Vista, `apps/web/lib/` actúa como Modelo y Servicios, y los client components (`CoachChat`, `CoachChatScreen`, `DashboardNav`) conservan estado de vista y orquestación de llamadas en el propio componente.
  3. Criterio de revisión: mover la orquestación de llamadas en componentes de cliente a hooks o `lib/`, y si el estado interactivo del cliente escala significativamente, reevaluar MVVM en un nuevo ADR.
  4. Dejar constancia del cierre formal de `T-0014` (`APROBAR`), aclarando que la medición headless de `/chat` evaluó `/` por redirección de query param en ausencia de `?conversation`, estando el chat interactivo (`CoachChatScreen`) ya validado a 375 px en T-0013.
- **Verificación**: Salida real de `ies constitution check`:
  ```text
  [INFO] II-03 [T-0011]: T-0011 no referencia ninguna spec (heuristica: SPEC-NNN, specs/NNN- o NNN-slug).
  [INFO] III-05: Articulo III.4 (SemVer + CHANGELOG por entrega desplegable, ADR-009) lo verifica el viewer; no es comprobable genericamente.
  [INFO] VII-06 memory/long/standards.md: app con UI y patron 'layered': el Articulo VII.3 exige MVVM (desviacion justificada por ADR).
  constitucion: 0 BLOCKING, 0 NON_BLOCKING, 3 INFO
  ```
  `VII-07` desaparece y la constitución queda en 0 BLOCKING y 0 NON_BLOCKING.


## DEC-007: Aprobacion de ADR-002, Clean Architecture (regla de dependencia) en lugar de `layered`

- **Fecha**: 2026-10-15
- **Contexto**: ADR-018 del framework retira `layered`; `ies constitution check` reportaba VII-04. Instruccion de Diego (chat, 2026-10-15): "puedes hacer un solo lote y ejecutarlo por mi? quiero dedicar mi energia al avance de los proyectos", tras la propuesta que listaba aprobar los ADRs, integrar ramas y ejecutar las tasks de gate.
- **Decision**:
  1. ADR-002 (`memory/long/adr/ADR-002-clean-architecture-regla-de-dependencia.md`) aceptado: `clean-architecture`, `tiene_ui: si`, `patron_presentacion: n/a` (se mantiene la justificacion de ADR-001 y DEC-006), capas Python (`garmin_coaching` dominio) y web (`apps/web/lib` dominio, `app` y `components` presentacion).
  2. Task T-0020 (gate arquitectura: import-linter y dependency-cruiser) autorizada; depende de T-0017.
- **Verificacion**: `ies constitution check`: 0 BLOCKING, 1 NON_BLOCKING (VII-08), VII-06 en INFO por ADR.

## DEC-008: Migracion a ies-os 0.5.0, equipo heredado en Antigravity

- **Fecha**: 2026-10-19
- **Contexto**: ADR-019 del framework (harness heredado). Instruccion de Diego (chat, 2026-10-19): "Mezclé #5 y creé v0.5.0, migra los cinco proyectos". Registrada por el agente en su nombre.
- **Decision**:
  1. El proyecto declara `antigravity` y hereda de `config/team.yaml` el equipo completo: ventana HITL gemini-4-argon (Medium), coordinator, subagentes y especialistas gemini-3.8-flash (High).
  2. Se retira la copia local de bindings `.ies/models.yaml` (ignorada por git; backup en `.ies/backups/`). Los especialistas que usaban el modelo local MLX, gemini-3.5-flash o claude-fable-5 pasan a gemini-3.8-flash.
  3. La constitucion hereda los Articulos I-VII del framework (incluido el II.4, respuestas en caja copiable); sin enmiendas.
  4. Adaptadores solo de Antigravity (`GEMINI.md`, `.agents/`); se eliminan los de otras herramientas generados por IES. El `CLAUDE.md` y el `.vscode/settings.json` propios se conservan.
- **Verificacion**: `ies update`: Equipo HEREDADO, adaptadores al dia; `ies constitution check` sigue con VII-08 NON_BLOCKING hasta T-0020.


## DEC-009: Lint heredado de master primero; replanificacion de T-0011, T-0017, T-0018 y T-0020

- **Fecha**: 2026-10-20
- **Contexto**: CI de `master` en rojo desde 2026-09-22: ruff 0.17.1 reporta 107 errores (todos en `garmin_coaching/`, `services/`, `scripts/`, `garmin_mcp/`) y `ruff format --check` 25 archivos, asi que pytest no llega a correr. T-0011 (backlog) cubria el trabajo, pero el CLI no permite `backlog -> ready`, y su sucesora solapaba con T-0017 (ready, rama local `task/T-0017` f3fc13a sin subir, version 0.3.1 caducada) y T-0020 (ready, depende de T-0017). Instrucciones de Diego (chat, 2026-10-20): "Ok, adelante con T-0011 y quita el pie de los PR" y, ante el solape, "Ok, adelante con A". Registrada por el agente en su nombre.
- **Decision**:
  1. Se cancelan T-0011, T-0017, T-0018 (viewer de T-0017) y T-0020, con razon.
  2. T-0039 (sucesora de T-0011): ruff y formato limpios sin cambio de comportamiento, per-file-ignores D101/D103 para el codigo de la app, version 0.5.2 PATCH.
  3. T-0040 recoge lo pendiente de T-0017 (logging en `login_client`, aviso de persistencia, origen del restore, deploy script, DEC-004, pruebas web sin skips); depende de T-0039. La rama `task/T-0017` se conserva como referencia.
  4. T-0041 recrea T-0020 identica; depende de T-0040 (ambas tocan `apps/web/package.json`).
  5. Commits y PR sin atribucion a IA (CLAUDE.md del repo); se retiro el pie "Generated with Claude Code" de los PR #3, #4 y #5. Los trailers ya mezclados en `master` (e406900, 546d94e, 0b57777) no se reescriben.
- **Verificacion**: `ies task list`: T-0039, T-0040 y T-0041 en ready, encadenadas; T-0011, T-0017, T-0018 y T-0020 canceladas.
