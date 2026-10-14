# ADR-001: Adopción del patrón Layered en apps/web y justificación frente a MVVM

- Estado: aceptado
- Fecha: 2026-10-14
- Decision: DEC-006 (migracion ADR-010 del framework)

## Contexto

El Artículo VII.3 de la Constitución del proyecto (incorporado en la migración ADR-010 del framework) establece que toda aplicación con interfaz de usuario (Android, iOS, web) debe utilizar el patrón arquitectónico MVVM (Model-View-ViewModel), requiriendo justificar por ADR en `memory/long/adr/` cualquier desviación arquitectónica (Art. VII.4).

La aplicación web `apps/web` (Tri-Coach) está construida sobre Next.js 15 con App Router y React Server Components, complementada con el recolector en Python (`services/collector/`, `garmin_coaching/`) y base de datos Supabase.

## Decisión

Adoptar el patrón arquitectónico `layered` (por capas) para `apps/web` y los servicios del proyecto en lugar de MVVM estricto:

1. **Capa de Vista (Presentación)**:
   - Las rutas y páginas del App Router (`apps/web/app/**/page.tsx`, `layout.tsx`) operan como Server Components encargados de renderizar la interfaz estructurada, inyectar metadatos (theme-color, dark scheme) y pasar propiedades iniciales a los componentes hijos.
2. **Capa de Modelo y Servicios**:
   - La lógica de dominio reside centralizada en `apps/web/lib/` (`dashboard.ts`, `preparation.ts`, `condition.ts`, `lastActivity.ts`, `lastUpdated.ts`, `mesocycle.ts`) y clientes Supabase/OpenAI, encapsulando reglas de negocio, modelos de datos, cálculos atléticos (ACWR, preparación, zonas, deltas de Body Battery) y transformaciones.
3. **Componentes de Cliente con Estado**:
   - La lógica de dominio vive en `lib/`, pero `DashboardNav` (sondeo del refresh) y `CoachChatScreen` (fetchReply y envío del chat) conservan estado de vista y orquestación de llamadas en el propio componente.

## Consecuencias y Criterio de Revisión

- **Positivas**: Mantiene una estructura directa, idiomática y ligera para Next.js con Server Components, evitando el sobrecosto de abstracción y boilerplate que implicaría implementar ViewModels desacoplados para pantallas mayoritariamente estáticas.
- **Negativas**: Esa orquestación en client components no cuenta actualmente con tests de componente y mezcla elementos de vista con orquestación de llamadas de red.
- **Criterio de revisión**: Mover dicha orquestación a hooks dedicados o extraerla a `lib/`, así como reevaluar la adopción de MVVM mediante un nuevo ADR si la interfaz de usuario escala en complejidad de estado bidireccional en cliente, forma parte del criterio de revisión arquitectónica.
