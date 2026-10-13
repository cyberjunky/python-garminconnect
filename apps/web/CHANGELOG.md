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

## [0.3.0] - 2026-10-13

Versión introducida en el PR #2 (rama `ux/audit-2026-10`), enfocada en resolver integralmente la auditoría UX (P1, P2 y P3), unificar la identidad visual de la marca Tri-Coach y asegurar consistencia de datos en Supabase.

### Añadido
- **Accesibilidad (P2)**: Enlaces directos "Saltar al contenido" (`#main-content` y `#chat-main-content`) para navegación por teclado y lectores de pantalla.
- **Accesibilidad (P2)**: Atributo `aria-current="page"` dinámico en la navegación del dashboard y etiquetas `aria-label` / `aria-busy` en el botón Actualizar.
- **Base de datos**: Migración `supabase/migrations/20261013_updated_at_triggers.sql` que crea una función y triggers genéricos `moddatetime` sobre `daily_snapshots`, `training_load` y `garmin_tokens` para actualizar automáticamente `updated_at` en cada modificación.
- **Suite de pruebas**: Tests automatizados (`p1-fixes.test.mjs`, `p2-p3-fixes.test.mjs`, `version.test.mjs`) que validan conversiones de zona horaria, formateo en español, protecciones contra desbordamiento horizontal en CSS y verificación de SemVer.

### Modificado
- **Marca e Identidad (P3)**: Unificación de la marca "Tri-Coach" en reemplazo de "Fitness Coach" a lo largo de la barra lateral, títulos de pestaña, metadatos y documentación.
- **Internacionalización y Copy (P2)**: Traducción completa al español de tipos de deporte (`Carrera`, `Ciclismo`, `Natación`, `Cinta`, etc.) y estados de entrenamiento de Garmin (`Mantenimiento`, `Productivo`, `Recuperación`, `Sobreesfuerzo`, `Desentrenamiento`).
- **Resiliencia en Chat**: Mensajes de error amigables para el usuario en `/api/chat` en español sin filtrar nombres de variables de entorno ni detalles técnicos internos.

### Corregido
- **Zona Horaria y Fechas (P1)**: Corrección del cálculo de fecha "Hoy" y hora de última actividad deportiva para evaluarse estrictamente en la zona horaria `America/Bogota` (UTC-5), eliminando el desfase visual de 5 horas.
- **Body Battery (P1)**: Corrección en el formato del diferencial de Body Battery, evitando signos duplicados como `+-12`.
- **Última Actualización (P1)**: Presentación amigable de timestamp con formato "Actualizado hoy a las HH:mm" o "Actualizado ayer a las HH:mm" en hora local colombiana.
- **Diseño Responsive Móvil (P1)**: Corrección de desbordamiento horizontal en pantallas móviles (375×812) mediante `grid-template-columns: minmax(0, 1fr)`, barra de navegación con scroll horizontal seguro y contenedor con `min-width: 0`.

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
- Eliminación de impresión de tokens sensibles en stdout de CI/CD.

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
