---
schema_version: 1
plan_id: PLAN-001
spec: SPEC-001
slug: recurring-token-sync
project_id: python-garminconnect
version: 1
status: approved
autonomy: autonomous
owner_task: T-0001
last_updated: '2026-10-13T19:11:06Z'
source: ies planner T-0001
approved_at: '2026-10-13T19:11:06Z'
decision_ref: memory/mid/decisions.md#DEC-003
---

# PLAN-001: Sincronización recurrente de tokens y actualización Vercel

## 1. Decisión técnica (resumen del ADR)

### Contexto
Garmin Connect gestiona la sesión mediante tokens OAuth con ciclo de expiración periódico. En el pipeline de recolección diaria de GitHub Actions (`coaching-daily-collect.yml`), los runners son efímeros: cualquier token refrescado durante la corrida se pierde al desmontarse el runner si no se persiste en un almacenamiento externo duradero. Esto hace que el token almacenado como secreto estático vuelva a vencer, forzando intervenciones manuales. Adicionalmente, el frontend en Next.js (`apps/web`) requiere actualizarse y desplegarse en producción en Vercel con la versión `v0.1.0`, navegación funcional y visualización de las métricas recién recolectadas en Supabase.

### Alternativas evaluadas
1. **Alternativa A — Escritura directa del GitHub Secret desde el runner vía GitHub API / gh CLI**:
   - *Complejidad*: Media. Requiere un Personal Access Token (PAT) con permisos de escritura de secretos o un GitHub App, expuesto en el entorno de ejecución, además de cifrado libsodium.
   - *Riesgo*: Alto. Conceder permisos de escritura sobre secretos del repositorio a un runner de CI/CD incrementa sustancialmente la superficie de ataque y el riesgo de exfiltración.
   - *Costo*: Bajo.
   - *Reversibilidad*: Alta.
2. **Alternativa B — Persistencia centralizada en Supabase (`garmin_tokens`) con RLS (`service_role` exclusivo) + sincronización bidireccional + contingencia en GitHub Secrets (Recomendada)**:
   - *Complejidad*: Baja. Supabase ya es la base de datos operativa del proyecto. `SUPABASE_SERVICE_ROLE_KEY` ya se encuentra configurada en GitHub Secrets y en entornos locales autorizados. Permite transacciones seguras de JSON estructurado.
   - *Riesgo*: Mínimo. Row Level Security garantiza aislamiento total: la tabla `garmin_tokens` no posee ninguna política para el rol `anon`, haciendo imposible su lectura o escritura desde clientes web o endpoints públicos.
   - *Costo*: Cero (infraestructura existente).
   - *Reversibilidad*: Inmediata (drop de tabla o fallback transparente).
3. **Alternativa C — Microservicio externo o instancia Redis dedicada para delegación de autenticación**:
   - *Complejidad*: Alta. Requiere infraestructura adicional, monitoreo y mantenimiento fuera del stack del proyecto.
   - *Riesgo*: Medio.
   - *Costo*: Medio/Alto.
   - *Reversibilidad*: Baja.

### Recomendación y tradeoff aceptado
Se adopta la **Alternativa B**. Se implementa la tabla `public.garmin_tokens` en Supabase con RLS estricto (`service_role` exclusivo). El workflow de GitHub Actions restaura tokens desde Supabase (con fallback a `GARMINTOKENS_B64`), ejecuta la recolección diaria y guarda los tokens refrescados nuevamente en Supabase. Los scripts locales en el Mac mantienen sincronización bidireccional opcional. El frontend `apps/web` se valida y despliega en Vercel producción.

ADR propuesto: `memory/long/adr/ADR-002-recurring-token-persistence.md`

## 2. Diseño

### Componentes tocados
1. **Migración Supabase** (`supabase/migrations/20261011_garmin_tokens.sql`):
   - Definición de tabla `public.garmin_tokens` (columnas: `id uuid`, `user_id uuid references users(id)`, `tokens jsonb`, `created_at`, `updated_at`).
   - Habilitación obligatoria de Row Level Security (`ALTER TABLE public.garmin_tokens ENABLE ROW LEVEL SECURITY`).
   - Política `service_role_all` exclusiva para el rol de servicio (`service_role`). Cero permisos para `anon`.
2. **Capa de persistencia Supabase** (`services/collector/supabase_client.py`):
   - `save_garmin_tokens(tokens: dict[str, Any], user_id: str = DEFAULT_USER_ID) -> dict[str, str]`: Guarda/actualiza el JSON de tokens en `garmin_tokens`.
   - `load_garmin_tokens(user_id: str = DEFAULT_USER_ID) -> dict[str, Any] | None`: Recupera el JSON de tokens más reciente de `garmin_tokens`.
3. **Adaptador de autenticación Garmin** (`scripts/garmin_auth.py`):
   - `restore_tokens_from_supabase(token_dir: str | Path | None = None, user_id: str = DEFAULT_USER_ID) -> bool`: Restaura los tokens desde Supabase a archivos locales con permisos `0o600`.
   - `save_tokens_to_supabase(token_dir: str | Path | None = None, user_id: str = DEFAULT_USER_ID) -> bool`: Lee los archivos de tokens locales y los persiste en Supabase.
   - Extensión en `login_client(restore_from_cloud=True)` para restaurar tokens de Supabase cuando el almacenamiento local no posea sesiones activas.
4. **Pipeline GitHub Actions** (`.github/workflows/coaching-daily-collect.yml`):
   - Paso 1: "Restore Garmin tokens": intenta restaurar desde Supabase con fallback a `GARMINTOKENS_B64`.
   - Paso 2: "Collect and upsert to Supabase": ejecuta recolección diaria de métricas.
   - Paso 3: "Persist refreshed Garmin tokens": tras éxito en la recolección, persiste los tokens actualizados de `~/.garminconnect` en Supabase.
5. **Scripts locales de sincronización** (`scripts/refresh_garmin_session.py` y `scripts/publish_garmin_tokens_secret.sh`):
   - Soporte para flag `--sync-supabase` y guardado automático post-refresco.
   - Publicación a GitHub Secrets cuando `gh` CLI esté disponible y autenticado.
6. **Aplicación web Next.js en Vercel** (`apps/web`):
   - Validación de build (`npm run build`), dependencias y lint.
   - Despliegue a producción vía `vercel --prod` y verificación del estado 200 con visualización de datos de hoy.

### Contratos e interfaces
- **Tabla Supabase**:
  ```sql
  create table if not exists public.garmin_tokens (
      id uuid primary key default gen_random_uuid(),
      user_id uuid not null references public.users(id) on delete cascade,
      tokens jsonb not null,
      created_at timestamptz not null default now(),
      updated_at timestamptz not null default now(),
      unique (user_id)
  );
  alter table public.garmin_tokens enable row level security;
  create policy "service_role_all" on public.garmin_tokens for all using (true) with check (true);
  ```
- **Firmas Python**:
  ```python
  def save_garmin_tokens(tokens: dict[str, Any], user_id: str = DEFAULT_USER_ID) -> dict[str, str]: ...
  def load_garmin_tokens(user_id: str = DEFAULT_USER_ID) -> dict[str, Any] | None: ...
  def restore_tokens_from_supabase(token_dir: str | Path | None = None, user_id: str = DEFAULT_USER_ID) -> bool: ...
  def save_tokens_to_supabase(token_dir: str | Path | None = None, user_id: str = DEFAULT_USER_ID) -> bool: ...
  ```

## 3. Dimensionamiento del equipo y autonomía
- **Autonomía de la ejecución**: `autonomous` (definida al crear la spec). La aprobación del plan autoriza al coordinator a orquestar a implementers y viewers a través de las tasks descompuestas sin detenciones innecesarias.
- **Tamaño**: `M`.
- **Equipo propuesto**: 1 implementer para tasks de desarrollo / despliegue + 1 viewer para la verificación integral final.

## 4. Descomposición en tasks

| Task propuesta | Destino | REQ cubiertos | Allowlist de archivos | Depende de | Perfil |
|---|---|---|---|---|---|
| **T-0002**: Implementar persistencia de tokens Garmin en Supabase y adaptadores Python | implementer | REQ-001, REQ-005 | `supabase/migrations/20261011_garmin_tokens.sql`, `services/collector/supabase_client.py`, `scripts/garmin_auth.py`, `tests/test_garmin_tokens_supabase.py` | T-0001 | riguroso |
| **T-0003**: Automatizar sincronización recurrente en GitHub Actions y scripts locales | implementer | REQ-002, REQ-003, REQ-005 | `.github/workflows/coaching-daily-collect.yml`, `scripts/publish_garmin_tokens_secret.sh`, `scripts/refresh_garmin_session.py` | T-0002 | riguroso |
| **T-0004**: Build, validación y despliegue a producción de apps/web en Vercel | implementer | REQ-004 | `apps/web/**` | T-0003 | riguroso |
| **T-0005**: Verificación integral SDD SPEC-001 | viewer | todos (REQ-001..005) | solo lectura | T-0004 | riguroso |

## 5. Matriz de trazabilidad

| REQ | Task | Test / comprobación | Evidencia esperada | Resultado |
|---|---|---|---|---|
| REQ-001 | T-0002 | `pytest tests/test_garmin_tokens_supabase.py` | Migración aplicada, RLS activo, roundtrip de lectura y escritura exitoso vía `service_role`, `anon` rechazado | Cumple en producción (migración aplicada: service_role 200, anon 401; tabla garmin_tokens con RLS activo) |
| REQ-002 | T-0003 | Ejecución del workflow en GitHub Actions | Step de restore lee tokens desde Supabase y step de persist guarda tokens renovados tras la recolección | Cumple en producción (run 38450120206 sobre 0d81139: success, "tokens_persisted": true, fila persistida en garmin_tokens) |
| REQ-003 | T-0003 | Ejecución local de `refresh_garmin_session.py` y `publish_garmin_tokens_secret.sh` | Tokens locales sincronizados hacia Supabase y secreto `GARMINTOKENS_B64` actualizado si gh CLI está disponible | tests; en vivo pendiente (validado en tests unitarios locales; prueba en vivo en el Mac pendiente al próximo refresh) |
| REQ-004 | T-0004 | `npm --prefix apps/web run build && vercel deploy --prod` | Compilación Next.js limpia sin errores de tipos y despliegue en producción con respuesta 200 y métricas visibles | Cumple en producción (deploy 0d81139 en Vercel Ready con HTTP 200, Root Directory = apps/web y versión v0.1.0) |
| REQ-005 | T-0002, T-0003 | Prueba unitaria con credenciales/tokens erróneos | Excepción capturada, no se sobreescribe Supabase con null, logs limpios sin tokens en stdout | Cumple (guards de validación impiden sobreescritura con nulos; run 38450120206 sin secretos en logs) |


## 6. Verificación global

1. **Suite de pruebas unitarias y de integración**:
   ```bash
   ./.venv/bin/pytest tests/test_garmin_tokens_supabase.py tests/test_garmin_coaching.py
   ```
2. **Comprobación de sincronización local**:
   ```bash
   ./.venv/bin/python scripts/refresh_garmin_session.py
   ```
3. **Verificación de build y despliegue web**:
   ```bash
   npm --prefix apps/web run build
   npx vercel --prod --yes
   ```
4. **Verificación de workflow cloud**:
   ```bash
   gh workflow run coaching-daily-collect.yml --repo dalarconics/python-garminconnect --ref master
   ```

## 7. Rollback

- **Por task**: Reversión de los commits específicos del branch/worktree asociado (`git revert` o rollback de checkpoint).
- **En Supabase**: En caso de anomalía, la tabla `garmin_tokens` puede truncarse o descartarse mediante `DROP TABLE public.garmin_tokens CASCADE;` sin afectar las demás tablas de coaching. El sistema reasume automáticamente el fallback sobre `GARMINTOKENS_B64`.
- **En Vercel**: Reversión inmediata al deployment previo a través del comando `vercel rollback` o desde el dashboard de Vercel.
