# Handoff — Garmin Connect & Coaching Platform

## 1. Estado Actual (13 de octubre de 2026)

- **Rama principal**: `master` actualizada con el merge commit `0d81139` que incorporó el PR 1 (`cursor/shell-chat-hoy-43bc`).
- **SPEC-001 (Sincronización recurrente de tokens)**: Implementada y verificada en producción:
  - Tabla `public.garmin_tokens` en Supabase creada con Row Level Security (RLS) habilitado. Rol `service_role` autorizado (HTTP 200) y rol `anon` completamente bloqueado (HTTP 401).
  - Rotación y persistencia de tokens activa en el cron diario de GitHub Actions (`coaching-daily-collect.yml`), verificado en run `38450120206` con `"tokens_persisted": true` y fila creada en Supabase (`user_id: 00000000-0000-0000-0000-000000000001`).
- **Frontend Web (`apps/web`) en Vercel**:
  - Proyecto en Vercel renombrado a **"tri-coach"** (el CLI local sigue enlazado por `projectId`) y configurado con `Root Directory = apps/web`.
  - La URL de producción oficial sigue siendo **`https://web-chi-eight-31.vercel.app`** (sitio respondiendo HTTP 200 con versión visible `v0.1.0`).
  - *Nota importante*: el dominio `tri-coach.vercel.app` **NO** nos pertenece (corresponde a la aplicación de un tercero); no debe usarse ni enlazarse bajo ninguna circunstancia.
  - Despliegue automático de producción activo sobre `master` (`0d81139`).
  - Shell lateral con navegación (Inicio, Retos, Mesociclos, 70.3), tarjeta Hoy, chat con IA contextualizado y botón "Actualizar" que dispara el workflow de recolección en GitHub Actions.

## 2. Decisiones Arquitectónicas y Operativas

- **Persistencia de Tokens**: Supabase `garmin_tokens` actúa como almacén primario y duradero para runners efímeros de GitHub Actions; `GARMINTOKENS_B64` se mantiene como fallback secundario de contingencia.
- **Seguridad**: RLS estricto; tokens nunca expuestos al cliente web ni a roles no autenticados (`anon`). Secrets nunca filtrados en logs (`REQ-005`).
- **Monorepo y Despliegue**: Raíz del repo contiene el backend Python y workflows; `apps/web` contiene la app Next.js 15. Vercel apunta su Root Directory a `apps/web`.
- **Disciplina Git**: Commits sin trailers de IA (según `CLAUDE.md`). Prohibición estricta de `amend` + `force-push` sobre commits ya empujados (`DEC-001`). Toda modificación posterior al push se realiza con commit normal hacia adelante.
- **Disciplina SDD**: El gate formal de aprobación de especificaciones (`ies spec approve`) debe preceder a cualquier implementación; `SPEC-001` cuenta con aprobación retroactiva formalizada en `DEC-003`.

## 3. Tareas en Curso y Pendientes

- **`T-0010` (implementer, fast-track)**:
  1. Corregir 9 errores de `ruff` introducidos por `SPEC-001` en scripts auxiliares (`scripts/garmin_auth.py`, `services/collector/supabase_client.py`).
  2. Sustituir los bloques `except Exception: pass` en `scripts/garmin_auth.py:login_client` por `_LOGGER.warning` explícito (`REQ-005`).
  3. Registrar en los logs del workflow la fuente exacta desde la que se restauró el token (`source: supabase` o `source: b64_fallback`).
  4. Ajustar `scripts/deploy_web_vercel.sh` al nuevo `Root Directory = apps/web` de Vercel.
- **`T-0011` (backlog, riguroso)**:
  - Definir estrategia y saneamiento de los 97 errores de `ruff` heredados de master en scripts históricos para que los jobs `test (3.12)` y `test (3.13)` ejecuten `pytest` en CI de GitHub Actions.
- **Verificación operativa en vivo**:
  - `REQ-003`: Confirmar la sincronización local en vivo (`scripts/refresh_garmin_session.py` y `scripts/publish_garmin_tokens_secret.sh`) en el próximo ciclo de refresco manual desde el Mac.

## 4. Comandos de Referencia

- **Tests locales**:
  ```bash
  .venv/bin/python -m pytest -q tests
  ```
- **Validación del framework**:
  ```bash
  ies status
  ies memory validate
  ies doctor
  ```
- **Disparo manual del cron de recolección**:
  ```bash
  gh workflow run coaching-daily-collect.yml --repo dalarconics/python-garminconnect --ref master
  ```
