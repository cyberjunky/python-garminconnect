---
schema_version: 1
project_id: python-garminconnect
next_id: 18
source: ies-cli
last_updated: '2026-10-14T15:19:18Z'
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
```
