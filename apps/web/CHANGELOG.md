# Historial de cambios de Tri-Coach

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Semantic Versioning (SemVer)](https://semver.org/lang/es/).

> **Nota sobre el alcance**: Este CHANGELOG cubre de forma unificada todo el sistema **Tri-Coach**:
> - Aplicación web y dashboard Next.js (`apps/web`).
> - Recolector de datos y análisis fisiológico en Python (`garmin_coaching/`, `services/collector/`, `scripts/garmin_auth.py`).
> - Flujos de automatización de CI/CD en GitHub Actions (`.github/workflows/`).
> - Esquema de base de datos y migraciones de Supabase (`supabase/migrations/`).
>
> La versión canónica del sistema vive en `apps/web/package.json` y se incrementa en MINOR para cada PR de funcionalidad y en PATCH para PRs de corrección o parches.

---

## [0.5.2] - 2026-10-20

Versión de parche de `T-0039` (`DEC-009`): el CI de `master` vuelve a llegar a pytest. Sin cambios de comportamiento en la app web ni en el recolector.

### Corregido
- **Lint del código Python de Tri-Coach (`garmin_coaching/`, `services/`, `scripts/`, `garmin_mcp/`)**: `ruff check` (0.17.1) pasa de 107 hallazgos a 0 con arreglos automáticos seguros (orden de imports, imports sin usar, `datetime.UTC`), refactors equivalentes y `noqa` con motivo donde el patrón es intencional. Los `except Exception: pass` de `login_client` se mantienen hasta `T-0040`, que los sustituye por logging.
- **Docstrings (`pyproject.toml`)**: `D101` y `D103` se ignoran en el código de la app (adopción gradual, como `D102`); la librería `garminconnect/` sigue con la regla completa.
- **Formato**: `ruff format` en 25 archivos. `deliverables/`, `specs/` y `memory/` (artefactos IES) quedan fuera de ruff para no reescribir registros históricos.

---

## [0.5.1] - 2026-10-17

Versión de parche de `SPEC-004` (`PLAN-004`, `DEC-011`, `ADR-002`, `ADR-003`, `ADR-008`), corrigiendo el desborde geométrico en la tarjeta de Hoy, reposicionando el chat del coach al inicio de forma compacta y sincronizando reactivamente el historial de conversaciones:
- Corrección geométrica y tipográfica integral de `.metrics-grid` y celdas métricas en `TodayCard` eliminando el desborde horizontal de la celda «PUNTUACIÓN DE SUEÑO» (`scrollWidth <= clientWidth`) en cualquier resolución de 375px a 1600px.
- Reposicionamiento prioritario de `CoachChat` como primer componente en la vista de Inicio inmediatamente tras `page-header` y antes de `TodayCard`, con altura compacta acotada a ~25vh (`max-height: 28vh`, `min-height: 180px`), compositor de 2 filas y scroll vertical interno en historial.
- Sincronización reactiva de `accessToken` en `CoachConversationViewModel` vía `setAccessToken(token)` para emitir llamadas autenticadas con cabecera `Authorization: Bearer <token>` tan pronto se resuelve la sesión.
- Captura y manejo resiliente de respuestas no exitosas (401/500) y fallos de red en `loadConversations()` sin lanzar excepciones no controladas.
- Función de utilidad pura `mergeConversations(remote, local)` en `lib/coachStorage.ts` para unificar y deduplicar conversaciones remotas y locales supervivientes de `localStorage["fitness-coach-chats"]` en `CoachChat` y `CoachChatScreen`.
- Fallback automático a conversaciones y mensajes locales en `CoachChatScreen` ante sesiones no autenticadas o fallos 401.
- Respaldo local inmediato en `localStorage` con `upsertChat` al enviar y recibir mensajes para garantizar cero pérdida de datos.
- Suite de pruebas de regresión y validación de patch `apps/web/lib/patch-layout-chat.test.mjs` cubriendo requisitos `REQ-001` a `REQ-009` (`P01` a `P09`).

### Corregido
- **Desborde métricas en TodayCard (`apps/web/app/globals.css`)**: Columnas ampliadas con `repeat(auto-fit, minmax(7.5rem, 1fr))`, contención con `min-width: 0; overflow: hidden;` en `.metric-cell`, alineación flexible con `align-items: flex-start; gap: 0.35rem; min-width: 0;` en `.metric-label-row`, quiebre seguro de palabra indivisible con `overflow-wrap: break-word; line-height: 1.25;` en `.metric-label` y badge protegido contra compresión con `flex-shrink: 0;` (`REQ-001`, `REQ-002`, `P01`, `P02`).
- **Jerarquía y altura de CoachChat en Inicio (`apps/web/app/(dashboard)/page.tsx`, `apps/web/app/globals.css`, `apps/web/components/CoachChat.tsx`)**: Reubicación antes de `TodayCard`, dimensionamiento acotado con `max-height: 28vh; min-height: 180px;`, compositor compacto de 2 filas (`rows={2}`) y scroll interno (`overflow-y: auto`) en `.coach-history` (`REQ-003`, `REQ-004`, `P03`, `P04`).
- **Sincronización de token y resiliencia en ViewModel (`apps/web/hooks/useCoachConversation.ts`)**: Adición de `setAccessToken(token: string | null)` reactivo, manejo seguro de respuestas 401 y 500 en `loadConversations()` y `loadMessages()` sin excepciones no capturadas (`REQ-005`, `REQ-006`, `P05`, `P06`).
- **Historial unificado y persistencia inmediata (`apps/web/lib/coachStorage.ts`, `apps/web/components/CoachChat.tsx`, `apps/web/components/CoachChatScreen.tsx`)**: Implementación de `mergeConversations(remote, local)`, lectura de conversaciones locales supervivientes con `getSurvivingLegacyChats()`, visualización unificada en Inicio y barra lateral, fallback a mensajes locales y persistencia inmediata de mensajes en `localStorage` vía `upsertChat` (`REQ-007`, `REQ-008`, `P07`, `P08`).

---

## [0.5.0] - 2026-10-17

Versión final integral de `SPEC-003` (`PLAN-003`, `DEC-010`, `ADR-002`, `ADR-003`, `ADR-007`), introduciendo el motor de recomendaciones fisiológicas, la tarjeta Macrociclo en 4 bloques y la nueva ruta analítica de tendencia mensual:
- Motor de recomendaciones accionables de ciencia deportiva en «Qué atender» basadas en modulación parasimpática, cronobiología del sueño, recarga autonómica y ratio ACWR de Gabbett.
- Tarjeta «Macrociclo» enriquecida pedagógicamente en 4 bloques: definición conceptual, momento/fase actual con techos fisiológicos (FC y duración), pauta práctica de optimización y fecha de término en formato `es-CO` con cuenta regresiva a hitos de la temporada.
- Nueva ruta dedicada `/tendencia` en menú lateral `DashboardNav` con distribución visual de zonas (30 días), resumen mensual consolidado y tabla con números tabulares (`tabular-nums`) en contenedor centrado max 1120px (ADR-003).
- Runner unificado de pruebas `apps/web/lib/tendencia-macrociclo.test.mjs` que integra las suites de SPEC-003 bajo `npm test`.

### Añadido
- **Recomendaciones accionables de ciencia deportiva (`apps/web/lib/dashboard.ts`)**: Funciones puras tipadas `buildFocusRecommendations` y `buildFocusItems` que emiten directrices de entrenamiento precisas según umbrales fisiológicos (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `P01`–`P06`).
- **Tarjeta Macrociclo en 4 bloques (`apps/web/lib/mesocycle.ts`, `apps/web/app/(dashboard)/retos/page.tsx`)**: Función de dominio `getMacrocycleDetails` y renderizado de bloques A (definición), B (fase actual con código, foco, deporte, techo FC y duración máxima), C (cómo mejorarla según fase y fatiga) y D (cierre de fase en formato `es-CO`, días restantes y cuenta regresiva a mmB, Reto Letras y 70.3 Cartagena) (`REQ-007`, `REQ-008`, `REQ-009`, `REQ-010`, `REQ-011`, `P07`–`P11`).
- **Ruta dedicada `/tendencia` (`apps/web/app/(dashboard)/tendencia/page.tsx`)**: Server Component analítico con barra horizontal interactiva de zonas (verde, amarillo, rojo), tarjetas de resumen fisiológico mensual y tabla diaria de los últimos 30 días (`REQ-014`, `REQ-015`, `REQ-016`, `REQ-017`, `REQ-018`, `P14`–`P18`).
- **Cálculo puro y agregador de tendencia (`apps/web/lib/tendencia.ts`)**: Funciones puras `calculateMonthlyZoneDistribution`, `calculateMonthlySummary` y formateador de tabla con tolerancia a datos parciales o vacíos, más adaptador de lectura `fetchMonthlyTrend` (`REQ-015`, `REQ-016`, `REQ-018`, `REQ-019`).
- **Navegación permanente en menú lateral (`apps/web/components/DashboardNav.tsx`)**: Enlace permanente hacia `/tendencia` con icono de tendencia, etiqueta textual y estado activo dinámico con `aria-current="page"` (`REQ-013`, `P13`).
- **Suite runner de pruebas consolidada (`apps/web/lib/tendencia-macrociclo.test.mjs`)**: Suite nativa que ejecuta las pruebas de recomendaciones, macrociclo, tendencia mensual y Clean Architecture bajo `npm test` (`REQ-020`, `P20`).

### Modificado
- **Vista de retos (`apps/web/app/(dashboard)/retos/page.tsx`)**: Retiro de la tarjeta «Tendencia 14d» para descongestionar la pantalla operativa, integrando las nuevas recomendaciones en «Qué atender» y la tarjeta Macrociclo en 4 bloques (`REQ-012`, `P12`).
- **Estilos globales (`apps/web/app/globals.css`)**: Estilos para la barra proporcional de zonas, badges de porcentaje, grid de resumen mensual y soporte de tipografía `font-variant-numeric: tabular-nums` en celdas numéricas.

---

## [0.4.0] - 2026-10-17

Versión final integral de `SPEC-002` (`PLAN-002`, `DEC-009`, `ADR-002`, `ADR-003`, `ADR-004`, `ADR-005`), consolidando las tres etapas (`I-UI`, `I-SERVER`, `I-CLIENT`):
- Centrado responsive del dashboard a un ancho máximo de 1120px en Safari y móvil.
- Historial sincronizado privado y persistente en Supabase con Row Level Security y control de concurrencia e idempotencia.
- Flujo de autenticación Supabase Auth mediante email OTP (`apps/web/app/login/page.tsx`).
- ViewModel desacoplado (`apps/web/hooks/useCoachConversation.ts`) según Clean Architecture (MVVM).
- Estados de guardado visibles («Guardado»), manejo de errores sin pérdida de borradores y reintento idempotente.
- Paginación continua del historial sin límite de cuatro entradas ni descarte de mensajes.
- Importación local opt-in con confirmación explícita de cuenta destino y comparación de digests, conservando el `localStorage` original 100% íntegro e inalterado byte a byte.
- Retiro definitivo del selector de modelos y fijación estática de la etiqueta informativa «GPT-6 Luna · High».

### Añadido
- **Pantalla de login y sesión privada (`apps/web/app/login/page.tsx`)**: Formulario con solicitud y verificación de código OTP por email, integración con `ClientAuthService` (`apps/web/lib/infra/auth/clientAuthService.ts`), soporte de redirecciones y limpieza de sesión segura (`REQ-004`, `REQ-013`, `P04`, `P13`).
- **ViewModel de chat y desacoplamiento de componentes (`apps/web/hooks/useCoachConversation.ts`)**: Implementación del ViewModel interactivo para `CoachChat` y `CoachChatScreen` aislando llamadas de red, estado de guardado, actualización optimista y resolución de conflictos 409 (`REQ-022`, `P22`).
- **Estados de sincronización y reintento en chat**: Notificación visual de guardado confirmado en servidor, preservación de borradores ante fallos de red o 5xx, y reintento con reutilización de `operationId` para evitar duplicados (`REQ-006`, `REQ-008`, `REQ-009`, `REQ-010`, `P06`, `P08`, `P09`, `P10`).
- **Paginación de conversaciones**: Carga por páginas (`limit=20`, `offset`) sin truncar ni descartar conversaciones existentes en el cliente (`REQ-007`, `P07`).
- **Importación local opt-in segura (`apps/web/lib/coachStorage.ts`)**: Funciones `getSurvivingLegacyChats`, `computeChatDigest` y `executeOptInImport` que exigen confirmación de cuenta, detectan snapshots idénticos mediante digest SHA-256, gestionan errores parciales y garantizan que el almacenamiento `localStorage` original permanezca estrictamente inalterado byte a byte (`REQ-011`, `REQ-012`, `P11`, `P12`).
- **Etiqueta estática de modelo exclusivo (`CoachModelSelect.tsx`)**: Sustitución definitiva del selector interactivo `<select>` por una insignia estática que identifica «GPT-6 Luna · High» (`REQ-017`, `P17`).
- **Estilos globales responsivos (`apps/web/app/globals.css`)**: Estilos para la vista de login, modal de importación opt-in, badges de guardado y botones de reintento, preservando el centrado max 1120px en dashboard y 880px en compositor.

### Modificado
- **Componentes de UI de chat (`CoachChat.tsx`, `CoachChatScreen.tsx`)**: Migración de llamadas directas y almacenamiento local hacia `useCoachConversation`, integrando opciones de importación, historial sincronizado y cierre de sesión.

---

## [0.4.0-rc.2] - 2026-10-17

Candidato de release de la etapa `I-SERVER` de `SPEC-002` (`PLAN-002`, `ADR-002`, `ADR-004`, `ADR-005`), enfocado en la persistencia privada en base de datos bajo Supabase Auth con RLS, endpoints de historial y chat con control de concurrencia e idempotencia, forzado exclusivo de `gpt-6-luna` con `reasoning_effort: high` sin tools, aislamiento de contexto de salud MVP por vínculo owner y ventana de 12 mensajes.

### Añadido
- **Migración SQL aditiva y RLS privado (`20261017_coach_history.sql`)**: Creación de tablas `coach_conversations`, `coach_messages`, `coach_operations`, `coach_imports` y `coach_profile_links` con Row Level Security habilitado (`auth.uid() = owner_id`), claves foráneas compuestas de aislamiento de propietario y revocación estricta de permisos para rol `anon` (`REQ-004`, `REQ-005`, `P04`, `P05`).
- **Arquitectura limpia de chat (`apps/web/lib/chat/` e `infra/`)**: Implementación de entidades de dominio puras (`Conversation`, `Message`, `Operation`, validación de 4000 caracteres), puertos de aplicación (`IConversationRepository`, `IIdentityService`, `IHealthContextPort`, `ICoachProviderPort`) y adaptadores en `lib/infra/` (`chat`, `auth`, `health`, `coach`) bajo la regla de dependencia P22 (`ADR-002`).
- **Endpoints de API privados con cache `no-store`**: Rutas `/api/conversations` (listar y crear conversaciones) y `/api/conversations/[id]/messages` (historial cronológico de mensajes) con autenticación Supabase Bearer JWT, paginación y cabecera `Cache-Control: no-store` (`REQ-007`).
- **Idempotencia y control de concurrencia con lease**: Reclamación transaccional de operaciones en `/api/chat` con lease de 30 segundos; reintentos o doble clic devuelven la respuesta persistida sin duplicar inferencia ni mensajes en DB (`REQ-009`, `P09`), y colisiones de revisión responden deterministamente con HTTP 409 (`REQ-010`, `P10`).
- **Forzado exclusivo de modelo en servidor (`OpenAiCoachProvider`)**: Ejecución fija de `gpt-6-luna` con `reasoning_effort: high`, sin `temperature`, sin `tools` ni function calling, y sin fallback a modelos alternativos ante errores del proveedor (`REQ-015`, `REQ-016`, `P15`, `P16`).
- **Aislamiento de salud y retención íntegra**: Verificación estricta de vínculo a perfil MVP en servidor (`REQ-014`, `P14`); retención íntegra de mensajes en base de datos mientras se entrega una ventana de los últimos 12 mensajes al coach (`REQ-018`, `P18`).
- **Logging técnico sanitizado**: Formateo estructurado de logs de auditoría conteniendo únicamente metadatos opacos (`operation_id`, `conversation_id`, duración, código de estado), sin registrar datos de salud, emails ni tokens (`REQ-019`, `P19`).

### Modificado
- **Refactorización de infraestructura**: Reubicación de `apps/web/lib/supabase.ts` y `apps/web/lib/openaiModels.ts` hacia `apps/web/lib/infra/` conforme a `ADR-002`, actualizando importaciones en `condition.ts`, `dashboard.ts` y páginas del dashboard sin romper compatibilidad.

---

## [0.4.0-rc.1] - 2026-10-17

Candidato de release de la etapa `I-UI` de `SPEC-002` (`PLAN-002`, `ADR-003`), centrado en corregir la distribución responsive del contenedor principal del dashboard en Safari preservando la composición independiente del chat.

### Corregido
- **Centrado y ancho útil responsive del dashboard (SPEC-002 / REQ-001, REQ-002, REQ-003)**: Acotación del contenedor `.app-main > main` con `width: 100%`, `max-width: 1120px`, `margin: 0 auto` y `padding` lateral de `28px` en viewports `> 800px` y `16px` en `<= 800px`, eliminando el desplazamiento hacia la izquierda en pantallas amplias de Safari sin alterar el layout independiente de `/chat` (`.chat-main` a ancho completo, compositor `.chat-composer` centrado hasta `880px` y burbujas alineadas por rol) ni el scroll horizontal interno de gráficas (`.prep-chart-wrap`) y tablas (`.projection-table-wrap`).

### Añadido
- **Pruebas de geometría y arquitectura (`layout-responsive.test.mjs`)**: Verificación automatizada de las reglas de geometría `G` en las 14 celdas de la matriz `S` (SPEC-002 §5), preservación del layout de chat y comprobación ejecutable de la regla de dependencia de Clean Architecture (`REQ-022` / `P22`).

---

## [0.3.0] - 2026-10-13

Versión introducida en el PR #2 (rama `ux/audit-2026-10`), enfocada en resolver integralmente la auditoría UX (P1, P2 y P3), unificar la identidad visual de la marca Tri-Coach y asegurar consistencia de datos en Supabase.

### Añadido
- **Accesibilidad (P2)**: Anillo global `:focus-visible` en toda la interfaz y estilo `:focus-within` en el compositor de chat.
- **Accesibilidad (P2)**: Etiquetas `<label>` y `aria-label` en textareas de chat (`CoachChat`, `CoachChatScreen`).
- **Accesibilidad (P2)**: Enlaces directos "Saltar al contenido" (`#main-content` y `#chat-main-content`) para navegación por teclado y lectores de pantalla.
- **Accesibilidad (P2)**: Atributo `aria-current="page"` dinámico en la navegación del dashboard y etiquetas `aria-label` / `aria-busy` en el botón Actualizar.
- **Accesibilidad (P2)**: Estados de métricas comunicados con indicadores visuales y textuales (✓/!) además del color del borde en la tarjeta Hoy.
- **Accesibilidad (P2)**: Región viva `role="alert"` para errores en el chat y respeto a la preferencia de usuario `prefers-reduced-motion` en scroll suave y transiciones.
- **Diseño y Tema (P1 / P3)**: Configuración de `color-scheme: dark` y metadatos `theme-color` en el layout para controles nativos oscuros coherentes.
- **Base de datos (P1)**: Migración `supabase/migrations/20261013_updated_at_triggers.sql` con la función propia `public.set_updated_at()` y triggers `before update` en 6 tablas (`daily_snapshots`, `readiness_daily`, `training_load`, `session_log`, `weekly_sport_load`, `garmin_tokens`), más el envío de `updated_at` explícito desde el collector Python en cada upsert.
- **Suite de pruebas**: Tests automatizados (`p1-fixes.test.mjs`, `p2-p3-fixes.test.mjs`, `version.test.mjs`) que validan conversiones de fecha, formateo en español, protecciones de desbordamiento horizontal y conformidad SemVer.

### Modificado
- **Jerarquía en Inicio (P3)**: Reorganización visual posicionando la tarjeta Hoy antes que el compositor de chat.
- **Marca e Identidad (P3)**: Unificación de la marca "Tri-Coach" en reemplazo de "Fitness Coach" a lo largo de la barra lateral, encabezado `<h1>`, títulos de pestaña, metadatos y documentación.
- **Copy y Consistencia (P3)**: Unificación del copy al español sin términos en inglés crudos (`Carrera`, `Ciclismo`, `Natación`, `Mantenimiento`, `Recuperación`, etc.) y eliminación de mensajes de depuración técnicos en la interfaz pública.
- **Formateo Numérico y Fechas (P3)**: Fechas formateadas en español colombiano mediante `Intl.DateTimeFormat("es-CO")` y cifras/tablas con tipografía `font-variant-numeric: tabular-nums`.
- **Navegación Móvil (P1 / P3)**: Barra de navegación compacta con botón Actualizar fijo en la barra móvil, eliminando el menú vertical invasivo de 336 px (41% de pantalla).
- **Tarjeta de Recuperación (P1)**: Fase de recuperación dinámica obtenida desde `payload.macrocycle`, retirando la fecha meta fija y obsoleta.

### Corregido
- **Hora de Última Actividad (P1)**: Corrección en `lib/lastActivity.ts` para mostrar la hora local registrada por Garmin sin desfase de 5 horas.
- **Fecha de Mesociclos y Dashboard (P1)**: Cálculo de fecha local en zona horaria de Bogotá (UTC-5) para evitar el salto prematuro de día a las 19:00 locales originado por fechas UTC.
- **Body Battery (P1)**: Corrección del diferencial de Body Battery en la tarjeta Hoy, evitando signos duplicados como `+-12`.
- **Diseño Responsive Móvil (P1)**: Corrección de desbordamiento horizontal en pantallas móviles (375×812) mediante `minmax(0, 1fr)` con `scrollWidth == 375`, y gráfica de preparación física con contenedor de scroll horizontal para garantizar su legibilidad en pantallas de 320–375 px.

---

## [0.2.0] - 2026-10-13

Versión integrada a `master` en el merge `0d81139` (PR #1). Introduce la arquitectura de navegación con shell de barra lateral, asistente conversacional con OpenAI, sincronización bajo demanda y gestión de tokens en Supabase.

### Añadido
- **Shell y Barra Lateral**: Nueva interfaz con barra lateral persistente (`DashboardNav`), navegación entre secciones y presentación de versión en pie de barra.
- **Asistente Coach con IA**: Interfaz de chat integrada (`/chat`, `CoachChat`, `CoachChatScreen`) conectada a modelos de OpenAI (incluyendo soporte reasoning o-series) para responder preguntas sobre métricas de entrenamiento.
- **Botón Actualizar bajo demanda**: Disparo manual de la acción de GitHub Actions vía `workflow_dispatch` desde la interfaz web (`/api/refresh`) con sondeo de estado y notificación en vivo.
- **Persistencia de Última Actividad**: Integración de la última sesión deportiva en la base de datos y visualización mediante `LastActivityCard` (commit `b13aa16` del 3 de octubre de 2026).
- **Gestión Cloud de Tokens Garmin (SPEC-001)**: Sincronización bidireccional y persistencia recurrente de tokens de sesión Garmin Connect en la tabla `public.garmin_tokens` de Supabase, eliminando la degradación de autenticación en GitHub Actions.

### Seguridad
- Políticas Row Level Security (RLS) estrictas en `public.garmin_tokens` para restringir el acceso exclusivamente al rol de servicio (`service_role`), bloqueando lectura e inserción para el rol público `anon`.

---

## [0.1.0] - 2026-09-25

Versión inicial MVP de Tri-Coach, culminada en el commit `102430e` (2026-09-20..25).

### Añadido
- **Dashboard MVP**: Vista de métricas clave del día (`TodayCard`) consumiendo datos consolidados de Supabase.
- **Gráfica de Preparación**: Visualización del índice de preparación física 0–100 (`PreparationChart`) basado en readiness, carga, edad aeróbica y recuperación.
- **Mesociclos**: Desglose y cálculo de volumen semanal por disciplinas en preparación hacia metas deportivas.
- **Objetivo 70.3 Cartagena**: Módulo dedicado al seguimiento de hitos de entrenamiento para la carrera Ironman 70.3 Cartagena.
- **Pipeline de Recolección Diario**: Workflow programado en GitHub Actions (`coaching-daily-collect.yml`) que extrae métricas de Garmin Connect y las guarda en `daily_snapshots` y `training_load`.
- **Marca Temporal**: Visualización de fecha y hora de última sincronización en el encabezado del dashboard en hora de Bogotá.
