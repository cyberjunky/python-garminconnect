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
