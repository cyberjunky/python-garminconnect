# Tri-Coach Web (Phase 2)

Read-only Next.js dashboard for Supabase coaching data.

## Setup

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

## Deploy (Vercel)

Set environment variables:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

No Garmin credentials on Vercel — data comes from Supabase only.

## Versión y cambios

- **Versión actual**: `0.5.1`
- **Novedades en 0.5.1 (SPEC-004)**:
  - **Corrección de desborde métricas en TodayCard**: Cuadrícula con `repeat(auto-fit, minmax(7.5rem, 1fr))`, contención flexible `min-width: 0; overflow: hidden;` en celdas, y quiebre tipográfico seguro `overflow-wrap: break-word` que previene cualquier desborde horizontal de la celda de Puntuación de Sueño (`scrollWidth <= clientWidth`) en resoluciones de 375px a 1600px.
  - **Acceso prioritario y compacto a CoachChat en Inicio**: Reubicación de `CoachChat` inmediatamente tras el encabezado de página y antes de `TodayCard`, con altura acotada a ~25vh (`max-height: 28vh`, `min-height: 180px`), compositor compacto de 2 filas y scroll vertical interno en historial.
  - **Historial sincronizado y respaldo local inmediato**: Sincronización reactiva del `accessToken` JWT en `CoachConversationViewModel` vía `setAccessToken(token)`, unificación deduplicada de conversaciones remotas y locales supervivientes de `localStorage` (`mergeConversations`), fallback local ante fallos de conexión o 401, y persistencia inmediata con `upsertChat` al enviar y recibir mensajes.
- **Novedades en 0.5.0 (SPEC-003)**:
  - **Recomendaciones accionables de ciencia deportiva**: Alertas en «Qué atender» basadas en modulación parasimpática (HRV), cronobiología y deuda de sueño, recarga de Body Battery y ratio de carga aguda:crónica (ACWR < 1.3 de Gabbett).
  - **Tarjeta «Macrociclo» en 4 bloques**: Definición conceptual, momento y fase actual (con techo de FC y duración máxima), pauta práctica de optimización y fecha de culminación en formato `es-CO` con cuenta regresiva a hitos mayores (mmB 2027, Reto Letras 2027, Ironman 70.3 Cartagena 2027).
  - **Nueva ruta dedicada `/tendencia`**: Acceso desde el menú lateral `DashboardNav`, barra proporcional de distribución de zonas (verde, amarillo, rojo), resumen mensual consolidado y tabla de evolución de los últimos 30 días con números tabulares (`tabular-nums`) y diseño centrado responsive (ADR-003).
- **Regla SemVer**: Este proyecto sigue versionado semántico ([SemVer](https://semver.org/lang/es/)) unificado para todo el ecosistema Tri-Coach (aplicación web, recolector Python, workflows de GitHub Actions y esquema Supabase). La versión se incrementa en **MINOR** (0.x.0) para Pull Requests con nuevas funcionalidades o módulos, y en **PATCH** (0.x.y) para correcciones y parches.
- **Historial de cambios**: Consulta [CHANGELOG.md](./CHANGELOG.md) para el detalle de cambios por versión.
