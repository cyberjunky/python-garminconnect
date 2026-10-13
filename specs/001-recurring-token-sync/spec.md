---
schema_version: 1
spec_id: SPEC-001
slug: recurring-token-sync
project_id: python-garminconnect
version: 1
status: ready
autonomy: autonomous
owner_task: T-0001
last_updated: '2026-10-11T16:00:00Z'
source: ies planner T-0001
---

# SPEC-001: Sincronización recurrente de tokens y actualización Vercel

## 1. Problema y valor

La sesión de Garmin Connect expira de forma periódica y GitHub Actions se ejecuta en contenedores efímeros sin persistencia nativa, provocando que los tokens renovados se pierdan tras cada ejecución de recolección diaria. Al mismo tiempo, la aplicación web en Vercel (`apps/web`) requiere mantenerse actualizada y desplegada en producción reflejando los datos más recientes almacenados en Supabase, la versión `v0.1.0` y su shell de navegación, sin interrupciones operativas ni intervención manual diaria.

## 2. Alcance

### Incluye

- Creación y migración de la tabla `garmin_tokens` en Supabase con Row Level Security (RLS) habilitado y acceso exclusivo para el rol `service_role`.
- Adaptador y utilidades en Python (`services/collector/supabase_client.py` y `scripts/garmin_auth.py`) para persistir y restaurar de forma bidireccional los tokens de Garmin desde Supabase.
- Actualización del workflow de GitHub Actions (`coaching-daily-collect.yml`) para restaurar tokens desde Supabase (con fallback secundario a `GARMINTOKENS_B64`) y persistir los tokens renovados al culminar la recolección.
- Actualización de los scripts de mantenimiento local (`scripts/refresh_garmin_session.py` y `scripts/publish_garmin_tokens_secret.sh`) para sincronizar tokens hacia Supabase y actualizar el secreto en GitHub mediante `gh` CLI.
- Construcción y despliegue a producción de `apps/web` en Vercel verificando build limpio, navegación y visualización de datos frescos.
- Manejo defensivo contra fallos de autenticación: registro limpio de alertas, sin fugas de secretos en logs ni sobreescritura de tokens con datos nulos.

### No incluye (no-objetivos)

- Modificación de la librería central de OAuth/Garth de Garmin Connect.
- Exposición de tokens o credenciales al cliente web o al rol anónimo de Supabase (`anon`).
- Infraestructura multi-usuario externa a la arquitectura actual del MVP.

## 3. Historias de usuario

- **HU-1**: Como atleta y usuario del coach, quiero que el sistema recopile automáticamente y a diario mis métricas de Garmin sin requerir logins manuales periódicos, para consultar mi estado de readiness y plan de entrenamiento siempre al día.
- **HU-2**: Como usuario de la aplicación web en Vercel, quiero acceder a la interfaz de producción y ver los datos de hoy sincronizados, con navegación fluida y sin pantallas de error ni datos obsoletos.
- **HU-3**: Como operador de infraestructura, quiero que los tokens de Garmin se almacenen de forma segura y centralizada en Supabase con RLS, evitando almacenar secretos en texto plano o que los runners queden desincronizados.

## 4. Requisitos (EARS)

| ID | Patrón | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|---|
| REQ-001 | Ubicuo | El sistema deberá persistir y sincronizar los tokens de autenticación de Garmin Connect en la tabla `garmin_tokens` de Supabase accesible exclusivamente mediante el rol `service_role` con Row Level Security (RLS) habilitado, bloqueando todo acceso público/anon. | must | test: `tests/test_garmin_tokens_supabase.py` valida creación de esquema, upsert/select vía `service_role` y denegación explícita para rol `anon`. |
| REQ-002 | Evento | CUANDO el workflow `coaching-daily-collect.yml` se ejecute en GitHub Actions, el sistema deberá restaurar los tokens más recientes desde Supabase con fallback a `GARMINTOKENS_B64`, y tras completar exitosamente la recolección o refresco, deberá persistir los tokens actualizados nuevamente en Supabase. | must | test: Ejecución controlada o simulada de recolección validando flujo completo de lectura de tokens desde Supabase, refresco y re-guardado con timestamp actualizado. |
| REQ-003 | Evento | CUANDO se ejecute la sincronización o refresco local en el entorno de desarrollo (mediante `scripts/refresh_garmin_session.py` o `scripts/publish_garmin_tokens_secret.sh`), el sistema deberá sincronizar los tokens de Garmin hacia Supabase y actualizar el secreto `GARMINTOKENS_B64` en GitHub via `gh secret set` si existen credenciales configuradas. | must | test: `scripts/publish_garmin_tokens_secret.sh` y `scripts/refresh_garmin_session.py` completan sincronización a Supabase y validan presencia de tokens actualizados. |
| REQ-004 | Ubicuo | El sistema deberá mantener desplegada y verificada la aplicación web `apps/web` en el entorno de producción de Vercel con un build limpio (sin errores de TypeScript ni lint), visualizando las métricas más recientes de Supabase y reflejando la versión `v0.1.0`. | must | test: `npm --prefix apps/web run build` finaliza con código 0 y `vercel --prod` confirma despliegue activo con respuesta HTTP 200 y visualización de snapshot actual. |
| REQ-005 | No deseado | SI falla la autenticación de tokens en el cloud o la respuesta de Garmin Connect no contiene una sesión válida, ENTONCES el sistema deberá registrar una alerta clara sin filtrar tokens ni credenciales en stdout/stderr y abstenerse de sobreescribir los tokens persistidos en Supabase con datos nulos o vacíos. | must | test: `tests/test_garmin_tokens_supabase.py` valida que fallos de autenticación provocan terminación controlada sin mutar el registro en Supabase y sin emitir secretos en logs. |

## 5. Restricciones

- **Seguridad**: Cero credenciales ni tokens en commits o logs. La tabla `garmin_tokens` en Supabase no debe poseer ninguna directiva que otorgue permisos a `anon` ni a usuarios no autenticados.
- **Permisos locales**: Los archivos de tokens en disco deben mantener permisos restrictivos `0o600` para archivos y `0o700` para directorios.
- **Constitución**: Conformidad con los artículos de la constitución del proyecto (Art. I Autoridad, Art. II Spec primero, Art. III Calidad con tests primero, Art. IV Seguridad sin secretos).
- **Compatibilidad**: Integración limpia con Python 3.12 y Next.js 15 en Node.js 20+.

## 6. Riesgos y preguntas abiertas

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Reto de bot/Cloudflare o bloqueo temporal en Garmin Connect durante refresco en GitHub Actions | Baja | Alto | Usar tokens renovados existentes (`_token_expires_soon`), respaldar en Supabase y mantener fallback local asistido por Keychain en el Mac. |
| Falla de red transitoria con Supabase al guardar tokens | Baja | Media | Operaciones idempotentes con reintentos y tolerancia a fallo en el almacenamiento secundario sin interrumpir la entrega de datos recolectados. |
| Desincronización entre GitHub secret y Supabase | Baja | Baja | Supabase actúa como fuente primaria viva; el secreto en GitHub actúa como red de seguridad de contingencia. |

Preguntas abiertas: Ninguna bloqueante identificada para esta iteración.

## 7. Criterios de éxito de la spec

- Todos los requisitos (REQ-001 a REQ-005) implementados y cubiertos por pruebas verificables.
- Pipeline `coaching-daily-collect.yml` ejecutando de manera autónoma y manteniendo el ciclo de vida del token.
- Aplicación `apps/web` desplegada y operativa en producción en Vercel con build limpio y datos del día.
