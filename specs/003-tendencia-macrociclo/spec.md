---
schema_version: 1
spec_id: SPEC-003
slug: tendencia-macrociclo
project_id: python-garminconnect
version: 1
status: approved
autonomy: hitl
owner_task: T-0031
last_updated: '2026-10-17T15:52:39Z'
source: planner T-0031
approved_at: '2026-10-17T15:52:39Z'
decision_ref: memory/mid/decisions.md#dec-010-aprobacion-humana-g0-de-spec-003-y-plan-003
---

# SPEC-003: Tendencia mensual, macrociclo en 4 bloques y recomendaciones accionables de ciencia deportiva

- **Origen**: Instrucción humana en HITL - Tri-Coach (`memory/immediate/handoff.md`), task T-0031.
- **Autonomía**: `hitl` (requiere aprobación humana G0 antes de despachar implementers).
- **Versión objetivo**: SemVer `0.5.0` MINOR.

---

## 1. Problema y valor

El dashboard de Tri-Coach presenta tres oportunidades de mejora en la experiencia del atleta:
1. **Recomendaciones en «Qué atender»**: Actualmente, las alertas en `/retos` se limitan a constatar déficits numéricos (ej. *«Sueño 6.2 h — meta ≥7.5 h»*), sin orientar al atleta sobre qué acción específica y fisiológica debe tomar para corregir la desviación.
2. **Tarjeta «Macrociclo»**: La tarjeta actual en `/retos` solo muestra el código, nombre y foco genérico (ej. *«R1 Base aeróbica · 80/20 Z1-Z2»*), sin explicar pedagógicamente qué es un macrociclo, cuáles son los límites de seguridad de la fase activa (techo de frecuencia cardíaca y duración máxima), cómo optimizarla día a día y cuántos días restan para su culminación e hitos mayores.
3. **Tendencia y progreso mensual**: La tarjeta «Tendencia 14d» en `/retos` satura la vista operativa diaria con una tabla reducida de dos semanas, mientras que el atleta carece de una perspectiva mensual integral (últimos 30 días) que consolide la distribución de zonas, el progreso fisiológico promedio (HRV, sueño, Body Battery, estrés, carga ACWR y VO₂max) y un historial detallado accesible desde el menú principal.

El valor entregado es una plataforma de entrenamiento que no solo diagnostica métricas, sino que prescribe pautas accionables basadas en ciencia deportiva, clarifica la periodización plurianual y ofrece una vista dedicada de tendencia mensual en un contenedor centrado y responsive.

---

## 2. Alcance

### Incluye

1. **Recomendaciones de ciencia deportiva en «Qué atender»** (`apps/web/app/(dashboard)/retos/page.tsx` y `apps/web/lib/dashboard.ts`):
   - Cada indicador fuera de umbral incluye una frase corta accionable fundamentada en:
     - Modulación parasimpática / HRV (tono vagal, recuperación activa Z1, respiración diafragmática).
     - Higiene y deuda de sueño (cronobiología, adelanto de horario, retiro de pantallas/luz azul).
     - Recarga autonómica / Body Battery (reducción de estresores nocturnos, cenas tardías/alcohol).
     - Ratio de carga aguda:crónica (ACWR < 1.3 de Gabbett para prevención de lesiones).
     - Descarga ante sobreesfuerzo / overreaching (fatiga no funcional, descarga o descanso total).
     - Mensaje afirmativo de ejecución cuando los indicadores están en VERDE.
2. **Tarjeta «Macrociclo» estructurada en 4 bloques** (`apps/web/app/(dashboard)/retos/page.tsx` y `apps/web/lib/mesocycle.ts`):
   - **Bloque A (Definición)**: Breve explicación pedagógica de qué es un macrociclo y su propósito en la temporada.
   - **Bloque B (Fase actual)**: Código (`code`), nombre (`name`), foco (`focus`), deporte(s) prescritos (`sport`), techo de FC (`hr_cap` bpm) y duración máxima por sesión (`max_duration_min`).
   - **Bloque C (Cómo mejorarla)**: Recomendación práctica contextualizada a la fase activa y adaptada al estado de preparación/fatiga del atleta.
   - **Bloque D (Cuándo termina)**: Fecha de cierre de la fase en formato `es-CO`, cálculo exacto de días restantes y cuenta regresiva a los hitos de la temporada (Media Maratón Bogotá 2027, Reto Letras 2027, Ironman 70.3 Cartagena 2027).
3. **Nueva ruta dedicada `/tendencia` y navegación** (`DashboardNav.tsx`, `retos/page.tsx`, `apps/web/app/(dashboard)/tendencia/page.tsx` y `apps/web/lib/tendencia.ts`):
   - Retiro de la tarjeta «Tendencia 14d» de `/retos`.
   - Adición del enlace «Tendencia» (`/tendencia`) en la navegación lateral `DashboardNav.tsx`.
   - Página `/tendencia` con:
     - Distribución de zonas en barra horizontal y conteo/porcentaje (`VERDE`, `AMARILLO`, `ROJO`) en los últimos 30 días.
     - Resumen mensual de métricas clave (promedios de HRV, horas y calidad de sueño, cambio de Body Battery, estrés, ACWR y VO₂max).
     - Tabla mensual detallada con fechas en formato `es-CO` y números tabulares (`font-variant-numeric: tabular-nums`).
4. **Gobernanza y arquitectura**:
   - Cumplimiento de Clean Architecture (ADR-002, regla de dependencia): funciones de cálculo y agregación puras en `apps/web/lib/`, presentación en `app/(dashboard)/` y `components/`.
   - Geometría centrada responsive (ADR-003): contenedor con `max-width: 1120px` centrado con padding responsive (28px / 16px).
   - Versionado SemVer `0.5.0` MINOR con reserva serial del grupo `R`.

### No incluye (No-objetivos)

- **Modificación del backend colector en Python** (`garmin_coaching/`, `services/collector/`): El pipeline existente ya recolecta y persiste `readiness_daily`, `daily_snapshots` y `training_load`. No se alteran sus esquemas ni workflows.
- **Nuevas migraciones SQL en Supabase**: Los datos requeridos para los últimos 30 días ya existen en las tablas `readiness_daily` y `training_load`. No se añaden tablas ni columnas a la base de datos cloud.
- **Rediseño visual no relacionado**: No se alteran los colores del tema oscuro, la tipografía global ni las páginas de `/mesociclos`, `/70-3-cartagena` ni `/chat`.
- **Streaming de respuestas o interacción LLM**: La vista `/tendencia` es un Server Component de visualización analítica, no un asistente conversacional.
- **Soporte offline con persistencia en cliente (Service Workers/IndexedDB)**: La aplicación depende de la conectividad y de las consultas a Supabase como el resto del dashboard.

---

## 3. Historias de usuario

- **HU-1 (Recomendaciones accionables)**: Como atleta en entrenamiento, quiero que las alertas de «Qué atender» me indiquen exactamente qué ajuste de descanso, volumen o higiene circadiana debo realizar hoy, para corregir mi déficit fisiológico antes de acumular sobreentrenamiento o riesgo de lesión.
- **HU-2 (Claridad del macrociclo)**: Como atleta preparándome para competencias mayores (mmB, Letras, 70.3), quiero entender en qué fase del macrociclo estoy, cuáles son mis techos seguros de FC y duración, qué directriz rige mi entrenamiento actual y cuántos días faltan para culminar la fase y llegar a mis metas, para mantener la disciplina y el foco estratégico.
- **HU-3 (Visualización de tendencia mensual)**: Como atleta y usuario del dashboard, quiero acceder a una página dedicada de «Tendencia» desde el menú principal, donde pueda evaluar en una sola hoja la proporción de días en verde/amarillo/rojo de los últimos 30 días, el balance de mis métricas fisiológicas y la tabla detallada del mes, para tomar decisiones informadas sobre mi progresión de carga.
- **HU-4 (Consistencia visual y accesibilidad)**: Como usuario que consulta la aplicación en desktop (Safari/Chrome) y móvil, quiero que la nueva vista de tendencia respete el contenedor centrado (ADR-003) sin desbordamientos horizontales, con números alineados en columnas y compatibilidad con lectores de pantalla.

---

## 4. Requisitos EARS y criterios de prueba

Todos los requisitos son de prioridad `must`. Las referencias Pxx identifican criterios de aceptación reproducibles.

| ID | Patrón | Requisito | Prioridad | Criterio de aceptación (Pxx) |
|---|---|---|---|---|
| **REQ-001** | Estado | MIENTRAS el indicador de horas o puntuación de sueño esté por debajo del umbral objetivo (`sleep_h < th.sleep_h` o `sleep_score < th.sleep_score`), el sistema deberá presentar una recomendación accionable de higiene circadiana y mitigación de deuda acumulada. | must | **P01**: Test unitario en `lib/dashboard.ts` valida que ante `sleep_h: 5.8, th: 7.0`, el item generado contiene la observación cuantitativa y la pauta de adelantar descanso nocturno y retirar pantallas/luz azul 1 h antes. |
| **REQ-002** | Estado | MIENTRAS el indicador de HRV nocturno esté deprimido respecto a la línea base (`hrv < th.hrv`), el sistema deberá presentar una recomendación accionable de modulación parasimpática, estímulo vagal y contención de intensidad. | must | **P02**: Test unitario en `lib/dashboard.ts` valida que ante `hrv: 36, th: 48`, el item recomienda priorizar recuperación activa en Z1, respiración diafragmática o descanso para restablecer el tono vagal. |
| **REQ-003** | Estado | MIENTRAS la recarga de Body Battery durante el sueño sea inferior al umbral esperado (`bb_change < th.bb_change`), el sistema deberá presentar una recomendación accionable para mitigar estresores nocturnos y favorecer la regeneración celular. | must | **P03**: Test unitario en `lib/dashboard.ts` valida que ante `bb_change: 15, th: 30`, el item recomienda evitar comidas pesadas/alcohol antes de dormir y optimizar el entorno de descanso (oscuro y fresco). |
| **REQ-004** | Estado | MIENTRAS el ratio de carga aguda:crónica supere el umbral de seguridad (`acwr > 1.3`), el sistema deberá presentar una recomendación de prevención de lesiones orientada a modular el volumen semanal según el modelo de Gabbett. | must | **P04**: Test unitario en `lib/dashboard.ts` valida que ante `acwr: 1.45`, el item recomienda reducir el volumen semanal entre 20% y 30% y evitar picos de intensidad hasta descender al rango seguro (< 1.3). |
| **REQ-005** | Estado | MIENTRAS el estado de entrenamiento reportado sea de sobreesfuerzo (`status_phrase === "OVERREACHING"`), el sistema deberá presentar una recomendación de descarga activa obligatoria ante fatiga no funcional. | must | **P05**: Test unitario en `lib/dashboard.ts` valida que ante sobreesfuerzo, el item prescribe 24-48 h de descarga estricta o rodajes regenerativos Z1 de muy bajo impacto. |
| **REQ-006** | Estado | MIENTRAS todos los indicadores evaluados estén en rango objetivo y la zona de preparación sea `VERDE`, el sistema deberá presentar una recomendación afirmativa de confirmación y ejecución de la sesión planificada. | must | **P06**: Test unitario en `lib/dashboard.ts` valida que sin alertas activas y zona VERDE, el item autoriza la ejecución de la sesión programada según el macrociclo. |
| **REQ-007** | Ubicuo | El sistema deberá estructurar la tarjeta «Macrociclo» en cuatro bloques claramente delimitados y legibles: (a) definición conceptual; (b) momento/fase actual; (c) cómo mejorarla; y (d) cuándo termina. | must | **P07**: Inspección y render de componente en `/retos` comprueba que la tarjeta contiene los 4 bloques con encabezados de bloque accesibles y separación semántica. |
| **REQ-008** | Estado | MIENTRAS se visualice el bloque (a) de definición, el sistema deberá explicar pedagógicamente qué es un macrociclo y su rol en la periodización anual hacia los objetivos de la temporada (mmB 2027, Reto Letras, 70.3 Cartagena). | must | **P08**: Test de componente y dominio verifica texto explicativo sobre la planificación estratégica plurianual por fases para alcanzar el pico de rendimiento en los hitos deportivos. |
| **REQ-009** | Estado | MIENTRAS se visualice el bloque (b) de fase actual, el sistema deberá detallar el código de fase, nombre, foco, deporte(s) prescrito(s), techo de frecuencia cardíaca (`hr_cap` bpm) y duración máxima de sesión (`max_duration_min`). | must | **P09**: Test unitario en `lib/mesocycle.ts` comprueba que para la fecha activa (ej. fase R1) retorna `code: "R1"`, `name: "Base aeróbica"`, `focus: "80/20 Z1-Z2"`, `sport: "run+bike"`, `hr_cap: 135`, `max_duration_min: 75`. |
| **REQ-010** | Estado | MIENTRAS se visualice el bloque (c) de cómo mejorarla, el sistema deberá prescribir una recomendación práctica de ejecución deportiva coherente con la fase activa y modulada según el estado actual de fatiga/carga del atleta. | must | **P10**: Test unitario en `lib/mesocycle.ts` verifica que para R1 prescribe disciplina estricta en Z1-Z2 (< 135 bpm) para estimular biogénesis mitocondrial, y ante fatiga adapta la recomendación hacia recuperación sin desvirtuar el foco. |
| **REQ-011** | Estado | MIENTRAS se visualice el bloque (d) de cuándo termina, el sistema deberá mostrar la fecha de cierre de la fase en formato `es-CO`, los días restantes calculados y la lista de hitos de la temporada con sus respectivas cuentas regresivas. | must | **P11**: Test unitario en `lib/mesocycle.ts` comprueba que con fecha base en R1 formatea el fin como fecha `es-CO` (ej. "31 dic 2026"), calcula días restantes a la fase, y lista los hitos (mmB 2027, Reto Letras 2027, 70.3 Cartagena 2027). |
| **REQ-012** | Evento | CUANDO se acceda a la vista `/retos`, el sistema deberá omitir la tarjeta «Tendencia 14d», preservando sin alteración las secciones de Preparación vs retos, Sesión, Qué atender, Qué va bien y Macrociclo. | must | **P12**: Test de markup de `apps/web/app/(dashboard)/retos/page.tsx` comprueba ausencia de texto "Tendencia 14d" y tabla histórica de 14 filas, y confirma presencia de las demás secciones. |
| **REQ-013** | Ubicuo | El menú lateral de navegación (`DashboardNav`) deberá incluir un elemento permanente hacia la ruta `/tendencia` con etiqueta «Tendencia», marcándolo como activo cuando la ruta actual coincida. | must | **P13**: Test de `DashboardNav.tsx` valida presencia de `{ href: "/tendencia", label: "Tendencia" }` y aplicación de clase `active` y `aria-current="page"` al navegar a `/tendencia`. |
| **REQ-014** | Evento | CUANDO el usuario navegue a `/tendencia`, el sistema deberá renderizar una hoja dedicada dentro del contenedor centrado con ancho máximo de 1120px y padding responsive (ADR-003). | must | **P14**: Test de layout y estilos verifica que `/tendencia` está envuelta en `.app-main > main` cumpliendo max-width 1120px y padding 28px (>800px) / 16px (<=800px). |
| **REQ-015** | Estado | MIENTRAS se visualice `/tendencia`, el sistema deberá desplegar una barra horizontal proporcional de distribución de zonas con el conteo de días y porcentaje en `VERDE`, `AMARILLO` y `ROJO` sobre los últimos 30 días. | must | **P15**: Test unitario de `calculateMonthlyZoneDistribution` en `lib/tendencia.ts` verifica anchos porcentuales exactos, conteos numéricos y soporte de periodos con datos parciales. |
| **REQ-016** | Estado | MIENTRAS se visualice `/tendencia`, el sistema deberá presentar un resumen mensual consolidado con promedios y metas de HRV, horas de sueño, score de sueño, cambio de Body Battery, estrés promedio, ratio ACWR y VO₂max. | must | **P16**: Test unitario de `calculateMonthlySummary` en `lib/tendencia.ts` comprueba promedios aritméticos correctos, omisión limpia de valores nulos y cálculo de deltas respecto a umbrales. |
| **REQ-017** | Estado | MIENTRAS se visualice `/tendencia`, el sistema deberá presentar una tabla con el registro diario de los últimos 30 días, fechas en formato `es-CO`, badges de zona accesibles y cifras con `font-variant-numeric: tabular-nums`. | must | **P17**: Test de componente y estilos comprueba formateo de fechas con `formatDateEsCO`, etiquetas de zona semánticas y clase CSS con números tabulares aplicada a todas las celdas numéricas. |
| **REQ-018** | No deseado | SI la consulta de datos en Supabase para el periodo mensual falla o no contiene registros, ENTONCES el sistema deberá mostrar un estado vacío informativo y amigable sin lanzar excepciones de runtime. | must | **P18**: Test de componente con respuesta de error o arreglo vacío valida renderizado de mensaje amigable de contingencia sin romper el layout ni fallar la página. |
| **REQ-019** | Ubicuo | Toda la lógica de cálculo, reglas de recomendación, proyección de macrociclo y agregación de tendencias mensuales deberá implementarse en funciones puras en `apps/web/lib/`, sin dependencias directas de React, Next.js ni Supabase (Clean Architecture, ADR-002). | must | **P19**: Test de arquitectura por máquina comprueba que los módulos de cálculo puro (`tendencia.ts`, `mesocycle.ts`, `dashboard.ts`) no importan frameworks de presentación ni clientes de red. |
| **REQ-020** | Ubicuo | La entrega desplegable final deberá declarar la versión SemVer `0.5.0` (MINOR) de forma sincronizada en `package.json`, `package-lock.json`, `version.test.mjs`, `README.md` y `CHANGELOG.md` mediante reserva serial del grupo `R`. | must | **P20**: Ejecución de `version.test.mjs` y verificación de consistencia confirman versión 0.5.0 sin degradaciones de versión previa (0.4.0). |

---

## 5. Restricciones

1. **Clean Architecture (ADR-002, regla de dependencia, Art. VII.2)**:
   - La lógica de negocio pura de recomendaciones deportivas, macrociclo y agregación estadística vive exclusivamente en `apps/web/lib/`.
   - Las páginas Server Components en `apps/web/app/(dashboard)/` consumen datos del adaptador de infraestructura y delegan el formateo y cálculo a funciones puras.
   - Ninguna función de cálculo matemático o de dominio importa componentes de React, hooks, o clientes de red.
2. **Geometría centrada responsive (ADR-003)**:
   - La nueva ruta `/tendencia` se inserta bajo `apps/web/app/(dashboard)/layout.tsx` dentro de `<main className="...">`, beneficiándose de la regla de contenedor centrado con `max-width: 1120px; margin: 0 auto;` y paddings `28px` (> 800px) y `16px` (<= 800px).
   - Se preserva el scroll horizontal interno de tablas y gráficas sin generar overflow horizontal en el `viewport`.
3. **Versionado y release (Art. III.4, ADR-009)**:
   - Incremento MINOR a `0.5.0` justificado por la incorporación de una nueva ruta funcional (`/tendencia`) y enriquecimiento del modelo de dominio de macrociclo y recomendaciones.
   - Grupo de archivos `R` reservado serialmente para evitar colisiones de versión.
4. **Persistencia y datos**:
   - Acceso estrictamente en modo lectura sobre tablas existentes (`readiness_daily`, `daily_snapshots`, `training_load`) para el usuario MVP (`MVP_USER_ID`).
   - Cero mutaciones de esquema, cero adiciones de tablas y cero requerimientos de migración SQL cloud en esta especificación.

---

## 6. Riesgos y preguntas abiertas

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **Días faltantes o registros incompletos en el rango de 30 días** | Media | Baja | Las funciones puras de agregación filtran registros nulos o incompletos y calculan promedios sobre los días efectivamente disponibles, indicando el número real de días computados. |
| **Desfase temporal entre tabla de preparación (`readiness_daily`) y carga (`training_load`)** | Baja | Media | Se realiza una consulta cruzada indexada por fecha (`loadByDate = new Map<string, LoadRow>()`) tal como opera actualmente `fetchDashboard()`, tolerando ausencia de fila de carga con valores `null` controlados. |
| **Saturación de columnas en tabla mensual en pantallas móviles estrechas (< 400px)** | Media | Media | La tabla mensual implementa un contenedor con scroll horizontal suave (`overflow-x: auto`), clase `.history-table` y columnas prioritarias claramente visibles. |
| **Inconsistencia entre catálogo de fases de Python y TypeScript** | Baja | Media | Se sincroniza rigurosamente el catálogo `PHASES` en `apps/web/lib/mesocycle.ts` con `garmin_coaching/macrocycle.py` (códigos R0 a R7, techos FC, deportes y fechas). |

- **Preguntas abiertas**: Ninguna identificada que bloquee la especificación; los requisitos del humano en `handoff.md` son cerrados, precisos y ejecutables.

---

## 7. Criterios de éxito de la spec

1. Los 20 requisitos EARS (`REQ-001` a `REQ-020`) cuentan con pruebas automatizadas (`P01` a `P20`) en verde.
2. La suite de pruebas existente (58 tests) continúa pasando al 100% sin regresiones.
3. El comando `npm run build` en `apps/web` compila exitosamente con código de salida 0.
4. El contenedor centrado (ADR-003) se respeta en `/tendencia` en anchos móvil (375px) y escritorio (1120px+).
5. Las recomendaciones de «Qué atender» están rigurosamente fundamentadas en modulación parasimpática, cronobiología del sueño, recarga autonómica y ratio ACWR de Gabbett.

---

## 8. Seguridad y operación

- **Secretos y credenciales**: No se introducen nuevos secretos. El acceso a Supabase continúa utilizando el cliente anónimo público del frontend o sesión autenticada establecida en SPEC-002. Cero tokens Garmin o credenciales sensibles en logs o código.
- **Permisos y superficie expuesta**: La ruta `/tendencia` es una página de lectura protegida bajo el mismo régimen del dashboard; las consultas a `readiness_daily` y `training_load` leen datos consolidados.
- **Datos y retención**: Solo se leen los últimos 30 días de métricas fisiológicas para el cálculo de tendencias. No se guardan ni modifican registros en la base de datos.
- **Observabilidad mínima en operación**:
  - Monitorear respuestas HTTP de `/tendencia` y `/retos`: tasa de error 5xx < 0.1%.
  - Tiempo de renderizado en servidor < 400 ms en percentil 95.
  - Verificar que el botón "Actualizar" en el `DashboardNav` refresque transparentemente los datos tanto en `/retos` como en `/tendencia`.
- **Criterio de reapertura de la spec**: Si el usuario requiere filtros por rango de fechas personalizado (ej. 60 o 90 días), exportación a CSV/PDF, o ajuste de la fórmula de periodización del macrociclo hacia nuevas competencias, se creará una nueva especificación de producto (SPEC-004 o enmienda mayor).
