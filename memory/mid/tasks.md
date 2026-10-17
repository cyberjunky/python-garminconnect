---
schema_version: 1
project_id: python-garminconnect
next_id: 39
source: ies-cli
last_updated: '2026-10-17T17:49:19Z'
---

# Task Ledger

## T-0001 — Especificar y planificar recurring-token-sync

```yaml
id: T-0001
title: Especificar y planificar recurring-token-sync
project_id: python-garminconnect
origin: human
destination: planner
status: done
input: Revisar y actualizar app en Vercel, solucionar actualizacion recurrente del
  token Garmin con sincronizacion automatica y despliegue
expected_output: specs/001-recurring-token-sync/{spec.md,plan.md} completas con EARS
  y descomposicion en tasks
parent_task: null
dependencies: []
priority: medium
profile: riguroso
autonomy: autonomous
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
acceptance_criteria:
- spec.md con REQ EARS y plan.md con tasks y matriz de trazabilidad
allowlist: []
created_at: '2026-10-11T15:54:12Z'
started_at: '2026-10-11T16:01:26Z'
completed_at: '2026-10-11T16:01:26Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0001.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  git_after: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  result: success
edits: []
```

## T-0002 — Migracion Supabase garmin_tokens y adaptadores Python

```yaml
id: T-0002
title: Migracion Supabase garmin_tokens y adaptadores Python
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: Crear migracion SQL para garmin_tokens con RLS service_role y funciones en
  services/collector/supabase_client.py y scripts/garmin_auth.py con tests unitarios
expected_output: Migracion SQL, adaptadores de lectura/escritura de tokens en Supabase
  y tests unitarios pasando
parent_task: T-0001
dependencies: []
priority: medium
profile: riguroso
autonomy: autonomous
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- tests unitarios para sincronizacion de tokens con Supabase pasando sin regresiones
allowlist: []
created_at: '2026-10-11T16:01:36Z'
started_at: '2026-10-11T17:04:17Z'
completed_at: '2026-10-11T17:04:17Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0002.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  git_after: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  result: success
edits: []
```

## T-0003 — Actualizar workflow GitHub Actions y scripts de sincronizacion

```yaml
id: T-0003
title: Actualizar workflow GitHub Actions y scripts de sincronizacion
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: Actualizar coaching-daily-collect.yml, publish_garmin_tokens_secret.sh y refresh_garmin_session.py
  para sincronizar tokens bidireccionalmente con Supabase y GitHub Secrets
expected_output: Workflow y scripts actualizados con persistencia automatica en Supabase
  y verificacion
parent_task: T-0001
dependencies:
- T-0002
priority: medium
profile: riguroso
autonomy: autonomous
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- coaching-daily-collect.yml y scripts locales integrados con persistencia en Supabase
  y verificados
allowlist: []
created_at: '2026-10-11T17:04:26Z'
started_at: '2026-10-11T17:09:54Z'
completed_at: '2026-10-11T17:09:54Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0003.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  git_after: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  result: success
edits: []
```

## T-0004 — Build, validacion y despliegue a produccion de apps/web en Vercel

```yaml
id: T-0004
title: Build, validacion y despliegue a produccion de apps/web en Vercel
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: Compilar, verificar y desplegar apps/web a produccion en Vercel, validando
  que el sitio responda HTTP 200 y muestre version y datos frescos
expected_output: Deploy exitoso a produccion en Vercel con URL verificada y estado
  HTTP 200
parent_task: T-0001
dependencies:
- T-0003
priority: medium
profile: riguroso
autonomy: autonomous
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- deploy en Vercel completado exitosamente y URL de produccion respondiendo 200 con
  datos actualizados
allowlist: []
created_at: '2026-10-11T17:10:01Z'
started_at: '2026-10-11T17:13:58Z'
completed_at: '2026-10-11T17:13:58Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0004.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  git_after: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  result: success
edits: []
```

## T-0005 — Verificacion integral SDD SPEC-001

```yaml
id: T-0005
title: Verificacion integral SDD SPEC-001
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: 'Verificar integralmente los requisitos EARS de SPEC-001: REQ-001 a REQ-005,
  pruebas unitarias, seguridad RLS y despliegue Vercel'
expected_output: Reporte de revision independiente en deliverables/T-0005.md con veredicto
  formal
parent_task: T-0001
dependencies:
- T-0004
priority: medium
profile: riguroso
autonomy: autonomous
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- todos los requisitos de SPEC-001 verificados con pruebas y sin hallazgos BLOCKING
allowlist: []
created_at: '2026-10-11T17:14:07Z'
started_at: '2026-10-11T17:18:02Z'
completed_at: '2026-10-11T17:18:02Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0005.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  git_after: 630e50ed0dcdf82e02a575e2cd7781afea06333b
  result: success
edits: []
```

## T-0006 — Corregir soporte de temperature para modelos reasoning en /api/chat

```yaml
id: T-0006
title: Corregir soporte de temperature para modelos reasoning en /api/chat
project_id: python-garminconnect
origin: human
destination: implementer
status: done
input: Ajustar /api/chat para omitir temperature en modelos reasoning/sol y manejar
  fallback sin 502
expected_output: apps/web corregido, pruebas de chat validadas y redeploy exitoso
  a Vercel
parent_task: null
dependencies: []
priority: high
profile: riguroso
autonomy: autonomous
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- chat funcional con gpt-6.1-sol y modelos tradicionales sin error 502
allowlist: []
created_at: '2026-10-11T17:28:29Z'
started_at: '2026-10-11T17:35:00Z'
completed_at: '2026-10-11T17:35:00Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0006.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: d73e40e2fb7e0ba041bf95c1256c4490172b1f21
  git_after: d73e40e2fb7e0ba041bf95c1256c4490172b1f21
  result: success
edits: []
```

## T-0007 — Verificacion independiente de correccion de temperature en produccion

```yaml
id: T-0007
title: Verificacion independiente de correccion de temperature en produccion
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: Verificar de forma independiente que /api/chat en produccion responda 200 con
  modelos reasoning (gpt-6.1-sol) y estandar (gpt-4o-mini), sin errores de temperature
  ni regresiones
expected_output: Reporte de verificacion viewer en deliverables/T-0007.md sin hallazgos
  BLOCKING
parent_task: T-0006
dependencies: []
priority: high
profile: riguroso
autonomy: autonomous
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- comprobacion independiente de /api/chat en vivo sin errores 502
allowlist: []
created_at: '2026-10-11T17:35:10Z'
started_at: '2026-10-11T17:36:39Z'
completed_at: '2026-10-11T17:36:39Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0007.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: d73e40e2fb7e0ba041bf95c1256c4490172b1f21
  git_after: d73e40e2fb7e0ba041bf95c1256c4490172b1f21
  result: success
edits: []
```

## T-0008 — Resolver conflicto del PR 1 con master y sincronizar rama

```yaml
id: T-0008
title: Resolver conflicto del PR 1 con master y sincronizar rama
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: En la rama cursor/shell-chat-hoy-43bc, hacer git fetch origin y fusionar origin/master
  (merge commit, no rebase ni force-push). Resolver el conflicto en .github/workflows/coaching-daily-collect.yml
  conservando la version de la rama (ya incluye last_activity de b13aa16). Correr
  .venv/bin/python -m pytest -q tests y reportar la falla esperada de macOS (test_absolute_path_outside_home_still_allowed
  por /var -> /private/var) sin tocar codigo ni tests. Commit y push a cursor/shell-chat-hoy-43bc
  sin atribucion a IA en el mensaje (CLAUDE.md). Mantener PR 1 en draft y no fusionar.
expected_output: deliverables/T-0008.md con log de merge, hash del commit resultante
  en la rama, salida de pytest y confirmacion de push
parent_task: null
dependencies: []
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Rama cursor/shell-chat-hoy-43bc sincronizada con origin/master sin conflictos y
  con push exitoso
- Suite pytest ejecutada con solo la falla conocida de symlink de macOS reportada
- Commit sin atribucion a IA y PR 1 conservado en draft sin merge
allowlist: []
created_at: '2026-10-13T17:00:48Z'
started_at: '2026-10-13T17:15:31Z'
completed_at: '2026-10-13T17:15:31Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0008.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 7c19924433e57af70526cd418f3660445f92af65
  git_after: 7c19924433e57af70526cd418f3660445f92af65
  result: success
edits: []
```

## T-0009 — Verificacion viewer diff SPEC-001 y checklist pre-merge PR 1

```yaml
id: T-0009
title: Verificacion viewer diff SPEC-001 y checklist pre-merge PR 1
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: 'Inspeccionar el diff completo origin/master...7c19924433e57af70526cd418f3660445f92af65
  (hash reportado en deliverables/T-0008.md) contra REQ-001..REQ-005 de SPEC-001 con
  veredicto por requisito. Auditar si GARMINTOKENS: ~/.garminconnect en el workflow
  se expande con expanduser o requiere $HOME. Auditar REQ-005 (fallo de login no sobreescribe
  tokens en Supabase ni fuga secretos; || true en restore no oculta fallos reales).
  Auditar migracion supabase/migrations/20261011_garmin_tokens.sql (RLS y anon bloqueado;
  reportar como pendiente si no se puede verificar en prod). Si falta apps/web/node_modules,
  correr npm --prefix apps/web ci antes del build y registrarlo en la entrega; validar
  npm --prefix apps/web run build. Auditar fallo del check Vercel del PR (dpl_CtnDJBtHAv4jWqfEtSFbCJYkTcWj:
  ENOENT en raiz /vercel/path0/package.json por Root Directory != apps/web en configuracion
  del proyecto Vercel) y clasificar si es BLOCKING o NON_BLOCKING para el merge (la
  configuracion en Vercel la ajusta el humano). Confirmar resultado de los checks
  test (3.12) y test (3.13) de GitHub Actions sobre 7c19924. Solo lectura: no corregir
  codigo.'
expected_output: deliverables/T-0009.md con matriz de requisitos, evaluacion tecnica
  de env y seguridad, estado de checks de CI/Vercel y lista de hallazgos BLOCKING
  y NON_BLOCKING
parent_task: null
dependencies:
- T-0008
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Revision exhaustiva de REQ-001 a REQ-005 sobre el commit 7c19924 con veredicto por
  requisito
- Dictamen tecnico de GARMINTOKENS (~ vs $HOME) y auditoria de REQ-005 / migracion
  Supabase
- Build de apps/web ejecutado (con ci si faltaba node_modules) y reportado con codigo
  0
- Evaluacion y clasificacion (BLOCKING/NON_BLOCKING) del check de Vercel y confirmacion
  de checks test (3.12/3.13) sobre 7c19924
- Entrega en deliverables/T-0009.md en modo solo lectura sin mutaciones en el repositorio
allowlist: []
created_at: '2026-10-13T17:00:58Z'
started_at: '2026-10-13T18:35:11Z'
completed_at: '2026-10-13T18:35:11Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0009.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 7c19924433e57af70526cd418f3660445f92af65
  git_after: 7c19924433e57af70526cd418f3660445f92af65
  result: success
edits: []
```

## T-0010 — Saneamiento linter SPEC-001, observabilidad REQ-005, trazabilidad de restore y ajuste deploy script

```yaml
id: T-0010
title: Saneamiento linter SPEC-001, observabilidad REQ-005, trazabilidad de restore
  y ajuste deploy script
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: cancelled
input: '1. Corregir los 9 errores de ruff introducidos por SPEC-001 en scripts/garmin_auth.py
  y services/collector/supabase_client.py. 2. Sustituir bloques except Exception:
  pass en scripts/garmin_auth.py:login_client por logging explicito _LOGGER.warning
  (REQ-005). 3. Registrar en los logs del workflow .github/workflows/coaching-daily-collect.yml
  de donde se restauro el token (supabase | b64_fallback). 4. Ajustar scripts/deploy_web_vercel.sh
  para alinearlo con Root Directory = apps/web configurado en Vercel.'
expected_output: deliverables/T-0010.md con diffs de ruff, logging implementado, salida
  de trazabilidad de restore y scripts validados
parent_task: null
dependencies: []
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 0 errores de ruff en scripts/garmin_auth.py y services/collector/supabase_client.py
- Excepciones en login_client logueadas con _LOGGER.warning
- Workflow reporta en log la fuente de restauracion del token (supabase | b64_fallback)
- scripts/deploy_web_vercel.sh verificado y funcional con Root Directory de Vercel
allowlist: []
created_at: '2026-10-13T19:00:10Z'
started_at: null
completed_at: '2026-10-13T19:38:05Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  cancel_reason: reemplazada por T-0015 con alcance ampliado (DEC-004)
edits: []
```

## T-0011 — Estrategia y resolución de 97 errores de linter heredados de master

```yaml
id: T-0011
title: Estrategia y resolución de 97 errores de linter heredados de master
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: backlog
input: Analizar y definir la estrategia para subsanar los 97 errores de ruff heredados
  de master en scripts y servicios historicos (evaluar correccion en codigo vs configuracion
  de per-file-ignores en pyproject.toml), de modo que los jobs test (3.12) y test
  (3.13) en GitHub Actions puedan ejecutar pytest exitosamente en CI.
expected_output: deliverables/T-0011.md con estrategia ejecutada, ruff limpio en CI
  y pytest corriendo en GitHub Actions
parent_task: null
dependencies: []
priority: medium
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Jobs test (3.12) y test (3.13) en GitHub Actions ejecutando pytest sin ser bloqueados
  por linter
allowlist: []
created_at: '2026-10-13T19:00:15Z'
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

## T-0012 — Correccion de datos P1 y responsive movil en apps/web y backend

```yaml
id: T-0012
title: Correccion de datos P1 y responsive movil en apps/web y backend
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: 'Trabajar en la rama ux/audit-2026-10 (creada desde master) con PR a master.
  Sin force-push (DEC-001). Implementar seccion P1 de docs/ux-audit-2026-10-13.md:
  1. Hora de ultima actividad: en apps/web/lib/lastActivity.ts:40 formatear hora local
  sin desfase de 5h. 2. updated_at: ajustar services/collector/supabase_client.py
  y entregar migracion SQL idempotente (create or replace / drop trigger if exists)
  para tablas con upsert, lista para SQL Editor de Supabase. 3. BB delta con signo:
  en apps/web/app/(dashboard)/page.tsx:73 evitar +-12. 4. Tarjeta recuperacion: en
  apps/web/components/RecoveryMilestonesCard.tsx usar fase de payload.macrocycle y
  quitar meta fija si no viene en datos. 5. Fecha local Bogota: en app/(dashboard)/mesociclos/page.tsx:9,
  app/(dashboard)/page.tsx:42 y app/(dashboard)/retos/page.tsx:30 calcular fecha en
  zona Bogota en vez de UTC. 6. Menu movil: en globals.css sustituir barra sticky
  de 336px por navegacion compacta (<15% altura) con z-index correcto. 7. PreparationChart:
  min-width con scroll o version movil legible en 375px. 8. Layout: color-scheme:
  dark y theme-color. Tests donde aplique y verificacion visual 375x812.'
expected_output: deliverables/T-0012.md con diffs, script SQL idempotente, tests pasando
  y reporte de verificacion visual movil
parent_task: null
dependencies: []
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Hora de ultima actividad sin desfase horario
- Script SQL idempotente para updated_at en tablas con upsert generado
- Formato BB delta sin +- y fechas de dashboard calculadas en zona horaria Bogota
- Fase de recuperacion dinamica segun payload.macrocycle sin meta inventada
- Menu movil compacto (<15% altura) y grafica legible en 375x812
allowlist: []
created_at: '2026-10-13T19:20:22Z'
started_at: '2026-10-13T19:45:56Z'
completed_at: '2026-10-13T19:45:56Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0012.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: c1250438e8b77dc315913ae3d321eb0d7e195d06
  git_after: c1250438e8b77dc315913ae3d321eb0d7e195d06
  result: success
edits: []
```

## T-0013 — Accesibilidad P2, copy en espanol, consistencia UI y marca Tri-Coach P3

```yaml
id: T-0013
title: Accesibilidad P2, copy en espanol, consistencia UI y marca Tri-Coach P3
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: 'Trabajar en la rama ux/audit-2026-10 (creada desde master) con PR a master.
  Sin force-push (DEC-001). Implementar decisiones de producto y secciones P2 y P3
  de docs/ux-audit-2026-10-13.md: 1. Marca Tri-Coach en layout, nav, paginas y metadatos.
  2. Jerarquia en Inicio: tarjeta Hoy antes que el chat en app/(dashboard)/page.tsx.
  3. Accesibilidad (P2): anillo :focus-visible global y focus-within en compositor;
  labels/aria-label en textareas de chat; aria-current=''page'' en enlace activo;
  h1 en Inicio y salto a contenido; alertas con icono/texto ademas de color; role=''alert''
  en errores de chat; prefers-reduced-motion. 4. Copy y consistencia (P3): copy unificado
  al espanol sin terminos en ingles crudos; eliminar mensajes de debug para desarrolladores
  en UI; fechas con Intl.DateTimeFormat(''es-CO'') y etiqueta amigable de actualizacion;
  tabular-nums; router.push en vez de window.location.assign; consolidar estilos y
  colores en clases y tokens CSS.'
expected_output: deliverables/T-0013.md con diffs, validacion de build limpio npm
  --prefix apps/web run build y evidencia de accesibilidad
parent_task: null
dependencies:
- T-0012
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Marca Tri-Coach aplicada y tarjeta Hoy antes del chat en Inicio
- Navegacion por teclado y foco 100% visible con aria-current, labels y alerts
- Copy en espanol consistente sin mensajes de debug expuestos
- Cifras y tablas con tabular-nums y fechas en formato es-CO
- npm --prefix apps/web run build finaliza con codigo 0
allowlist: []
created_at: '2026-10-13T19:20:50Z'
started_at: '2026-10-13T20:27:29Z'
completed_at: '2026-10-13T20:27:29Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0013.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: cf19c10adfa1917b33200709b51f5f34f650c5ca
  git_after: cf19c10adfa1917b33200709b51f5f34f650c5ca
  result: success
edits: []
```

## T-0014 — Verificacion viewer independiente de UX/UI P1-P3 y SemVer 0.3.0 (Local 1280x800 y 375x812)

```yaml
id: T-0014
title: Verificacion viewer independiente de UX/UI P1-P3 y SemVer 0.3.0 (Local 1280x800
  y 375x812)
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: 'Verificacion en modo solo lectura de las implementaciones de T-0012, T-0013
  y T-0016 en la app local levantada con npm --prefix apps/web run build && npm --prefix
  apps/web run start (el preview de Vercel pide login 302 y lo revisa el humano a
  mano). Verificar de forma exhaustiva en dos resoluciones: escritorio (1280x800)
  y movil (375x812). Auditar resolucion de items P1 (hora actividad, updated_at, BB
  delta, recuperacion dinamica, fecha Bogota, menu movil, grafica 375px, dark theme),
  items P2 (foco visible, labels, aria-current, h1, alertas con texto/icono, role
  alert, reduced motion), items P3 (copy espanol, fechas Intl, tabular-nums, marca
  Tri-Coach, tarjeta Hoy antes de chat) y versionado SemVer 0.3.0 (package.json, package-lock.json,
  version en sidebar, CHANGELOG.md y README.md). Comprobar tests unitarios, ausencia
  de errores de consola y regresiones.'
expected_output: deliverables/T-0014.md con matriz de verificacion en 1280x800 y 375x812,
  evidencia funcional y veredicto formal APROBAR / RECHAZAR
parent_task: null
dependencies:
- T-0012
- T-0013
- T-0016
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Verificacion local documentada en resoluciones 1280x800 y 375x812
- Comprobacion exhaustiva de todos los puntos de P1, P2 y P3 del informe docs/ux-audit-2026-10-13.md
- Comprobacion de version 0.3.0 en sidebar/package.json y apps/web/CHANGELOG.md
- Veredicto formal emitido en modo solo lectura sin mutaciones en el repositorio
allowlist: []
created_at: '2026-10-13T19:21:00Z'
started_at: '2026-10-14T15:17:58Z'
completed_at: '2026-10-14T15:17:58Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0014.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 828f3075fc9c4467c2e4a34f96d3535395ad9e5f
  git_after: 828f3075fc9c4467c2e4a34f96d3535395ad9e5f
  result: success
edits: []
```

## T-0015 — Saneamiento linter SPEC-001, observabilidad REQ-005, deploy script y privacidad de logs CI

```yaml
id: T-0015
title: Saneamiento linter SPEC-001, observabilidad REQ-005, deploy script y privacidad
  de logs CI
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: cancelled
input: 'Trabajar en la rama chore/lint-logs-2026-10 (creada desde master tras merge
  de UX) con PR a master. 1. Corregir los 10 errores de ruff en el alcance de SPEC-001/UX
  (9 introducidos en SPEC-001 mas UP017 en services/collector/supabase_client.py:28
  introducido en T-0012; el total de CI reporta 107 con los 97 heredados de master)
  en scripts/garmin_auth.py y services/collector/supabase_client.py. 2. Sustituir
  bloques except Exception: pass en scripts/garmin_auth.py:login_client por logging
  explicito _LOGGER.warning (REQ-005). 3. Registrar en logs del workflow de donde
  se restauro el token (supabase | b64_fallback). 4. Ajustar scripts/deploy_web_vercel.sh
  para Root Directory = apps/web de Vercel. 5. Recortar salida de workflows (DEC-004):
  en coaching-daily-collect.yml el JSON final solo puede incluir upsert ok/fallo,
  tokens_persisted y fuente del restore (supabase | b64_fallback); quitar zone, acwr,
  guards y last_activity. Revisar que ningun otro print o log del collector (garmin_coaching/,
  services/collector/, scripts/garmin_auth.py) emita metricas, nombres de actividad
  ni coordenadas a stdout en Actions.'
expected_output: deliverables/T-0015.md con diffs de ruff, logging implementado, salida
  de trazabilidad de restore, sanitizacion de logs de Actions y scripts validados
parent_task: null
dependencies: []
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 0 errores de ruff en scripts/garmin_auth.py y services/collector/supabase_client.py
- Excepciones en login_client logueadas con _LOGGER.warning
- Workflow reporta en log la fuente de restauracion del token (supabase | b64_fallback)
- scripts/deploy_web_vercel.sh verificado y funcional con Root Directory de Vercel
- El log de un run de Coaching Daily Collect no contiene metricas de salud, nombres
  de actividad ni ubicacion; verificado en el log de un run real despues del merge.
allowlist: []
created_at: '2026-10-13T19:38:13Z'
started_at: null
completed_at: '2026-10-14T15:19:03Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: null
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  cancel_reason: reemplazada por T-0017 para cumplir nuevo contrato (allowlist ADR-012,
    SemVer 0.3.1 ADR-009 y worktree)
edits: []
```

## T-0016 — Versionado SemVer 0.3.0 y CHANGELOG de Tri-Coach (apps/web)

```yaml
id: T-0016
title: Versionado SemVer 0.3.0 y CHANGELOG de Tri-Coach (apps/web)
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: 'Trabajar en la rama ux/audit-2026-10 (viaja dentro del PR #2). Sin force-push
  (DEC-001). 1. Adoptar SemVer para Tri-Coach; la version vive en apps/web/package.json
  y apps/web/package-lock.json (MINOR por PR de funcionalidad, PATCH por correcciones).
  2. Crear apps/web/CHANGELOG.md (formato Keep a Changelog, en espanol), cuyo encabezado
  aclare que cubre todo Tri-Coach (app web, collector Python, workflows de GitHub
  Actions y esquema Supabase), no solo apps/web. Historia retroactiva desde git log:
  - 0.1.0 (2026-09-20..25): MVP dashboard, collect diario, grafica de preparacion,
  mesociclos, 70.3 Cartagena. - 0.2.0 (2026-10-13, PR #1, merge 0d81139): shell con
  barra lateral, chat con OpenAI, boton Actualizar (workflow_dispatch), persistencia
  de ultima actividad Garmin (commit b13aa16 del 3-oct) y tokens Garmin en Supabase
  (SPEC-001). - 0.3.0 (PR #2): auditoria UX P1-P3 (T-0012, T-0013), marca Tri-Coach,
  triggers updated_at. 3. Subir apps/web/package.json y apps/web/package-lock.json
  a 0.3.0 (usando npm --prefix apps/web install --package-lock-only o equivalente).
  4. Actualizar apps/web/README.md con seccion ''Version y cambios'' (version actual,
  regla SemVer, enlace a CHANGELOG.md). No tocar el README.md raiz. 5. En deliverables/T-0016.md
  proponer los tags para que los cree el humano: tri-coach-v0.1.0 (commit 102430e),
  tri-coach-v0.2.0 (0d81139) y tri-coach-v0.3.0 (merge de PR #2). El agente no crea
  ni empuja tags. 6. Commit nuevo hacia adelante en ux/audit-2026-10 sin amend ni
  force-push.'
expected_output: deliverables/T-0016.md con diffs, apps/web/CHANGELOG.md creado, package.json
  y package-lock.json en 0.3.0, README.md actualizado, barra lateral mostrando v0.3.0
  y propuesta de tags git
parent_task: null
dependencies:
- T-0013
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- apps/web/package.json y package-lock.json en version 0.3.0 con build limpio
- apps/web/CHANGELOG.md creado en espanol cubriendo 0.1.0, 0.2.0 (con b13aa16) y 0.3.0,
  aclarando cobertura integral del stack
- apps/web/README.md con seccion 'Version y cambios' y enlace a CHANGELOG sin tocar
  el README raiz
- La barra lateral del dashboard muestra v0.3.0 verificada en local
- Propuesta de tags git documentada en la entrega sin creacion de tags por el agente
  y commit nuevo en ux/audit-2026-10
allowlist: []
created_at: '2026-10-13T20:36:46Z'
started_at: '2026-10-13T23:00:20Z'
completed_at: '2026-10-13T23:00:20Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0016.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 6093d34d0fc90394826889b09c0910eec5421120
  git_after: 6093d34d0fc90394826889b09c0910eec5421120
  result: success
edits: []
```

## T-0017 — Saneamiento linter SPEC-001, privacidad logs CI, deploy script y SemVer 0.3.1

```yaml
id: T-0017
title: Saneamiento linter SPEC-001, privacidad logs CI, deploy script y SemVer 0.3.1
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: ready
input: 'Trabajar en el worktree .ies/worktrees/T-0017 creado desde master (despues
  del merge del PR #2). El implementer no hace push ni abre PR; el humano empuja la
  rama y abre el PR. 1. Corregir los 10 errores de ruff en el alcance de SPEC-001/UX
  (9 de SPEC-001 mas UP017 en services/collector/supabase_client.py:28 introducido
  en T-0012) en scripts/garmin_auth.py y services/collector/supabase_client.py. 2.
  Sustituir bloques except Exception: pass en scripts/garmin_auth.py:login_client
  por logging explicito _LOGGER.warning (REQ-005). 3. Registrar en logs del workflow
  de donde se restauro el token (supabase | b64_fallback). 4. Ajustar scripts/deploy_web_vercel.sh
  para Root Directory = apps/web de Vercel. 5. Recortar salida de workflows (DEC-004):
  en coaching-daily-collect.yml el JSON final solo puede incluir upsert ok/fallo,
  tokens_persisted y fuente del restore (supabase | b64_fallback); quitar zone, acwr,
  guards y last_activity. Revisar que ningun otro print o log del collector (garmin_coaching/,
  services/collector/, scripts/garmin_auth.py) emita metricas, nombres de actividad
  ni coordenadas a stdout en Actions. 6. Versionado SemVer 0.3.1 (PATCH, ADR-009):
  al modificar el collector y el workflow de produccion, subir apps/web/package.json
  y apps/web/package-lock.json a 0.3.1 con entrada en apps/web/CHANGELOG.md.'
expected_output: deliverables/T-0017.md con diffs de ruff, logging implementado, trazabilidad
  de restore, sanitizacion de logs Actions, scripts validados y bump a 0.3.1
parent_task: null
dependencies: []
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 0 errores de ruff en scripts/garmin_auth.py y services/collector/supabase_client.py
- Excepciones en login_client logueadas con _LOGGER.warning
- Workflow reporta en log la fuente de restauracion del token (supabase | b64_fallback)
- scripts/deploy_web_vercel.sh verificado y funcional con Root Directory de Vercel
- El log de un run de Coaching Daily Collect no contiene metricas de salud, nombres
  de actividad ni ubicacion; verificado en el log de un run real despues del merge.
- Bump SemVer a 0.3.1 en package.json y package-lock.json con entrada en apps/web/CHANGELOG.md
  (ADR-009)
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
created_at: '2026-10-14T15:19:18Z'
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

## T-0018 — Verificacion viewer independiente de T-0017 sobre commit f3fc13a

```yaml
id: T-0018
title: Verificacion viewer independiente de T-0017 sobre commit f3fc13a
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: ready
input: 'Auditar en modo solo lectura el commit exacto f3fc13a1bf5aa0490687882c1d89e04be176ca91
  en .ies/worktrees/T-0017 (referenciando la entrega deliverables/T-0017.md de T-0017
  sin marcarla done). Revisar todos los criterios de T-0017 y reproducir rigurosamente:
  1. Cumplimiento estricto de allowlist con ies git verify --task T-0017. 2. Tres
  pruebas web omitidas con --test-skip-pattern en apps/web/package.json. 3. Dos fallos
  al correr node --test lib/*.test.mjs sin filtro. 4. Ruff distinto de cero: 10 errores
  en scripts/garmin_auth.py y services/collector/supabase_client.py (sin rebajar a
  NON_BLOCKING por considerarlos legacy si el criterio contractual exigia 0 errores)
  mas los 2 errores de Ruff en el test nuevo tests/test_collector_privacy_and_resilience.py
  (I001, SIM108). 5. Excepcion sin sanitizar en warnings de login_client (%s, exc).
  6. Persistencia fallida sin warning (persist_tokens_to_supabase retorna False sin
  elevar, dejando inactivo el try/except de login_client). 7. Afirmaciones incorrectas
  del entregable deliverables/T-0017.md (afirma 0 errores de ruff y omite el skip
  de tests web). 8. En SDLC, evaluar si el procedimiento preparado para despliegue
  satisface el contrato sin calificarlo falso por no ejecutar el deploy, conservando
  como pendientes las comprobaciones reales en produccion (run real de Actions post-merge
  y despliegue efectivo en Vercel). Emitir veredicto canonico APROBAR | CORREGIR |
  BLOQUEAR.'
expected_output: deliverables/T-XXXX.md con matriz de verificacion de criterios de
  T-0017, reproduccion de hallazgos tecnicos, clasificacion formal de severidad y
  veredicto APROBAR | CORREGIR | BLOQUEAR
parent_task: null
dependencies: []
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- Revision independiente en solo lectura del commit f3fc13a sin mutaciones en el repositorio
- Auditoria de allowlist (ies git verify) y reproduccion de las 3 pruebas omitidas
  y 2 fallos web sin filtro
- Auditoria de Ruff en modulos del recolector (10 errores) y en el test nuevo (2 errores)
- Auditoria de manejo de excepciones y warnings en persist_tokens_to_supabase y login_client
- Auditoria de veracidad del entregable, evaluacion de procedimiento de despliegue
  y validaciones pendientes en produccion
- Veredicto canonico formal (APROBAR | CORREGIR | BLOQUEAR) con clasificacion de severidad
allowlist: []
created_at: '2026-10-14T16:44:27Z'
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

## T-0020 — Gate arquitectura: import-linter y dependency-cruiser (ADR-002)

```yaml
id: T-0020
title: 'Gate arquitectura: import-linter y dependency-cruiser (ADR-002)'
project_id: python-garminconnect
origin: human
destination: implementer
status: ready
input: 'Python: anadir import-linter a las dependencias de desarrollo en pyproject.toml
  y un archivo .importlinter con el contrato ''garmin_coaching independiente de garminconnect,
  services, supabase, fastapi, requests'' (ADR-002 §2 y §5). Web: anadir dependency-cruiser
  en apps/web/package.json con apps/web/.dependency-cruiser.cjs que prohiba que lib/**
  (salvo lib/infra/**) importe @supabase/* u openai (ADR-002 §3). Registrar en .ies/gate.yaml
  dos comandos cuyo nombre contenga ''arquitectura'' (lint-imports; npx depcruise
  en apps/web), sdlc: pruebas. No mover supabase.ts ni openaiModels.ts: si hoy violan
  la regla, el contrato web los exime por ruta y se anota como deuda en el deliverable.
  Depende de T-0017 porque ambas tocan apps/web/package.json.'
expected_output: Ambos linters en verde, comandos de arquitectura en .ies/gate.yaml,
  ies constitution check sin VII-08 y deliverable con la salida del gate y la deuda
  registrada.
parent_task: null
dependencies:
- T-0017
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
created_at: '2026-10-15T10:07:27Z'
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

## T-0025 — I-UI: Centrado responsive en Safari y SemVer 0.4.0-rc.1 (SPEC-002)

```yaml
id: T-0025
title: 'I-UI: Centrado responsive en Safari y SemVer 0.4.0-rc.1 (SPEC-002)'
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: 'Ejecutar exclusivamente la etapa I-UI (G2) de specs/002-layout-responsive/{spec.md,plan.md}
  aprobados en DEC-009 (propuesta T-0022, propuesta cerrada en deliverables/T-0024.md),
  trabajando estrictamente dentro del worktree aislado .ies/worktrees/T-0025 desde
  el baseline de codigo aeaa5da9a02c0070cb4f4259da13f1cb27ba16ab. 1. Orden tests-first:
  escribir primero pruebas automatizadas en apps/web/lib/layout-responsive.test.mjs
  (y/o apps/web/tests/layout-responsive/) que fallen ante el defecto de centrado/geometria
  y verifiquen la regla de dependencia de archivos tocados (P22), luego aplicar la
  correccion minima en apps/web/app/globals.css (y apps/web/app/(dashboard)/layout.tsx
  solo si es necesario) para centrar el contenedor del dashboard en su area disponible
  (.app-main) con max-width 1120px y padding 28px (>800px) / 16px (<=800px), preservando
  el layout independiente del chat (compositor max 880px centrado y burbujas por rol).
  2. Actualizar la version candidata a 0.4.0-rc.1 en apps/web/package.json, ambos
  niveles de apps/web/package-lock.json, apps/web/lib/version.test.mjs, apps/web/README.md
  y apps/web/CHANGELOG.md, sin anadir dependencias nuevas. 3. Levantar servidor local
  aislado con fixtures sinteticas (sin consultar ni escribir en servicios reales,
  sin inferencia cloud ni tocar datos de usuario) y ejecutar en Safari real las mediciones
  de las 14 celdas de la matriz S (SPEC-002 seccion 5: cuatro rutas dashboard y chat
  a 375px y 1600px, mas Inicio y chat a 800px y 801px), verificando P01 (desvio de
  ancho/padding <=2px, diferencia de margenes izq/der <=2px), P02 (overflow horizontal
  global <=1px, controles accesibles, scroll interno de graficas intacto) y P03 (ciclo
  de navegacion dashboard -> chat con ID -> historial -> chat -> volver a 375px y
  1600px). Guardar las capturas requeridas y mediciones en deliverables/evidence/T-0025/.
  4. Ejecutar npm --prefix apps/web test, npm --prefix apps/web run build e IES_ACTOR=implementer
  ies git verify --task T-0025 (0 drift). 5. Entregar deliverables/T-0025.md con envelope
  SDLC completo y realizar commit local en la rama task/T-0025 sin atribucion a IA
  (CLAUDE.md), sin merge, sin push y sin deploy.'
expected_output: CSS/layout centrado en Safari real (max 1120px, padding 28/16 en
  breakpoint 800px), chat preservado (compositor 880px), version candidata 0.4.0-rc.1
  coherente, pruebas automatizadas y build en verde, 14 celdas medidas y capturas
  Safari real en deliverables/evidence/T-0025/, deliverables/T-0025.md completo y
  commit local en task/T-0025 con 0 drift.
parent_task: T-0022
dependencies: []
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- long/adr/ADR-003-centered-container.md
- long/adr/ADR-006-tool-context-models.md
- mid/decisions.md
- immediate/handoff.md
acceptance_criteria:
- 'REQ-001 / P01: MIENTRAS se muestre una ruta dashboard incluida (/, /retos, /mesociclos,
  /70-3-cartagena), el sistema centra su contenedor en el area principal (.app-main)
  con W=min(A,1120) y padding 28px (>800px) o W=A y padding 16px (<=800px), con desvio
  <=2px y diferencia de margenes izq/der <=2px en las 14 celdas de la matriz S en
  Safari real.'
- 'REQ-002 / P02: MIENTRAS se muestre una ruta incluida, los controles permanecen
  accesibles sin overflow horizontal global (max(body.scrollWidth,documentElement.scrollWidth)-documentElement.clientWidth
  <=1px), sin recorte ni solapamiento y conservando el scroll interno de graficas.'
- 'REQ-003 / P03: CUANDO se active una navegacion incluida, muestra el destino esperado
  en el ciclo cuatro rutas dashboard -> chat con ID -> historial -> chat -> volver
  a 375px y 1600px, conservando en chat el compositor centrado (max 880px) y roles
  de burbuja.'
- 'REQ-020 / P20: Version candidata 0.4.0-rc.1 coherente en apps/web/package.json,
  ambos niveles de apps/web/package-lock.json, version visible, apps/web/lib/version.test.mjs,
  apps/web/README.md y apps/web/CHANGELOG.md, sin nuevas dependencias.'
- 'REQ-022 / P22: El codigo nuevo o tocado respeta la direccion de dependencias declarada
  (Clean Architecture, ADR-002/003/004), verificado por prueba ejecutable y revision
  de imports junto con npm test, npm run build e IES_ACTOR=implementer ies git verify
  --task T-0025 en PASS (0 drift).'
allowlist:
- apps/web/app/globals.css
- apps/web/app/(dashboard)/layout.tsx
- apps/web/tests/layout-responsive
- apps/web/lib/layout-responsive.test.mjs
- apps/web/package.json
- apps/web/package-lock.json
- apps/web/lib/version.test.mjs
- apps/web/README.md
- apps/web/CHANGELOG.md
- deliverables/T-0025.md
- deliverables/evidence/T-0025
created_at: '2026-10-17T12:56:19Z'
started_at: '2026-10-17T13:47:57Z'
completed_at: '2026-10-17T13:47:57Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0025.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 8139f9bb74c5d101f39ea303f34533a84c1486dd
  git_after: 8139f9bb74c5d101f39ea303f34533a84c1486dd
  result: success
edits: []
```

## T-0026 — V-UI: Verificación viewer independiente de T-0025 sobre commit 2dcd4ee

```yaml
id: T-0026
title: 'V-UI: Verificación viewer independiente de T-0025 sobre commit 2dcd4ee'
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: 'Auditar en modo solo lectura el commit exacto 2dcd4eed848e8e9806c846b6928896940fa21401
  en el worktree .ies/worktrees/T-0025 y su entrega deliverables/T-0025.md (referenciando
  la entrega de T-0025 sin marcarla done). Revisar todos los criterios de T-0025 y
  reproducir rigurosamente: 1. Cumplimiento estricto de allowlist con ies git verify
  --task T-0025. 2. Cumplimiento de constitucion con ies constitution check --task
  T-0026. 3. Gate de maquina con ies gate --task T-0025. 4. Pruebas unitarias de apps/web
  con npm test (18 tests pasando, 0 fallos). 5. Build de produccion de apps/web con
  npm run build (codigo de salida 0). 6. Auditoria de las 14 celdas de la matriz S
  en Safari real y ciclo de navegacion P03 en deliverables/evidence/T-0025/. 7. Verificacion
  de version candidata SemVer 0.4.0-rc.1 en package.json, package-lock.json, README.md,
  CHANGELOG.md y version.test.mjs. 8. Verificacion de direccion de dependencias Clean
  Architecture P22 en archivos tocados. Emitir veredicto canonico APROBAR | CORREGIR
  | BLOQUEAR en deliverables/T-0026.md.'
expected_output: deliverables/T-0026.md con informe de auditoria solo lectura, tabla
  de reproduccion de criterios, comprobaciones estaticas y dinamicas, hallazgos BLOCKING/NON_BLOCKING
  y veredicto canonico APROBAR | CORREGIR | BLOQUEAR.
parent_task: T-0022
dependencies: []
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- long/adr/ADR-003-centered-container.md
- long/adr/ADR-006-tool-context-models.md
- mid/decisions.md
- immediate/handoff.md
acceptance_criteria:
- Revision independiente en solo lectura del commit 2dcd4ee y deliverables/T-0025.md
  sin mutaciones en el repositorio
- Auditoria de allowlist (ies git verify) con 0 drift y verificacion de gate de maquina
  (ies gate --task T-0025 PASS)
- Reproduccion de pruebas npm test (18 tests) y npm run build con codigo de salida
  0
- Auditoria de las 14 celdas de la matriz S y ciclo de navegacion P03 en Safari real
  y evidencia fotografica
- Auditoria de coherencia SemVer 0.4.0-rc.1 y regla de dependencia Clean Architecture
  P22
- Veredicto canonico formal (APROBAR | CORREGIR | BLOQUEAR) con clasificacion de severidad
  en deliverables/T-0026.md
allowlist: []
created_at: '2026-10-17T13:34:17Z'
started_at: '2026-10-17T13:48:05Z'
completed_at: '2026-10-17T13:48:05Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0026.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 8139f9bb74c5d101f39ea303f34533a84c1486dd
  git_after: 8139f9bb74c5d101f39ea303f34533a84c1486dd
  result: success
edits: []
```

## T-0027 — I-SERVER: Backend de historial privado, auth RLS y modelo exclusivo (SPEC-002)

```yaml
id: T-0027
title: 'I-SERVER: Backend de historial privado, auth RLS y modelo exclusivo (SPEC-002)'
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: 'Ejecutar exclusivamente la etapa I-SERVER (G2) de specs/002-layout-responsive/{spec.md,plan.md}
  aprobados en DEC-009 (propuesta T-0022, PLAN-002 seccion 4), trabajando estrictamente
  dentro del worktree aislado .ies/worktrees/T-0027. 1. Orden tests-first: escribir
  primero pruebas automatizadas en apps/web/tests/chat-server/ y apps/web/lib/chat-server.test.mjs
  para contratos de dominio y puertos de aplicación (ConversationRepository, Identity,
  HealthContext, CoachProvider), RLS y aislamiento de usuario (REQ-004, REQ-005, P04,
  P05), persistencia y operaciones idempotentes (REQ-009, REQ-010, P09, P10), forzado
  exclusivo de modelo gpt-6-luna con reasoning_effort high sin tools (REQ-015, REQ-016,
  P15, P16), vínculo de salud (REQ-014, P14), retención/ventana 12 mensajes (REQ-018,
  P18), y regla de dependencias P22 (Clean Architecture: lib/chat/ puro, lib/chat/application/
  puertos, lib/infra/ adaptadores). 2. Implementar schema aditivo en supabase/migrations/20261017_coach_history.sql
  con tablas coach_conversations, coach_messages, coach_operations, coach_imports,
  coach_profile_links, RLS auth.uid()=owner_id, constraints y tests en supabase/tests/coach_history/.
  3. Implementar endpoints API en apps/web/app/api/conversations/ y apps/web/app/api/chat/
  con respuestas tipadas, cache no-store y sin exponer tokens/claves ni service-role.
  4. Refactorizar apps/web/lib/supabase.ts y apps/web/lib/openaiModels.ts hacia apps/web/lib/infra/
  según ADR-002, actualizando llamadas en condition.ts, dashboard.ts y mesocycle.ts
  sin romper compatibilidad. 5. Actualizar versión candidata a 0.4.0-rc.2 en apps/web/package.json,
  ambos niveles de package-lock.json, version.test.mjs, README.md y CHANGELOG.md sin
  dependencias externas nuevas. 6. Ejecutar pruebas unitarias, build de producción
  y verificación de arquitectura con cero drift (ies git verify).'
expected_output: deliverables/T-0027.md con frontmatter YAML reglamentario, envelope
  SDLC, tabla REQ->evidencia P04-P07, P09-P12, P14-P16, P18-P22, commit local en task/T-0027
  con candidato 0.4.0-rc.2, pruebas automatizadas en tests/chat-server/, migración
  aditiva SQL y suite de tests ejecutada con código 0.
parent_task: T-0022
dependencies:
- T-0025
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- long/adr/ADR-004-private-history.md
- long/adr/ADR-005-exclusive-chat-model.md
- long/adr/ADR-006-tool-context-models.md
- mid/decisions.md
- immediate/handoff.md
acceptance_criteria:
- Implementación de dominio, puertos y adaptadores de chat en apps/web/lib/chat/ y
  apps/web/lib/infra/ respetando Clean Architecture (P22)
- Migración SQL aditiva supabase/migrations/20261017_coach_history.sql con RLS auth.uid()=owner_id,
  claves únicas y pruebas de aislamiento (REQ-004, REQ-005, P04, P05)
- Endpoints API /api/conversations y /api/chat con control de concurrencia, idempotencia
  de operaciones y cache no-store (REQ-009, REQ-010, P09, P10)
- Forzado exclusivo en servidor de gpt-6-luna con reasoning_effort high sin tools
  ni fallback (REQ-015, REQ-016, P15, P16)
- Aislamiento de contexto de salud MVP por vínculo owner (REQ-014, P14) y ventana
  de 12 mensajes sin truncar historial DB (REQ-018, P18)
- Versionado SemVer coherente 0.4.0-rc.2 en paquete, lock, README, CHANGELOG y version.test.mjs
  (REQ-020, P20)
- Pruebas unitarias pasando, npm run build código 0 e ies git verify con 0 drift en
  worktree aislado
allowlist:
- apps/web/package.json
- apps/web/package-lock.json
- apps/web/lib/version.test.mjs
- apps/web/README.md
- apps/web/CHANGELOG.md
- deliverables/T-0027.md
- deliverables/evidence/T-0027
- apps/web/lib/chat
- apps/web/lib/infra
- apps/web/lib/condition.ts
- apps/web/lib/dashboard.ts
- apps/web/lib/mesocycle.ts
- apps/web/lib/supabase.ts
- apps/web/lib/openaiModels.ts
- apps/web/app/api/chat
- apps/web/app/api/conversations
- apps/web/app/(dashboard)
- apps/web/tests/chat-server
- apps/web/lib/chat-server.test.mjs
- supabase/migrations/20261017_coach_history.sql
- supabase/tests/coach_history
created_at: '2026-10-17T13:55:47Z'
started_at: '2026-10-17T14:37:45Z'
completed_at: '2026-10-17T14:37:45Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0027.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: bc8c2bf653fb149816b39ce213fcb65b76519831
  git_after: bc8c2bf653fb149816b39ce213fcb65b76519831
  result: success
edits: []
```

## T-0028 — V-SERVER: Verificación viewer independiente de T-0027 sobre commit 3fc506c

```yaml
id: T-0028
title: 'V-SERVER: Verificación viewer independiente de T-0027 sobre commit 3fc506c'
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: 'Auditar en modo solo lectura el commit exacto 3fc506c9e430bc28b2a13aa7dad0a55cbfbab54e
  en el worktree .ies/worktrees/T-0027 y su entrega deliverables/T-0027.md (referenciando
  la entrega de T-0027 sin marcarla done). Revisar todos los criterios de T-0027 y
  reproducir rigurosamente: 1. Cumplimiento estricto de allowlist con ies git verify
  --task T-0027 (0 drift). 2. Cumplimiento de constitución con ies constitution check
  --task T-0028 (0 BLOCKING). 3. Gate de máquina con ies gate --task T-0027 (PASS).
  4. Pruebas unitarias de apps/web con npm test (37 tests pasando, 0 fallos). 5. Build
  de producción de apps/web con npm run build (código de salida 0). 6. Auditoría de
  migración SQL aditiva en supabase/migrations/20261017_coach_history.sql, verificando
  constraints, revocación a rol anon y políticas RLS auth.uid()=owner_id. 7. Auditoría
  de forzado exclusivo de gpt-6-luna con reasoning_effort high en lib/infra/coach/openAiCoachProvider.ts
  sin tools ni fallback. 8. Verificación de regla de dependencia Clean Architecture
  P22 en apps/web/lib/chat/ y apps/web/lib/infra/. 9. Verificación de coherencia SemVer
  0.4.0-rc.2 en package.json, lock, README, CHANGELOG y version.test.mjs. Emitir veredicto
  canónico APROBAR | CORREGIR | BLOQUEAR en deliverables/T-0028.md.'
expected_output: deliverables/T-0028.md con informe de auditoría solo lectura, tabla
  de reproducción de criterios, comprobaciones estáticas y dinámicas, hallazgos BLOCKING/NON_BLOCKING
  y veredicto canónico APROBAR | CORREGIR | BLOQUEAR.
parent_task: T-0022
dependencies: []
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- long/adr/ADR-004-private-history.md
- long/adr/ADR-005-exclusive-chat-model.md
- long/adr/ADR-006-tool-context-models.md
- mid/decisions.md
- immediate/handoff.md
acceptance_criteria:
- Revisión independiente en solo lectura del commit 3fc506c y deliverables/T-0027.md
  sin mutaciones en el repositorio
- Auditoría de allowlist (ies git verify --task T-0027) con 0 drift y verificación
  de gate de máquina (ies gate --task T-0027 PASS)
- Reproducción de pruebas npm test (37 tests) y npm run build con código de salida
  0
- Auditoría de migración SQL aditiva, constraints de validación, revocación anon y
  políticas RLS auth.uid()=owner_id
- Auditoría de forzado exclusivo en servidor de gpt-6-luna High sin tools ni fallback
  (REQ-015, REQ-016)
- Auditoría de regla de dependencias Clean Architecture P22 en capas de dominio, aplicación
  e infraestructura
- Veredicto canónico formal (APROBAR | CORREGIR | BLOQUEAR) con clasificación de severidad
  en deliverables/T-0028.md
allowlist: []
created_at: '2026-10-17T14:30:49Z'
started_at: '2026-10-17T14:37:48Z'
completed_at: '2026-10-17T14:37:48Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0028.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: bc8c2bf653fb149816b39ce213fcb65b76519831
  git_after: bc8c2bf653fb149816b39ce213fcb65b76519831
  result: success
edits: []
```

## T-0029 — I-CLIENT: UI, ViewModel, historial sincronizado, migración opt-in y SemVer 0.4.0 (SPEC-002)

```yaml
id: T-0029
title: 'I-CLIENT: UI, ViewModel, historial sincronizado, migración opt-in y SemVer
  0.4.0 (SPEC-002)'
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: 'Ejecutar exclusivamente la etapa I-CLIENT (G2) de specs/002-layout-responsive/{spec.md,plan.md}
  aprobados en DEC-009 (propuesta T-0022, PLAN-002 seccion 4), trabajando estrictamente
  dentro del worktree aislado .ies/worktrees/T-0029. 1. Orden tests-first: escribir
  primero pruebas en apps/web/tests/chat-client/ y apps/web/lib/chat-client.test.mjs
  cubriendo ViewModel de chat, estados de sincronización, importación opt-in, ausencia
  de selector de modelos y preservación de layout y dirección de dependencias P22.
  2. Implementar pantalla de login en apps/web/app/login/ (Supabase Auth email OTP)
  y manejo de sesión/logout (REQ-004, REQ-013). 3. Refactorizar componentes de chat
  (CoachChat.tsx, CoachChatScreen.tsx) y hook dedicado useCoachConversation en apps/web/hooks/
  para conectar con los endpoints /api/conversations y /api/chat desarrollados en
  I-SERVER, mostrando historial sincronizado, estados ''Guardado'', reintento ante
  conflicto 409 y paginación (REQ-006, REQ-007, REQ-008, REQ-009, REQ-010). 4. Implementar
  flujo de importación opt-in desde localStorage (coachStorage.ts): lectura de conversaciones
  locales supervivientes, validación de digest, confirmación explícita de cuenta destino,
  copia a servidor sin modificar ni limpiar el almacenamiento local (REQ-011, REQ-012).
  5. Retirar selector de modelos (CoachModelSelect.tsx) y fijar etiqueta informativa
  estática GPT-6 Luna · High (REQ-017). 6. Verificar preservación del contenedor centrado
  y responsive en globals.css y rutas de chat (P01, P02, P03). 7. Actualizar versión
  a 0.4.0 final en apps/web/package.json, package-lock.json, README.md, CHANGELOG.md
  y version.test.mjs. 8. Ejecutar suite de pruebas completa y build de producción
  con 0 errores y 0 drift.'
expected_output: deliverables/T-0029.md con frontmatter YAML reglamentario, envelope
  SDLC, tabla REQ->evidencia P01-P22, commit local en task/T-0029 con versión 0.4.0
  final, pruebas automatizadas en tests/chat-client/, build Next.js código 0 e ies
  git verify con 0 drift.
parent_task: T-0022
dependencies:
- T-0027
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- long/adr/ADR-003-centered-container.md
- long/adr/ADR-004-private-history.md
- long/adr/ADR-005-exclusive-chat-model.md
- long/adr/ADR-006-tool-context-models.md
- mid/decisions.md
- immediate/handoff.md
acceptance_criteria:
- Implementación de ViewModel de chat y hook desacoplado en apps/web/hooks/ y componentes
  de UI respetando Clean Architecture (ADR-002, P22)
- Pantalla de login con OTP / sesión Supabase Auth y protección de rutas privadas
  (REQ-004, P04, P13)
- Historial sincronizado entre sesiones/navegadores, paginación y manejo de errores
  visible sin pérdida de borradores (REQ-006, REQ-007, REQ-008, P06, P07, P08)
- Flujo de importación local opt-in con confirmación de cuenta destino, validación
  de digest, sin alterar localStorage original (REQ-011, REQ-012, P11, P12)
- Retiro definitivo del selector de modelos e identificación estática exclusiva de
  GPT-6 Luna · High (REQ-017, P17)
- Preservación del layout responsive centrado max 1120px y compositor max 880px centrado
  sin overflow (REQ-001, REQ-002, REQ-003, P01, P02, P03)
- Sincronización SemVer final 0.4.0 en paquete, lock, README, CHANGELOG y version.test.mjs
  (REQ-020, P20)
- Pruebas unitarias pasando, build Next.js con código 0 y 0 drift con ies git verify
  en worktree aislado
allowlist:
- apps/web/package.json
- apps/web/package-lock.json
- apps/web/lib/version.test.mjs
- apps/web/README.md
- apps/web/CHANGELOG.md
- deliverables/T-0029.md
- deliverables/evidence/T-0029
- apps/web/components/CoachChat.tsx
- apps/web/components/CoachChatScreen.tsx
- apps/web/components/CoachModelSelect.tsx
- apps/web/hooks
- apps/web/app/login
- apps/web/app/(chat)
- apps/web/app/globals.css
- apps/web/lib/coachStorage.ts
- apps/web/lib/infra/auth
- apps/web/lib/infra/chat
- apps/web/tests/chat-client
- apps/web/lib/chat-client.test.mjs
created_at: '2026-10-17T14:46:53Z'
started_at: '2026-10-17T15:31:09Z'
completed_at: '2026-10-17T15:31:09Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0029.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 8f70c6d1991c39f7c3425028f354cdbd4032bac7
  git_after: 8f70c6d1991c39f7c3425028f354cdbd4032bac7
  result: success
edits: []
```

## T-0030 — V-INTEGRAL: Verificación viewer integral de T-0029 sobre commit d595e52

```yaml
id: T-0030
title: 'V-INTEGRAL: Verificación viewer integral de T-0029 sobre commit d595e52'
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: 'Auditar en modo solo lectura el commit exacto d595e52dcbd19e3b20c9aa8db8bb703a6cde50eb
  en el worktree .ies/worktrees/T-0029 y su entrega deliverables/T-0029.md (referenciando
  la entrega de T-0029 sin marcarla done). Revisar todos los criterios de T-0029 y
  reproducir rigurosamente: 1. Cumplimiento estricto de allowlist con ies git verify
  --task T-0029 (0 drift). 2. Cumplimiento de constitución con ies constitution check
  --task T-0030 (0 BLOCKING). 3. Gate de máquina con ies gate --task T-0029 (PASS).
  4. Pruebas unitarias de apps/web con npm test (58 tests pasando, 0 fallos). 5. Build
  de producción de apps/web con npm run build (código de salida 0). 6. Auditoría de
  ViewModel useCoachConversation y desacoplamiento de componentes CoachChat/CoachChatScreen
  (Clean Architecture P22). 7. Auditoría de login OTP y logout en apps/web/app/login/page.tsx.
  8. Auditoría de flujo de importación opt-in conservador en coachStorage.ts. 9. Auditoría
  de insignia estática GPT-6 Luna · High sin selectores en CoachModelSelect.tsx. 10.
  Auditoría de preservación de geometría centrada en globals.css. 11. Verificación
  de versión final SemVer 0.4.0 en package.json, lock, README, CHANGELOG y version.test.mjs.
  Emitir veredicto canónico APROBAR | CORREGIR | BLOQUEAR en deliverables/T-0030.md.'
expected_output: deliverables/T-0030.md con informe de auditoría solo lectura, tabla
  de reproducción integral de criterios P01-P22, comprobaciones estáticas y dinámicas,
  hallazgos BLOCKING/NON_BLOCKING y veredicto canónico APROBAR | CORREGIR | BLOQUEAR.
parent_task: T-0022
dependencies: []
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- long/adr/ADR-003-centered-container.md
- long/adr/ADR-004-private-history.md
- long/adr/ADR-005-exclusive-chat-model.md
- long/adr/ADR-006-tool-context-models.md
- mid/decisions.md
- immediate/handoff.md
acceptance_criteria:
- Revisión independiente en solo lectura del commit d595e52 y deliverables/T-0029.md
  sin mutaciones en el repositorio
- Auditoría de allowlist (ies git verify --task T-0029) con 0 drift y verificación
  de gate de máquina (ies gate --task T-0029 PASS)
- Reproducción de pruebas npm test (58 tests) y npm run build con código de salida
  0
- Auditoría de ViewModel de chat useCoachConversation, patrón MVVM y Clean Architecture
  P22
- Auditoría de login Supabase Auth OTP, flujo de sesión y logout seguro (REQ-004,
  REQ-013)
- Auditoría de importación opt-in conservadora, verificación de digest y preservación
  byte a byte de localStorage (REQ-011, REQ-012)
- Auditoría de retiro de selector de modelos y etiqueta informativa estática GPT-6
  Luna · High (REQ-017)
- Auditoría de preservación de centrado responsive max 1120px y compositor max 880px
  sin overflow (REQ-001, REQ-002, REQ-003)
- Auditoría de coherencia SemVer 0.4.0 final en paquete, lock, README, CHANGELOG y
  version.test.mjs (REQ-020, P20)
- Veredicto canónico formal (APROBAR | CORREGIR | BLOQUEAR) con clasificación de severidad
  en deliverables/T-0030.md
allowlist: []
created_at: '2026-10-17T15:25:29Z'
started_at: '2026-10-17T15:31:14Z'
completed_at: '2026-10-17T15:31:15Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0030.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 8f70c6d1991c39f7c3425028f354cdbd4032bac7
  git_after: 8f70c6d1991c39f7c3425028f354cdbd4032bac7
  result: success
edits: []
```

## T-0031 — Especificar y planificar tendencia mensual, macrociclo y recomendaciones (SPEC-003)

```yaml
id: T-0031
title: Especificar y planificar tendencia mensual, macrociclo y recomendaciones (SPEC-003)
project_id: python-garminconnect
origin: coordinator
destination: planner
status: done
input: 'Especificar formalmente en specs/003-tendencia-macrociclo/spec.md y planificar
  en specs/003-tendencia-macrociclo/plan.md la implementación de las tres funcionalidades
  de producto de la cola de handoff.md para la versión 0.5.0 MINOR: 1. ''Qué atender''
  (apps/web/app/(dashboard)/retos/page.tsx y apps/web/lib/dashboard.ts): incorporar
  para cada alerta/indicador una recomendación accionable en una frase corta basada
  en ciencia deportiva (modulación parasimpática/HRV, higiene y deuda de sueño, recarga
  autonómica/Body Battery, ratio de carga aguda:crónica ACWR < 1.3 para prevención
  de lesiones y descarga ante sobreesfuerzo/overreaching). 2. Tarjeta ''Macrociclo''
  (apps/web/app/(dashboard)/retos/page.tsx y lógica de dominio en apps/web/lib/mesocycle.ts):
  4 bloques claros: a) breve descripción de qué es un macrociclo; b) momento/fase
  actual (código, nombre, foco, deporte, techo FC/duración); c) cómo mejorarla (recomendación
  práctica alineada con la fase activa y el estado actual); d) cuándo termina (fecha
  de cierre de fase en formato es-CO, días restantes y referencia al cierre del macrociclo).
  3. Nueva ruta ''/tendencia'' y navegación (DashboardNav.tsx, retos/page.tsx, apps/web/app/(dashboard)/tendencia/page.tsx
  y apps/web/lib/tendencia.ts): retirar tendencia 14d de /retos, agregar ítem ''Tendencia''
  (/tendencia) en el menú lateral, mostrar en una sola hoja avances del mes (últimos
  30 días / mes en curso): barra y conteo de distribución de zonas (VERDE, AMARILLO,
  ROJO), resumen mensual de métricas clave (HRV, sueño, Body Battery, estrés, ACWR/VO2max)
  y tabla mensual con fechas es-CO y tabular-nums. 4. Respetar Clean Architecture
  (lógica pura en lib/, componentes en app/(dashboard) y components/), geometría centrada
  responsive (ADR-003, max-width 1120px) y versionado SemVer 0.5.0.'
expected_output: deliverables/T-0031.md con propuesta de G0, specs/003-tendencia-macrociclo/spec.md
  con requisitos EARS completos y specs/003-tendencia-macrociclo/plan.md con alternativas,
  matriz de pruebas y descomposición en tasks implementer/viewer.
parent_task: null
dependencies: []
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs:
- long/constitution.md
- long/standards.md
- long/adr/ADR-002-clean-architecture-regla-de-dependencia.md
- long/adr/ADR-003-centered-container.md
- long/adr/ADR-006-tool-context-models.md
- mid/decisions.md
- immediate/handoff.md
acceptance_criteria:
- spec.md con requisitos EARS completos, no-objetivos claros y criterios Pxx para
  las 3 funcionalidades de producto
- plan.md con análisis de alternativas, Clean Architecture P22, matriz de pruebas
  y descomposición en tasks con allowlists disjuntas
- Diseño de recomendaciones accionables de ciencia deportiva en Qué atender fundamentadas
  en HRV, sueño, Body Battery y ACWR
- 'Diseño de tarjeta Macrociclo en 4 bloques: descripción, momento/fase actual, cómo
  mejorarla y cuándo termina (es-CO)'
- Diseño de nueva ruta /tendencia en menú lateral con zonas VERDE/AMARILLO/ROJO, resumen
  mensual y tabla tabular-nums centrada (ADR-003)
- deliverables/T-0031.md con propuesta de G0 y envelope SDLC reglamentario
allowlist: []
created_at: '2026-10-17T15:41:10Z'
started_at: '2026-10-17T15:48:04Z'
completed_at: '2026-10-17T15:48:04Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0031.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 2768faeb336bc2526f00be1bbad6d85fccb6940b
  git_after: 2768faeb336bc2526f00be1bbad6d85fccb6940b
  result: success
edits: []
```

## T-0032 — I-DOMAIN-RETOS: Recomendaciones accionables y macrociclo en 4 bloques (SPEC-003)

```yaml
id: T-0032
title: 'I-DOMAIN-RETOS: Recomendaciones accionables y macrociclo en 4 bloques (SPEC-003)'
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: Implementar el motor de recomendaciones accionables de ciencia deportiva en
  apps/web/lib/dashboard.ts, la lógica y tipos de macrociclo en 4 bloques en apps/web/lib/mesocycle.ts,
  y actualizar la vista apps/web/app/(dashboard)/retos/page.tsx retirando la tendencia
  histórica de 14 días y renderizando la nueva tarjeta de Macrociclo según SPEC-003
  y PLAN-003.
expected_output: Suites de tests unitarios apps/web/tests/tendencia-macrociclo/recommendations.test.mjs
  y macrocycle.test.mjs pasando al 100%, Clean Architecture P22 preservada, renderizado
  verificado y deliverable deliverables/T-0032.md con evidencia completa.
parent_task: T-0031
dependencies: []
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 'REQ-001: Alertas de sueño con recomendación fisiológica de higiene y recuperación
  de deuda'
- 'REQ-002: Alertas de HRV con recomendación de modulación autonómica y estimulación
  vagal'
- 'REQ-003: Alertas de Body Battery con pautas de carga parasimpática y pausas activas'
- 'REQ-004: Alertas de ACWR > 1.3 con reducción de Gabbett (<1.3 seguro, >1.5 peligro)'
- 'REQ-005: Detección de sobreesfuerzo agudo y descarga activa obligatoria'
- 'REQ-006: Validación y recomendación afirmativa para estado VERDE'
- 'REQ-007: Tarjeta de macrociclo en 4 bloques visuales delimitados'
- 'REQ-008: Explicación pedagógica del concepto de macrociclo en Bloque A'
- 'REQ-009: Detalle de momento/fase actual con techo de FC y duración máxima en Bloque
  B'
- 'REQ-010: Recomendación práctica contextualizada según fase y fatiga en Bloque C'
- 'REQ-011: Fecha fin en formato es-CO, días restantes y lista de hitos en Bloque
  D'
- 'REQ-012: Retiro de tendencia histórica de 14d en /retos preservando el resto de
  tarjetas'
allowlist:
- apps/web/lib/dashboard.ts
- apps/web/lib/mesocycle.ts
- apps/web/app/(dashboard)/retos/page.tsx
- apps/web/tests/tendencia-macrociclo/recommendations.test.mjs
- apps/web/tests/tendencia-macrociclo/macrocycle.test.mjs
- deliverables/T-0032.md
created_at: '2026-10-17T15:53:57Z'
started_at: '2026-10-17T16:10:13Z'
completed_at: '2026-10-17T16:10:13Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0032.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 43de96b9a7bf0cbdccf50777e4792a318adb25f9
  git_after: 43de96b9a7bf0cbdccf50777e4792a318adb25f9
  result: success
edits: []
```

## T-0033 — I-TENDENCIA-NAV: Ruta /tendencia, menú lateral, distribución de zonas y resumen mensual (SPEC-003)

```yaml
id: T-0033
title: 'I-TENDENCIA-NAV: Ruta /tendencia, menú lateral, distribución de zonas y resumen
  mensual (SPEC-003)'
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: Implementar la lógica y tipos de tendencia mensual en apps/web/lib/tendencia.ts
  (distribución de zonas y agregación de métricas), agregar la ruta /tendencia en
  apps/web/components/DashboardNav.tsx, crear la vista apps/web/app/(dashboard)/tendencia/page.tsx
  con la barra de distribución, tarjetas de resumen y tabla con tabular-nums y fechas
  es-CO, y estilos asociados en globals.css según SPEC-003 y PLAN-003.
expected_output: Suites de tests unitarios apps/web/tests/tendencia-macrociclo/trend-monthly.test.mjs
  y architecture.test.mjs pasando al 100%, Clean Architecture P22 preservada, renderizado
  verificado y deliverable deliverables/T-0033.md con evidencia completa.
parent_task: T-0031
dependencies:
- T-0032
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 'REQ-013: Enlace /tendencia en menú lateral DashboardNav con icono e indicador de
  estado activo'
- 'REQ-014: Layout centrado max-width 1120px y padding responsive en /tendencia (ADR-003)'
- 'REQ-015: Barra de distribución mensual de zonas VERDE/AMARILLO/ROJO con porcentajes
  y días'
- 'REQ-016: Resumen consolidado mensual de 30 días de HRV, sueño, Body Battery, estrés
  y ACWR'
- 'REQ-017: Tabla de evolución diaria con fechas es-CO, badges de zona y números tabulares
  (tabular-nums)'
- 'REQ-018: Tolerancia a datos incompletos o errores con estado vacío explicativo
  amigable'
- 'REQ-019: Clean Architecture (ADR-002, P22) con funciones puras en lib/tendencia.ts'
allowlist:
- apps/web/lib/tendencia.ts
- apps/web/components/DashboardNav.tsx
- apps/web/app/(dashboard)/tendencia/page.tsx
- apps/web/app/globals.css
- apps/web/tests/tendencia-macrociclo/trend-monthly.test.mjs
- apps/web/tests/tendencia-macrociclo/architecture.test.mjs
- deliverables/T-0033.md
created_at: '2026-10-17T16:13:14Z'
started_at: '2026-10-17T16:25:57Z'
completed_at: '2026-10-17T16:25:57Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0033.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 609c523cd381eccf83c62dc8f6e3ce0ce1632431
  git_after: 609c523cd381eccf83c62dc8f6e3ce0ce1632431
  result: success
edits: []
```

## T-0034 — I-RELEASE-050: Bump SemVer 0.5.0, sincronización grupo R y suite consolidada (SPEC-003)

```yaml
id: T-0034
title: 'I-RELEASE-050: Bump SemVer 0.5.0, sincronización grupo R y suite consolidada
  (SPEC-003)'
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: Actualizar la versión de la aplicación a SemVer 0.5.0 MINOR en apps/web/package.json,
  ambos niveles de package-lock.json, README.md y CHANGELOG.md documentando las 3
  mejoras de SPEC-003 (recomendaciones accionables de ciencia deportiva, tarjeta macrociclo
  en 4 bloques y ruta /tendencia con navegación), agregar la suite runner apps/web/lib/tendencia-macrociclo.test.mjs
  para integración con npm test, y verificar que pasen todas las pruebas sin dependencias
  nuevas.
expected_output: Versión 0.5.0 sincronizada en todos los archivos del grupo R, apps/web/lib/tendencia-macrociclo.test.mjs
  ejecutando todas las pruebas de tendencia-macrociclo con npm test, 0 dependencias
  añadidas, build exitoso y deliverable deliverables/T-0034.md con evidencia completa.
parent_task: T-0031
dependencies:
- T-0033
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 'REQ-020: Versionado SemVer 0.5.0 MINOR en package.json, package-lock.json (ambos
  niveles), version.test.mjs, README.md y entrada formal en CHANGELOG.md'
allowlist:
- apps/web/package.json
- apps/web/package-lock.json
- apps/web/lib/version.test.mjs
- apps/web/README.md
- apps/web/CHANGELOG.md
- apps/web/lib/tendencia-macrociclo.test.mjs
- deliverables/T-0034.md
created_at: '2026-10-17T16:26:44Z'
started_at: '2026-10-17T16:32:49Z'
completed_at: '2026-10-17T16:32:49Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0034.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 3c9ef5a4db9a3de4a95a3177ccdd468829cbf712
  git_after: 3c9ef5a4db9a3de4a95a3177ccdd468829cbf712
  result: success
edits: []
```

## T-0035 — V-INTEGRAL-050: Auditoría viewer integral independiente de SPEC-003 (SemVer 0.5.0)

```yaml
id: T-0035
title: 'V-INTEGRAL-050: Auditoría viewer integral independiente de SPEC-003 (SemVer
  0.5.0)'
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: Realizar una auditoría independiente en modo solo lectura de la implementación
  completa de SPEC-003 (commits de T-0032, T-0033 y T-0034 integrados en master),
  ejecutando las suites de tests (npm test), el build de producción, la verificación
  de Clean Architecture P22, la geometría centrada ADR-003, el versionado SemVer 0.5.0
  y emitiendo el veredicto formal en deliverables/T-0035.md.
expected_output: Informe de auditoría integral en deliverables/T-0035.md con envelope
  SDLC completo, tabla de requisitos EARS vs evidencia verificada, evaluación de constitución
  y machine gate, y veredicto canónico formal.
parent_task: T-0031
dependencies:
- T-0034
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 'REQ-001..020: Auditoría integral independiente de los 20 requisitos EARS de SPEC-003'
- 'P01..P20: Ejecución y verificación de 82 tests unitarios pasando al 100% con 0
  fallos'
- 'BUILD: Compilación limpia Next.js 15 App Router con generación estática y dinámica
  exitosa'
- 'CLEAN-ARCH: Verificación Clean Architecture P22 sin imports de React/Next/Supabase
  en lib/'
- 'GEOMETRY: Verificación de contenedor centrado max-width 1120px responsive (ADR-003)'
- 'SEMVER: Verificación de versión 0.5.0 sincronizada en package.json, lock, README
  y CHANGELOG'
- 'GATE: Evaluación de machine gate y constitución IES (0 BLOCKING)'
- 'VEREDICTO: Emisión de veredicto canónico (APROBAR | CORREGIR | BLOQUEAR) en deliverables/T-0035.md'
allowlist:
- deliverables/T-0035.md
created_at: '2026-10-17T16:33:27Z'
started_at: '2026-10-17T16:41:29Z'
completed_at: '2026-10-17T16:41:29Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0035.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: cd5b006fc4f00e1d3536345801dfa4808e5531ec
  git_after: cd5b006fc4f00e1d3536345801dfa4808e5531ec
  result: success
edits: []
```

## T-0036 — Especificar y planificar correcciones 0.5.1 (SPEC-004)

```yaml
id: T-0036
title: Especificar y planificar correcciones 0.5.1 (SPEC-004)
project_id: python-garminconnect
origin: coordinator
destination: planner
status: done
input: 'Redactar spec.md y plan.md para SPEC-004 cubriendo los 3 puntos de handoff.md:
  corrección de desborde PUNTUACIÓN DE SUEÑO, posicionamiento de CoachChat en el primer
  cuarto de Inicio, y sincronización reactiva de token/historial local en useCoachConversation
  y componentes de chat.'
expected_output: specs/004-patch-layout-chat/spec.md y plan.md completos y deliverable
  deliverables/T-0036.md con propuesta cerrada para Gate G0.
parent_task: null
dependencies: []
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- spec.md con requisitos EARS para desborde métricas, jerarquía de chat e historial
- plan.md con descomposición en implementer y viewer, allowlists disjuntas y reserva
  grupo R
allowlist:
- specs/004-patch-layout-chat/spec.md
- specs/004-patch-layout-chat/plan.md
- deliverables/T-0036.md
created_at: '2026-10-17T17:07:59Z'
started_at: '2026-10-17T17:16:36Z'
completed_at: '2026-10-17T17:16:36Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0036.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 385b1edb1126078190b92399064b0478b7e983b8
  git_after: 385b1edb1126078190b92399064b0478b7e983b8
  result: success
edits: []
```

## T-0037 — I-PATCH-051: Corrección de desborde métricas, jerarquía de chat, historial y SemVer 0.5.1

```yaml
id: T-0037
title: 'I-PATCH-051: Corrección de desborde métricas, jerarquía de chat, historial
  y SemVer 0.5.1'
project_id: python-garminconnect
origin: coordinator
destination: implementer
status: done
input: Implementar las correcciones de desborde en PUNTUACIÓN DE SUEÑO, posicionamiento
  compacto de CoachChat al inicio (~25vh) antes de TodayCard, reactividad de token
  e historial local en chat, y bump SemVer 0.5.1 PATCH en Grupo R según SPEC-004 y
  PLAN-004.
expected_output: Suites de tests unitarios y de integración pasando al 100%, build
  de Next.js limpio, 0 regresiones y deliverable deliverables/T-0037.md con evidencia
  completa.
parent_task: T-0036
dependencies: []
priority: high
profile: fast-track
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 'REQ-001: Ausencia de desborde horizontal (scrollWidth <= clientWidth) en .metrics-grid
  y celdas métricas en viewports de 375px a 1600px'
- 'REQ-002: Reglas CSS canónicas minmax(7.5rem, 1fr), min-width 0, overflow-wrap break-word,
  line-height 1.25 y flex-shrink 0 en badge'
- 'REQ-003: Posicionamiento de CoachChat como primer componente en Inicio tras page-header
  y antes de TodayCard'
- 'REQ-004: Dimensionamiento compacto de CoachChat a ~25vh con max-height 28vh, min-height
  180px, compositor 2 filas y scroll en historial'
- 'REQ-005: Sincronización reactiva de accessToken en CoachConversationViewModel y
  recarga de conversaciones'
- 'REQ-006: Captura resiliente de respuestas no exitosas en loadConversations() sin
  crash ni estado bloqueado'
- 'REQ-007: Merge deduplicado de conversaciones remotas y locales supervivientes de
  localStorage en CoachChat y CoachChatScreen'
- 'REQ-008: Respaldo inmediato en localStorage con upsertChat al enviar y recibir
  mensajes en el chat'
- 'REQ-009: Versionado sincronizado SemVer 0.5.1 PATCH en package.json, lock, README,
  CHANGELOG y version.test.mjs'
allowlist:
- apps/web/app/globals.css
- apps/web/components/TodayCard.tsx
- apps/web/app/(dashboard)/page.tsx
- apps/web/components/CoachChat.tsx
- apps/web/components/CoachChatScreen.tsx
- apps/web/hooks/useCoachConversation.ts
- apps/web/lib/coachStorage.ts
- apps/web/package.json
- apps/web/package-lock.json
- apps/web/README.md
- apps/web/CHANGELOG.md
- apps/web/lib/version.test.mjs
- apps/web/tests/patch-layout-chat
- apps/web/lib/patch-layout-chat.test.mjs
- deliverables/T-0037.md
created_at: '2026-10-17T17:19:10Z'
started_at: '2026-10-17T17:42:55Z'
completed_at: '2026-10-17T17:42:55Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0037.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 7b173861c16619dc83f88a6edcf2c236a7246f48
  git_after: 7b173861c16619dc83f88a6edcf2c236a7246f48
  result: success
edits: []
```

## T-0038 — V-VIEWER-051: Auditoría viewer integral independiente de SPEC-004 (SemVer 0.5.1)

```yaml
id: T-0038
title: 'V-VIEWER-051: Auditoría viewer integral independiente de SPEC-004 (SemVer
  0.5.1)'
project_id: python-garminconnect
origin: coordinator
destination: viewer
status: done
input: Realizar una auditoría independiente en modo solo lectura de la implementación
  de T-0037 (commit en task/T-0037), ejecutando la suite de pruebas (npm test), build
  de Next.js, verificación de Clean Architecture, geometría centrada, ausencia de
  desbordamientos en PUNTUACIÓN DE SUEÑO, posición de CoachChat, reactividad del historial
  y bump SemVer 0.5.1 PATCH, emitiendo veredicto canónico en deliverables/T-0038.md.
expected_output: Informe de auditoría integral en deliverables/T-0038.md con envelope
  SDLC completo, tabla de requisitos EARS vs evidencia, evaluación de constitución
  y machine gate, y veredicto formal canónico.
parent_task: T-0036
dependencies:
- T-0037
priority: high
profile: riguroso
autonomy: hitl
execution_mode: null
requested_iterations: null
skills: []
memory_refs: []
acceptance_criteria:
- 'REQ-001..009: Auditoría integral independiente de los 9 requisitos EARS de SPEC-004'
- 'TESTS: Ejecución y verificación del 100% de tests unitarios y de integración pasando
  con 0 fallos'
- 'BUILD: Compilación limpia Next.js 15 App Router sin errores'
- 'GEOMETRY: Ausencia de desborde horizontal (scrollWidth <= clientWidth) en TodayCard
  y contenedor centrado ADR-003'
- 'SEMVER: Versión 0.5.1 PATCH sincronizada en package.json, lock, README, CHANGELOG
  y version.test.mjs'
- 'VEREDICTO: Emisión de veredicto canónico (APROBAR | CORREGIR | BLOQUEAR) en deliverables/T-0038.md'
allowlist:
- deliverables/T-0038.md
created_at: '2026-10-17T17:19:20Z'
started_at: '2026-10-17T17:49:18Z'
completed_at: '2026-10-17T17:49:19Z'
blocked_reason: null
superseded_by: null
superseded_reason: null
terminal_status: null
output_ref: deliverables/T-0038.md
approval:
  required: true
  approved_by: null
  approved_at: null
metrics:
  git_before: 7b173861c16619dc83f88a6edcf2c236a7246f48
  git_after: 7b173861c16619dc83f88a6edcf2c236a7246f48
  result: success
edits: []
```
