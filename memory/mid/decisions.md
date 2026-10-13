---
schema_version: 1
project_id: python-garminconnect
layer: mid
last_updated: '2026-10-13T18:35:00Z'
source: coordinator
confidence: alta
---

# Decisions

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





