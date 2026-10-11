# Diagnóstico para adoptar SDD en Fitness Coach

Versión 1.0 · 2 de octubre de 2026 · Estado: diagnóstico y propuesta, adopción pendiente.

## Dictamen

El proyecto puede adoptar Spec-Driven Development de forma incremental. Tiene componentes separables, lógica determinista y una base de pruebas aprovechable. Sin embargo, todavía no existe una cadena verificable entre necesidad, especificación aprobada, decisión técnica, tarea, implementación y aceptación.

La prioridad es convertir las reglas de producto en contratos comprobables. Crear carpetas de especificaciones sin corregir la precedencia de reglas, la integridad de los datos y los límites de acceso dejaría intactos los problemas principales.

Recomiendo mantener inicialmente el repositorio actual, distinguir Fitness Coach de la biblioteca Garmin que incorpora y añadir una capa de especificaciones vivas por capacidad. OpenSpec es mi opción preferida para organizar esa capa; IES conservaría el gobierno de tareas y autorizaciones. Esta elección es una propuesta de arquitectura de trabajo, no una instalación ni una política aprobada.

## Alcance y evidencia

- Checkout examinado: `/Users/alarcondiegof/ies-projects/python-garminconnect`.
- Rama: `cursor/shell-chat-hoy-43bc`.
- Commit: `c2068d481832e38fbb66593d355d96a609664deb`.
- Estado inicial limpio; 161 archivos versionados. La rama está ocho commits por delante de `master` local, sin commits exclusivos de ese `master`. No se hizo fetch; esto no acredita el estado remoto actual.
- Inspección de estructura, documentación, IES, Python, Next.js, SQL, MCP, scripts de publicación, workflows n8n, configuración de despliegue y CI.
- Comprobaciones locales con datos sintéticos y conexión de sockets bloqueada en las sondas Python. No se leyeron archivos de credenciales ni datos biométricos personales.
- No se consultaron cuentas Garmin, Supabase, OpenAI ni servicios desplegados; tampoco se enviaron mensajes, publicaron entrenamientos, dispararon workflows o modificaron servicios.
- La única entrega persistida por esta revisión es documental: este informe y el archivo de evidencia asociado. No se implantó SDD ni se corrigió código funcional.

Los hallazgos se distinguen como **reproducidos**, **observados en código** o **NO VERIFICADO en producción**. La [evidencia sintética](../../deliverables/sdd-diagnostic-2026-10-02.json) conserva entradas o resultados resumidos sin información de una cuenta real.

## Qué proyecto existe hoy

| Capa | Evidencia local | Papel real |
|---|---|---|
| Biblioteca Garmin | `garminconnect/`, `README.md`, `pyproject.toml` | Cliente reutilizable, autenticación, lecturas y escrituras Garmin. Metadatos y README siguen orientados a la biblioteca upstream. |
| MCP | `garmin_mcp/server.py` | Herramientas de consulta de cuenta, además de autenticación y gestión local de tokens. Es implementación del repositorio; no se acreditó carácter oficial de Garmin. |
| Motor de coaching | `garmin_coaching/` | Readiness, reglas restrictivas, sesión diaria, macrociclo, mesociclos y carga ejecutada. |
| Ingesta | `services/collector/`, `.github/workflows/coaching-daily-collect.yml` | API FastAPI y ejecución programada/manual en Actions; ambas pueden escribir Supabase. |
| Datos | `supabase/schema.sql`, `supabase/migrations/` | Snapshots, readiness, carga, sesiones, hitos y mensajes; identidad fija de MVP. |
| Producto web | `apps/web/` | Dashboard, retos, mesociclos, chat con contexto y botón que dispara recolección en Actions. |
| Orquestación y publicación | `docs/n8n/`, `scripts/publish_*` | Plantillas de mensajería y scripts con efectos sobre servicios externos. Su despliegue no se verificó. |
| Gobierno | `.ies/`, `memory/`, `HANDOFF.md` | IES inicializado, memoria canónica mayormente vacía y handoff operativo parcialmente desactualizado. |

La arquitectura implementada ofrece dos caminos de ingesta: Actions y FastAPI. Los documentos todavía mezclan Actions, Railway/Fly.io y n8n como arquitectura recomendada o desplegada. El README web se presenta como solo lectura, aunque hay endpoints que consumen OpenAI y disparan Actions. `HANDOFF.md` dice que el chat queda solo en Inicio, pero ahora también existe `/chat`.

La arquitectura objetivo debe decidir cuál es el camino operativo principal y cuáles son alternativas. La existencia de un archivo de configuración no prueba que el servicio esté activo.

## Preparación para SDD

| Dimensión | Estado observado | Brecha |
|---|---|---|
| Identidad y alcance del producto | Parcial | Biblioteca y producto personal conviven sin un contrato explícito de compatibilidad. |
| Especificaciones de comportamiento | Incipiente | Hay reglas en documentación y código, pero no catálogo de requisitos con escenarios y aceptación. |
| Arquitectura y decisiones | Parcial | Límites físicos razonables; decisiones dispersas y contradicciones documentales. |
| Trazabilidad IES | Ausente en el ledger inspeccionado | `memory/mid/tasks.md` no tiene tareas; producto, arquitectura, decisiones, riesgos y estado conservan placeholders. |
| Contratos de datos e integración | Débil | Diccionarios y JSON sin versión de contrato; fechas, calidad, procedencia y fallos parciales ambiguos. |
| Pruebas del producto | Parcial | Las reglas simples tienen pruebas; faltan cruces de reglas y aceptación entre capas. |
| CI del sistema completo | Parcial | CI Python existente; sin job web, SQL/RLS ni trazabilidad de requisitos. |
| Operación y recuperación | Parcial | Hay mecanismos de despliegue y autenticación, pero falta evidencia operativa asociada al mismo commit y contrato. |

Estas categorías no son porcentajes de avance. No hay un alcance SDD aprobado que permita calcularlos.

## Hallazgos que deben convertirse en contratos

### Precedencia de restricciones de entrenamiento

**Reproducido. Prioridad alta.** En `garmin_coaching/guards.py:20`, ROJO fuerza descanso, pero el bloque de ACWR llama a `_cut_volume(session, ...)` con la sesión original. Con ROJO, ACWR 1,4 y sesión de 60 minutos, el resultado es `action=train`, 45 minutos y una bandera `readiness_rojo` que ya no describe el resultado.

AMARILLO se recorta en `session_planner.py:58` y nuevamente en `guards.py:36`: para el 6 de octubre de 2026, 55 minutos pasan a 44 y luego a 35. Además, `_cut_volume` puede subir una duración inferior a 20 minutos hasta su mínimo de 20.

**Contrato necesario:** orden de precedencia, composición de restricciones, aplicación única y prohibición de que una restricción reactive o aumente una sesión restringida. Los umbrales existentes son reglas del producto que requieren dueño y versión; este diagnóstico no valida su fundamento clínico.

### Datos ausentes, antiguos o parcialmente fallidos

**Reproducido y observado. Prioridad alta.** Si el collector no obtiene readiness, `plan_session(None, ...)` y `apply_guards({}, {}, ...)` pueden devolver entrenamiento sin restricciones. La sonda del 6 de octubre devolvió 55 minutos. Si las llamadas sí responden pero con métricas vacías, `classify` puede clasificar ROJO. Son estados distintos sin un contrato común de calidad.

El collector permite recurrir al día anterior. En la sonda, métricas del 30 de septiembre se guardaron como `readiness_date=2026-10-01`, aunque el JSON interno conservó la fecha original. `collect_recent_metrics` usa `date.today()` incluso cuando se solicita recalcular una fecha histórica.

Los upserts no envían `updated_at`; el SQL declara `default now()` sin un trigger de actualización. El chat decide antigüedad a partir de esos timestamps y combina las últimas filas de varias tablas sin exigir fecha o lote común. `loadCondition` tampoco inspecciona los campos `error` devueltos por Supabase.

Fuentes: `collector.py:119–166`, `supabase_client.py:21–68`, `schema.sql:42–86`, `apps/web/lib/condition.ts:56–95`.

**Contrato necesario:** separar fecha observada, fecha solicitada, hora de recolección, zona horaria, lote y estado de calidad. Una actualización reciente no rejuvenece la observación. La decisión para información ausente debe aprobarse expresamente y reflejarse en UI y chat.

### Recolección que altera decisiones humanas e historial

**Reproducido en la llamada al adaptador y observado en código. Prioridad alta.** Cada upsert de `session_log` envía `executed=None` y `confirmed=False`, también cuando existe una fila para ese día. La sonda capturó estos valores sin acceder a una base real. No se comprobó si existen sesiones confirmadas afectadas en producción.

En carga semanal, una excepción de Garmin se transforma en una lista vacía. La sonda emitió 24 semanas con ejecución cero. Además, `weekly_sync` consulta como máximo 120 días de actividades, pero emite semanas desde septiembre de 2026: fuera de esa ventana puede sobrescribir ejecución antigua con ceros. Las escrituras se ejecutan tabla por tabla, sin transacción conjunta visible.

Fuentes: `supabase_client.py:70–104`, `activity_load.py:92–97`, `weekly_sync.py:23–52`.

**Contrato necesario:** la ingesta actualiza observaciones y propuestas sin borrar decisiones ni ejecución; fallo de origen es distinto de cero actividad; el reintento preserva datos y tiene resultado determinista. Definir cómo se publica un lote completo y cómo se recupera uno parcial.

### Acceso a datos y operaciones externas

**Observado en código. Prioridad alta; exposición efectiva NO VERIFICADA.** Las ocho políticas denominadas `service_role_all` omiten `TO service_role` y usan `FOR ALL USING (true) WITH CHECK (true)`. El nombre no restringe el rol: PostgreSQL aplica por defecto una política sin `TO` a `PUBLIC`. El acceso efectivo depende también de privilegios y configuración desplegada. Véase la [semántica oficial de CREATE POLICY](https://www.postgresql.org/docs/current/sql-createpolicy.html).

No se encontró autenticación de la persona solicitante ni control de frecuencia en `/api/chat`, `/api/refresh` o `/collect`. El token servidor autentica frente al proveedor, pero no identifica a quien invoca el endpoint del producto. No se verificó protección externa de Vercel o del worker.

Fuentes: `supabase/schema.sql:147–164`, migración semanal, `apps/web/app/api/chat/route.ts:35`, `apps/web/app/api/refresh/route.ts:39`, `services/collector/main.py:50`.

**Contrato necesario:** matriz de actor, recurso y operación; rechazo de acceso anónimo a datos personales y acciones con costo; identidad del atleta; privilegios mínimos; pruebas negativas de RLS en entorno desechable. Si el código está desplegado sin controles adicionales, la contención de acceso precede a ampliar funciones.

### Calendario y volúmenes inconsistentes

**Reproducido. Prioridad media.** Para la semana del 4 de octubre de 2027, el motor declara 132 minutos de natación y suma 264 en el detalle diario: divide entre tres y asigna esa cantidad a seis días. Para el hueco del 26 de julio de 2027, `active_phase` devuelve R7, aunque esa fase comienza en octubre.

Hay calendarios y reglas replicadas en Python, TypeScript y SQL. La UI puede recalcular metadatos de planificación al mostrar una fila persistida. No hay pruebas de paridad entre lenguajes.

Fuentes: `mesocycle.py:74–115`, `macrocycle.py:36–64`, `apps/web/lib/mesocycle.ts:1–109`, `supabase/seed.sql`.

**Contrato necesario:** suma de días igual al total semanal con tolerancia de redondeo definida; política explícita para huecos y límites de calendario; una configuración canónica versionada o fixtures de paridad compartidos. Las fechas del repositorio son configuración del producto, no fechas oficiales verificadas de eventos.

### Contratos de chat y actualización incompletos

**Observado en código. Prioridad media, además del acceso anterior.** La entrada de chat se convierte mediante cast de TypeScript, sin validar la forma en runtime: un `messages` que no sea array puede fallar antes del manejo de errores. Los límites de caracteres no sustituyen un límite de cuerpo o de uso.

`pickModel` admite también nombres que coincidan con un patrón aunque no estén en el catálogo; por tanto, el catálogo no funciona como una lista estricta permitida. La llamada no establece plazo de espera ni límite explícito de salida. El prompt pide prudencia, pero no existe evaluación de respuestas ni validación de reglas después de generar texto.

Refresh busca un workflow reciente por tiempo, con margen de un minuto, sin correlación exclusiva entre solicitud y run. La UI puede atribuir un run cercano a su actualización. El valor por defecto del dispatch es `master`, diferente de la rama revisada.

Fuentes: `app/api/chat/route.ts:44–79`, `lib/openaiModels.ts:79–85`, `app/api/refresh/route.ts:7–11,73–105`.

**Contrato necesario:** esquema de entrada, errores, modelos permitidos y presupuesto de uso; contexto coherente y evaluación del chat; identificador de solicitud/lote y estados observables de refresh. Terminar un job no basta para acreditar que el dato esperado quedó visible.

### Confirmación humana y operación todavía parciales

**Observado en artefactos.** Los JSON n8n piden respuestas, pero no contienen un flujo receptor que aplique `OK`, `Descanso` o `Recortar`. En `alerts-weekly.json`, el resumen semanal no está conectado a un nodo de envío y el nodo de salud de Garmin está desconectado. `/health` solo informa configuración de Supabase, no vigencia de sesión Garmin.

`/publish-session` responde `not_implemented`; los scripts de publicación sí llaman a Garmin y `--dry-run` es optativo. No se ejecutaron. El handoff y los README no establecen con suficiente precisión qué funcionalidades están implementadas, probadas o desplegadas.

**Contrato necesario:** estados propuesta, confirmada, rechazada, publicada y fallida; identidad del aprobador; idempotencia de mensajes y publicación; evidencia operativa y procedimiento de recuperación. No declarar completado un circuito humano solo porque el mensaje solicita una respuesta.

## Verificación realizada y límites

| Comprobación | Resultado | Alcance |
|---|---|---|
| Inventario AST de pruebas | 368 funciones `test_*` en 17 archivos | Conteo estático; parametrización y recolección pytest pueden producir cantidades distintas. |
| Pruebas de coaching existentes | 11 de 11 funciones ejecutadas sin fallos | Invocación directa con `runpy`, no ejecución de la suite pytest. |
| Sondas de límites y composición | Reprodujeron los resultados detallados arriba | Datos sintéticos; fábrica de Supabase sustituida; sockets bloqueados. |
| TypeScript con configuración del repo | Falló por referencias a rutas antiguas en `.next/types` | Caché generada anterior al cambio de grupos de rutas; no prueba por sí sola un defecto del código fuente. |
| TypeScript de fuentes sin caché `.next` | Pasó con configuración temporal externa | `tsc --noEmit`; no equivale a build Next ni a prueba de navegador. |
| Suite Python completa, coverage y lint | NO EJECUTADOS | La `.venv` no contiene pytest, coverage, ruff ni vcr. No se instalaron dependencias. |
| Build limpio, pruebas E2E, SQL aplicado y operación cloud | NO VERIFICADOS | Requieren otra validación; no se tomaron afirmaciones del handoff como resultados actuales. |

El entorno Python local es 3.14.4; CI declara 3.12 y 3.13. `pdm.lock` está ignorado y no versionado; la web sí versiona `package-lock.json`. Se necesita una línea base reproducible por componente antes de acreditar aceptación del sistema completo.

CI ejecuta pytest sobre `tests/`, pero cobertura, mypy y Bandit están centrados en `garminconnect` y algunos scripts heredados. `coverage` solo declara `garminconnect` como fuente; no mide la cobertura del coaching. No hay umbral de cobertura en la configuración revisada. La web no define script de pruebas ni tiene job dedicado en CI.

## Diseño recomendado de la adopción

### Papel de IES y de las especificaciones

IES conserva tareas, roles, permisos y evidencia de cierre. La especificación define el comportamiento aceptado. El diseño técnico explica cómo cumplirlo. Las pruebas demuestran escenarios concretos. El código existente constituye evidencia del estado actual, no aprobación automática de sus defectos.

Para evitar dos fuentes de estado, una tarea IES debe referenciar el cambio SDD correspondiente. El checklist técnico de ese cambio puede descomponer trabajo, pero no reemplaza ni duplica el estado oficial del ledger. Los IDs IES se obtienen mediante el CLI; no se inventan ni se edita el ledger manualmente.

Las especificaciones duraderas describen capacidades; los paquetes de cambio describen sus diferencias propuestas. Al aceptar un cambio se actualiza la especificación duradera y se conserva su historial. Un defecto conocido se registra como discrepancia, no como requisito que deba preservarse.

### Herramienta

| Opción | Ajuste al proyecto | Recomendación |
|---|---|---|
| OpenSpec | Organiza capacidades y paquetes de cambio con propuesta, especificación, diseño y tareas. | Preferida para este sistema existente; adaptar el flujo a la autoridad de IES. |
| GitHub Spec Kit | Proporciona constitución y flujo explícito de especificación, plan y tareas; también admite adopción incremental. | Alternativa razonable si se decide estandarizar ese flujo entre repositorios. |
| Markdown y validadores propios | Permite un piloto sin CLI nuevo. | Útil para probar contratos; evitar construir otro framework mantenido a mano. |

La documentación de [OpenSpec](https://github.com/Fission-AI/OpenSpec) describe paquetes de cambio y actualización de las especificaciones al archivarlos. La [guía de Spec Kit para proyectos existentes](https://github.com/github/spec-kit/blob/main/docs/guides/existing-projects.md) recomienda comenzar por un cambio acotado y no reconstruir todo el sistema antes de adoptar el flujo. La preferencia por OpenSpec aquí es una inferencia propia por su ajuste a las capacidades existentes, no una superioridad universal.

No conviene instalar ambas herramientas. Antes de inicializar la elegida hay que fijar versión, inspeccionar sus archivos generados y comprobar que sus instrucciones no contradicen IES o las convenciones del repositorio.

### Capacidades propuestas

| Capacidad | Qué debe especificar | Verificación principal |
|---|---|---|
| Acceso y privacidad | Actores, aislamiento, operaciones, retención y eliminación | Matriz RLS y pruebas negativas HTTP |
| Observaciones Garmin | Origen, fecha, calidad, fallback, zona horaria y errores | Contrato de payload y fixtures sintéticos |
| Readiness y restricciones | Precedencia, composición, faltantes y versión de reglas | Tablas de decisión y pruebas de invariantes |
| Planificación | Calendario, fases, volumen diario/semanal y autoridad de datos | Límites temporales y paridad Python/TypeScript |
| Persistencia | Idempotencia, integridad, conservación de decisiones y lotes | Pruebas de reintentos y fallos intermedios |
| Actualización y dashboard | Estados, frescura, dato esperado y correlación del job | Aceptación de API y E2E con proveedores simulados |
| Chat de coaching | Contexto, límites, incertidumbre, errores y uso permitido | Evaluaciones de escenarios y validadores deterministas |
| Confirmación y publicación | Máquina de estados, aprobación y efectos externos | Simulación de mensajes/publicación y no duplicación |

Una estructura posible, todavía no creada, sería `openspec/specs/<capacidad>/spec.md` y `openspec/changes/<cambio>/` para propuesta, deltas, diseño, tareas y evidencia. Los contratos de intercambio deben acompañarse de JSON Schema/OpenAPI o modelos equivalentes comprobables. La forma exacta depende de la versión de la herramienta elegida.

Cada requisito debe tener ID estable, responsable, estado, escenarios y vínculo con pruebas. Un PR que cambie comportamiento debe declarar los requisitos afectados y aportar evidencia sobre ese mismo commit. Los cambios mecánicos sin efecto funcional pueden usar una justificación breve en lugar de un paquete extenso.

## Ruta de conversión y condiciones de salida

| Paso | Trabajo propuesto | Condición para avanzar |
|---|---|---|
| 1. Línea base | Resolver identidad Fitness Coach/biblioteca, camino de ingesta, rama de referencia y arquitectura efectiva. Registrar vacíos de IES con evidencia. | Producto, límites, compatibilidad y diferencia entre local/remoto/desplegado explícitos. |
| 2. Base SDD mínima | Elegir una herramienta; reglas de autoridad; plantilla de requisito y cambio; referencias al ledger IES. | Se puede seguir una cadena requisito → tarea → código → prueba sin estados duplicados. |
| 3. Contratos prioritarios | Acceso/privacidad, precedencia de restricciones, calidad temporal e ingesta que preserva estado humano. | Escenarios aceptados y discrepancias actuales identificadas. Acceso expuesto, si se confirma, se contiene primero. |
| 4. Piloto funcional | Implementar únicamente la precedencia de restricciones y el recorte único. | Los escenarios del piloto fallan en la versión actual y pasan tras la corrección; regresión pertinente y revisión del diff. |
| 5. Verificación integral | CI coaching, web y SQL; fixtures compartidos; contrato de payload; evidencia por cambio. | Checkout limpio reproducible y aceptación automatizada sin cuentas personales. |
| 6. Adopción gradual | Migrar ingesta, calendario, chat y operaciones a medida que se intervienen. | Cada cambio funcional mantiene su especificación; operaciones externas tienen su validación y autorización propias. |

La implantación no exige separar inmediatamente repositorios ni reescribir la biblioteca. Primero conviene delimitarla como dependencia interna con compatibilidad protegida. Una extracción posterior requiere un motivo concreto: publicación independiente, conflicto con upstream o ciclos de entrega incompatibles.

## Primer piloto propuesto

**Nombre:** precedencia de restricciones y recorte único de sesión.

**Problema:** reglas individuales aparentemente correctas se contradicen al combinarse. El piloto valida SDD con una corrección local, determinista y de alcance pequeño.

**Alcance:** contrato de decisión y cambios mínimos en `garmin_coaching/guards.py`, `session_planner.py` y sus pruebas. Tarea IES real por crear mediante CLI. Sin modificación de umbrales, base de datos, chat, despliegue o publicación Garmin.

**Criterios propuestos para aprobación:**

1. ROJO produce descanso para cualquier ACWR, incluidos valores ausentes, 1,3, 1,4, 1,5 y superiores a 1,5.
2. Una restricción posterior nunca convierte descanso en entrenamiento ni aumenta la duración.
3. AMARILLO aplica exactamente una vez el recorte aprobado; debe definirse el redondeo.
4. ACWR elevado y OVERREACHING respetan la precedencia aceptada; probar combinaciones, no solo cada regla aislada.
5. Una sesión que ya era descanso permanece en cero minutos.
6. Las banderas explican el resultado final y no contradicen la acción.
7. La entrada no se modifica accidentalmente; la transformación determinista conserva metadatos ajenos al ajuste.
8. Las once pruebas actuales pertinentes siguen pasando, además de los nuevos casos aceptados.

**Decisiones fuera del piloto:** qué hacer con datos ausentes; persistencia real del descanso durante 48 horas; fundamento y revisión de umbrales; conflictos con el plan semanal. Deben tener contratos propios antes de ampliar el comportamiento. La frase «descanso 48h» hoy es texto; no hay estado temporal que lo imponga durante ese período.

## Cómo saber si la conversión funciona

No basta con contar documentos. Para el alcance migrado deben poder comprobarse estas condiciones:

- Todos los requisitos obligatorios del cambio tienen al menos un escenario y una evidencia de aceptación.
- Cada modificación funcional declara su contrato o una excepción revisada.
- Las decisiones pendientes y desviaciones conocidas permanecen visibles; los fallos no se renombran como comportamiento aceptado.
- Un checkout limpio reproduce pruebas y construcción con dependencias y runtimes definidos.
- Los fixtures son sintéticos y no requieren sesiones Garmin, claves ni biometría personal.
- Las capacidades de acceso, integridad de datos y restricciones no tienen fallos de alta prioridad abiertos al liberar su cambio.
- La evidencia identifica commit, versión de contrato y entorno. Aprobar código y verificar despliegue son estados distintos.

## Decisiones de producto pendientes

Estas decisiones no impiden el diagnóstico, pero sí afectan las especificaciones finales:

1. Confirmar si Fitness Coach seguirá siendo exclusivamente personal o si se proyecta más de un atleta. La privacidad es necesaria en ambos casos.
2. Confirmar si el producto solo propone sesiones o también podrá publicarlas tras aprobación explícita.
3. Definir quién aprueba reglas de entrenamiento, umbrales, límites y política de datos insuficientes.
4. Elegir Actions como ingesta principal o sostener además un worker permanente, con responsabilidades explícitas.
5. Determinar la relación futura con upstream y la rama sobre la que se adoptará SDD.

## Historial

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-10-02 | Primera revisión local, sondas sintéticas, contraste documental y propuesta de adopción incremental. |
