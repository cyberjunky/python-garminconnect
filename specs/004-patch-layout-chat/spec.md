---
schema_version: 1
spec_id: SPEC-004
slug: patch-layout-chat
project_id: python-garminconnect
version: 1
status: approved
autonomy: hitl
owner_task: T-0036
last_updated: '2026-10-17T17:18:42Z'
source: planner T-0036
approved_at: '2026-10-17T17:18:42Z'
decision_ref: memory/mid/decisions.md#dec-011-aprobacion-humana-g0-de-spec-004-y-plan-004
---

# SPEC-004: Corrección de desborde métricas, jerarquía de chat e historial de conversaciones (0.5.1)

- **Origen**: Instrucción humana en HITL - Tri-Coach (`memory/immediate/handoff.md`), task T-0036.
- **Autonomía**: `hitl` (requiere aprobación humana G0 antes de despachar implementers).
- **Versión objetivo**: SemVer `0.5.1` PATCH.

---

## 1. Problema y valor

Tras la liberación de la versión `0.5.0`, la inspección visual humana en producción identificó tres fricciones críticas en la experiencia de usuario del atleta:

1. **Desborde visual en subcomponente «PUNTUACIÓN DE SUEÑO»**:
   - En la tarjeta `TodayCard` (`apps/web/components/TodayCard.tsx`), la cuadrícula `.metrics-grid` utilizaba un dimensionamiento mínimo de columna insuficiente (`minmax(5.5rem, 1fr)` ≈ 88 px).
   - Debido a la ausencia de `min-width: 0` en `.metric-cell` y `.metric-label`, y a que la palabra en mayúsculas `PUNTUACIÓN` (~76 px) es indivisible sin quiebre forzado (`overflow-wrap: break-word`), el contenedor desborda horizontalmente en anchos estándar móviles y desktop angostos.
   - El badge de estado `✓` (`.metric-status-badge`) es forzado fuera del borde derecho de la celda, solapándose sobre la tarjeta contigua de `HRV` e infringiendo la regla de contención geométrica `scrollWidth <= clientWidth`.

2. **Jerarquía visual y ubicación de CoachChat en la vista de Inicio**:
   - En `HomePage` (`apps/web/app/(dashboard)/page.tsx`), `<CoachChat />` se encontraba relegado hacia el final de la página (después de `<RecoveryMilestonesCard />`), obligando al atleta a desplazarse verticalmente más allá de tres tarjetas operativas completas para consultar o dialogar con el entrenador.
   - La instrucción humana solicita revocar este orden histórico y ubicar `<CoachChat />` como primer componente inmediatamente debajo de `<header className="page-header">` y antes de `<TodayCard />`.
   - Para evitar que el chat empuje a `<TodayCard />` por debajo del pliegue de pantalla (*fold*), se requiere un dimensionamiento vertical compacto acotado al **primer cuarto de la pantalla** (~22vh a 25vh), con compositor de 2 filas y desplazamiento interno para conversaciones recientes.

3. **Invisibilidad y desincronización del historial de conversaciones**:
   - Se diagnosticaron tres causas raíz concurrentes en el sistema de chat:
     a) **Token congelado en `null`**: `CoachConversationViewModel` instanciaba y guardaba `accessToken` una sola vez en el montaje inicial del hook (`useCoachConversation.ts`). Cuando `ClientAuthService.getSession()` resolvía el token JWT real, el ViewModel nunca actualizaba su propiedad interna, provocando que las llamadas a `/api/conversations` se emitieran sin credenciales y recibieran `401`.
     b) **Fallo silencioso en carga remota**: En `loadConversations()`, respuestas no exitosas (401 o 500) se ignoraban silenciosamente sin reportar error ni activar contingencias.
     c) **Omisión del historial local superviviente**: En la vista de Inicio y en la pantalla de chat, se omitía la lectura de conversaciones previas almacenadas en el navegador (`localStorage["fitness-coach-chats"]`). Los usuarios sin sesión cloud activa veían la lista vacía (*«Aún no hay conversaciones registradas»*), impidiendo abrir o retomar conversaciones existentes.

El valor entregado por esta especificación es una interfaz estable, libre de desbordamientos geométricos en cualquier resolución, con acceso prioritario y compacto al coach en Inicio, y con sincronización bidireccional y resiliente del historial local y remoto.

---

## 2. Alcance

### Incluye

1. **Corrección geométrica de `.metrics-grid` y celdas métricas** (`apps/web/app/globals.css`, `apps/web/components/TodayCard.tsx`):
   - Ampliación de columna en `.metrics-grid` a `repeat(auto-fit, minmax(7.5rem, 1fr))`.
   - Contención flexible con `min-width: 0; overflow: hidden;` en `.metric-cell`.
   - Distribución alineada en fila con `align-items: flex-start; gap: 0.35rem; min-width: 0;` en `.metric-label-row`.
   - Quiebre tipográfico seguro con `overflow-wrap: break-word; word-break: break-word; min-width: 0; flex: 1 1 auto; line-height: 1.25;` en `.metric-label`.
   - Protección contra compresión con `flex-shrink: 0;` en `.metric-status-badge`.
   - Criterio de verificación geométrica: `scrollWidth <= clientWidth` en todas las celdas de métricas en viewports de 375px a 1600px.

2. **Reubicación y dimensionamiento compacto de CoachChat en Inicio** (`apps/web/app/(dashboard)/page.tsx`, `apps/web/app/globals.css`, `apps/web/components/CoachChat.tsx`):
   - Reordenamiento estructural en `HomePage`: `<CoachChat />` se ubica inmediatamente después de `<header className="page-header">` y antes de `<TodayCard />`.
   - Acotamiento vertical en CSS para `.coach-chat` en Inicio a ~22vh-25vh (con límites acotados `min-height: 180px; max-height: 28vh;`).
   - Compositor compacto con textarea de 2 filas (`min-height: 2.75rem; resize: none;`).
   - Contenedor de últimas conversaciones con desplazamiento vertical interno limpio (`overflow-y: auto`) si excede el espacio disponible.
   - Tarjeta `<TodayCard />` visible inmediatamente debajo en monitores estándar sin requerir scroll vertical excesivo.

3. **Sincronización reactiva de token, historial local y fallback en el chat** (`apps/web/hooks/useCoachConversation.ts`, `apps/web/components/CoachChat.tsx`, `apps/web/components/CoachChatScreen.tsx`, `apps/web/lib/coachStorage.ts`):
   - Incorporación de `setAccessToken(token: string | null): void` en `CoachConversationViewModel` y sincronización reactiva mediante `useEffect` en `useCoachConversation`.
   - Manejo de fallos en `loadConversations()`: captura de errores HTTP y estado no-bloqueante.
   - Fusión deduplicada de conversaciones en `CoachChat.tsx` y `CoachChatScreen.tsx`: unificación de conversaciones remotas con las locales supervivientes obtenidas de `getSurvivingLegacyChats()` en `localStorage["fitness-coach-chats"]`.
   - Apertura y recuperación de conversaciones locales en `CoachChatScreen` ante fallback por ausencia de autenticación remota o fallo 401.
   - Respaldo local inmediato en `localStorage` mediante `upsertChat` al enviar y recibir mensajes para garantizar cero pérdida de datos.
   - Visualización de enlace discreto a `/login` cuando la sincronización cloud requiera sesión de usuario.

4. **Versionado sincronizado SemVer 0.5.1 PATCH** en Grupo R:
   - Actualización atómica en `package.json`, `package-lock.json`, `README.md`, `CHANGELOG.md` y `version.test.mjs`.

### No incluye (No-objetivos)

- **Modificaciones de backend Python** (`garmin_coaching/`, `services/collector/`): El pipeline colector y sus modelos de dominio permanecen inalterados.
- **Nuevas migraciones SQL en Supabase**: No se alteran ni agregan tablas en la base de datos cloud.
- **Reemplazo del proveedor LLM o prompts**: Se mantiene `gpt-6-luna` con `high` reasoning según ADR-005.
- **Rediseño de otras páginas**: No se modifican las rutas `/retos`, `/tendencia`, `/mesociclos` ni `/70-3-cartagena`.
- **Eliminación o desactivación de Supabase Auth**: La sincronización cloud continúa utilizando RLS y sesiones privadas de Supabase Auth.

---

## 3. Historias de usuario

- **HU-1 (Integridad visual en métricas de Hoy)**: Como atleta, quiero consultar el estado de preparación y la celda de Puntuación de Sueño sin desbordamientos de texto ni iconos solapados sobre la tarjeta contigua en mi teléfono o navegador desktop, para evaluar mi recuperación diaria sin confusión visual.
- **HU-2 (Acceso inmediato al entrenador en Inicio)**: Como atleta, quiero encontrar el campo de diálogo con mi entrenador en la parte superior de la pantalla de Inicio ocupando un espacio moderado, para poder escribirle consultas de inmediato sin perder de vista mis métricas de Hoy.
- **HU-3 (Disponibilidad y persistencia del historial de chat)**: Como usuario, quiero acceder a mis conversaciones previas (tanto locales del navegador como remotas) en la sección de últimas conversaciones y en la pantalla completa de chat, y tener la seguridad de que mis mensajes se guardan localmente aunque falle la red o aún no haya iniciado sesión en la nube.
- **HU-4 (Trazabilidad y versión de corrección)**: Como operador del proyecto, quiero que esta corrección se libere formalmente bajo la versión SemVer `0.5.1` (PATCH) con suite automatizada en verde y sin regresiones en la arquitectura limpia del proyecto.

---

## 4. Requisitos EARS y criterios de prueba

Todos los requisitos tienen prioridad `must`. Las referencias Pxx identifican criterios de aceptación ejecutables por máquina.

| ID | Patrón | Requisito | Prioridad | Criterio de aceptación (Pxx) |
|---|---|---|---|---|
| **REQ-001** | Ubicuo | El sistema deberá renderizar la cuadrícula `.metrics-grid` y cada celda `.metric-cell` en `TodayCard` garantizando que el ancho desplazable no exceda el ancho visible (`scrollWidth <= clientWidth`) en cualquier viewport entre 375px y 1600px. | must | **P01**: Test geométrico automatizado comprueba que en las resoluciones de prueba (375px, 390px, 414px, 768px, 800px, 1024px, 1120px, 1440px y 1600px) la celda `PUNTUACIÓN DE SUEÑO` cumple `scrollWidth <= clientWidth`. |
| **REQ-002** | Ubicuo | El sistema deberá aplicar a `.metrics-grid` columnas mínimas de 7.5rem (`repeat(auto-fit, minmax(7.5rem, 1fr))`), contención flexible con `min-width: 0; overflow: hidden;` en `.metric-cell`, alineación vertical en fila (`align-items: flex-start; gap: 0.35rem; min-width: 0;`) en `.metric-label-row`, quiebre de palabra indivisible (`overflow-wrap: break-word; line-height: 1.25; min-width: 0; flex: 1 1 auto;`) en `.metric-label` y badge no compresible (`flex-shrink: 0;`) en `.metric-status-badge`. | must | **P02**: Test automatizado de CSS sobre `apps/web/app/globals.css` valida la existencia y sintaxis exacta de estas declaraciones. |
| **REQ-003** | Ubicuo | La página de Inicio (`apps/web/app/(dashboard)/page.tsx`) deberá renderizar el componente `<CoachChat />` como primer bloque interactivo inmediatamente después de `<header className="page-header">` y antes de `<TodayCard />`. | must | **P03**: Test de AST/marcado JSX de `page.tsx` verifica que `<CoachChat />` precede a `<TodayCard />` en el flujo jerárquico dentro de `<main>`. |
| **REQ-004** | Estado | MIENTRAS se visualice `CoachChat` en la página de Inicio, el sistema deberá acotar su contenedor `.coach-chat` al primer cuarto del viewport (~22vh a 25vh, con límites acotados `min-height: 180px` y `max-height: 28vh`), con textarea compacto de 2 filas y scroll vertical interno en el listado de historial. | must | **P04**: Test de reglas CSS e inspección de componente verifica las cotas de altura de `.coach-chat`, el atributo `rows={2}` en el textarea y la presencia de scroll interno en la lista de conversaciones recientes. |
| **REQ-005** | Evento | CUANDO el token de acceso (`accessToken`) de la sesión de autenticación se obtenga o cambie reactivamente, el sistema deberá actualizar la instancia activa de `CoachConversationViewModel` mediante `setAccessToken(token)` y recargar el listado de conversaciones sin remount del hook. | must | **P05**: Test unitario de `useCoachConversation` simula el paso de `accessToken: null` a `accessToken: "jwt-token-valido"` y verifica que las peticiones a `/api/conversations` incluyen el encabezado `Authorization: Bearer jwt-token-valido`. |
| **REQ-006** | No deseado | SI la petición remota a `/api/conversations` o `/api/conversations/[id]/messages` retorna un código de error HTTP (como 401 o 500) o falla por desconexión de red, ENTONCES el sistema deberá capturar el estado limpiamente sin lanzar excepciones no controladas y permitir el flujo de contingencia local. | must | **P06**: Test unitario en `CoachConversationViewModel` simulando error HTTP 401 y fallo de red comprueba que `isLoading` finaliza en `false`, el error se almacena en el estado y no hay crashes de runtime. |
| **REQ-007** | Ubicuo | El sistema deberá presentar en «Últimas conversaciones» (`CoachChat.tsx`) y en el historial (`CoachChatScreen.tsx`) una lista unificada y deduplicada que combine las conversaciones remotas con las conversaciones locales supervivientes en `localStorage["fitness-coach-chats"]`, permitiendo abrir y continuar cualquiera de ellas en `/chat?conversation=<id>`. | must | **P07**: Test unitario y de componente valida que al haber 2 chats locales y 1 remoto, se presentan todas las conversaciones sin duplicados y se navega correctamente a `/chat?conversation=<id>`. |
| **REQ-008** | Evento | CUANDO se cree una conversación o se envíe un mensaje en `CoachChatScreen` o `useCoachConversation`, el sistema deberá persistir inmediatamente una copia de respaldo en `localStorage["fitness-coach-chats"]` mediante `upsertChat`. | must | **P08**: Test de almacenamiento comprueba que tras enviar un mensaje, `localStorage.getItem("fitness-coach-chats")` contiene el registro actualizado con el mensaje y timestamp reciente. |
| **REQ-009** | Ubicuo | La entrega desplegable final deberá declarar de forma sincronizada la versión SemVer `0.5.1` (PATCH) en `package.json`, `package-lock.json`, `version.test.mjs`, `README.md` y `CHANGELOG.md` mediante reserva serial del grupo `R`. | must | **P09**: Ejecución de `version.test.mjs` y comprobación de integridad documental confirman versión 0.5.1 sin saltos ni degradaciones. |

---

## 5. Restricciones

1. **Clean Architecture (ADR-002, regla de dependencia, Art. VII.2)**:
   - La lógica de formateo, almacenamiento y modelos en `apps/web/lib/coachStorage.ts` y `apps/web/hooks/useCoachConversation.ts` mantiene desacopladas las interfaces de la presentación.
   - Las vistas en `apps/web/app/` y `apps/web/components/` no introducen lógica directa de llamadas SQL ni mutan el estado global sin pasar por los hooks y servicios.
2. **Geometría centrada responsive (ADR-003)**:
   - La página de Inicio mantiene su envolvente `.app-main > main` con ancho máximo de 1120px centrado.
   - Ni el componente `CoachChat` ni `TodayCard` pueden desbordar el viewport horizontalmente ni romper la matriz geométrica en Safari o navegadores WebKit/Blink.
3. **SemVer 0.5.1 PATCH (ADR-009)**:
   - Dado que los cambios son correcciones visuales de layout y mejoras de resiliencia sin alterar contratos de API ni introducir esquemas de base de datos nuevos, el incremento corresponde estrictamente a un `PATCH` (`0.5.0` -> `0.5.1`).

---

## 6. Riesgos y preguntas abiertas

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **R-1: Colisión de altura en pantallas con altura muy reducida (ej. móvil en apaisado < 500px)** | Baja | Media | `.coach-chat` declara `min-height: 180px` y `max-height: 28vh`, con scroll interno para historial y colapso de márgenes, asegurando que el contenido inferior siga siendo accesible. |
| **R-2: Conflicto de ID entre conversación local y remota** | Baja | Baja | La deduplicación utiliza el `id` único (UUID v4) y digest de contenido; la versión remota prevalece en visualización sin destruir la copia local. |
| **R-3: Expiración de sesión JWT durante el uso del chat** | Media | Baja | `useCoachConversation` detecta 401 y permite continuar interactuando con persistencia local de contingencia, mostrando un aviso para reautenticar. |

*Preguntas abiertas*: Ninguna detectada; los requerimientos provienen de observaciones precisas y directivas cerradas de producto.

---

## 7. Criterios de éxito de la spec

- Los 9 requisitos `REQ-001` a `REQ-009` cuentan con pruebas automatizadas (`P01` a `P09`) en verde.
- La suite completa existente de `apps/web` (82 tests actuales) pasa íntegramente al 100% sin regresiones (total ≥ 90 tests).
- Build de producción (`npm run build --prefix apps/web`) exitoso con código de salida 0.
- Verificación visual y geométrica sin desborde horizontal (`scrollWidth <= clientWidth`) en resoluciones de 375px a 1600px.

---

## 8. Seguridad y operación

- **Secretos y credenciales**: Ningún secreto, token persistente ni credencial se almacena en el repositorio ni en los logs. El token de sesión `accessToken` viaja exclusivamente en memoria y en los encabezados HTTP estándar `Authorization: Bearer <token>`.
- **Permisos y superficies expuestas**: No se crean endpoints públicos nuevos. Los endpoints existentes `/api/conversations` y `/api/chat` continúan protegidos mediante autenticación y políticas RLS de Supabase.
- **Datos persistentes y protección**: Las conversaciones locales se almacenan en `localStorage["fitness-coach-chats"]`. Las operaciones de importación y respaldo no eliminan datos históricos locales (política de no-destrucción byte a byte de REQ-011 / SPEC-002).
- **Observabilidad mínima en operación**:
  - *Qué observar*: Tasa de respuestas HTTP 200 en endpoints de chat (`/api/conversations`, `/api/chat`), ausencia de errores de consola por desborde geométrico o token `null`.
  - *Umbral*: 0 excepciones no controladas de frontend; latencia de carga en Inicio < 300 ms.
  - *Duración*: Monitoreo durante las primeras 24 horas posteriores al despliegue.
  - *Criterio de reapertura*: Reporte de desborde horizontal en cualquier dispositivo soportado o pérdida no recuperable de conversaciones.
