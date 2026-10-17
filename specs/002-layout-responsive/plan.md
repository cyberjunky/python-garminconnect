---
schema_version: 1
plan_id: PLAN-002
spec: SPEC-002
slug: layout-responsive
project_id: python-garminconnect
version: 1
status: approved
autonomy: hitl
owner_task: null
last_updated: '2026-10-17T12:17:02Z'
source: ies spec new
approved_at: '2026-10-17T12:17:02Z'
decision_ref: memory/mid/decisions.md#dec-009-aprobacion-humana-g0-de-spec-002-y-plan-002
---

# PLAN-002: Centrado responsive, historial privado sincronizado y modelo exclusivo

Origen: propuesta T-0022, materializada por T-0024 tras aprobacion humana G0; DEC-009.
Autonomia: `hitl`; cada gate de ejecucion conserva aprobacion propia.

## 1. Alternativas y recomendación
| Área | Alternativas | Complejidad, riesgo, costo y reversibilidad |
|---|---|---|
| Layout | Centrar 880 / centrar 1120 / ancho ilimitado / no cambiar | 880 es menor cambio pero conserva área útil reducida; **1120 recomendado**, costo bajo y reversible CSS; ilimitado perjudica lectura y amplía regresión; no cambiar deja fallo. |
| Historial | Local sin límite / Supabase Auth+Postgres / nuevo backend y proveedor | Local es barato pero no satisface dispositivos y falla ante borrado local; **Supabase existente recomendado**, complejidad media, exige auth/RLS y costo según cuenta; otro backend duplica operación sin valor demostrado. |
| Identidad | OTP por invitación / contraseña nueva / UUID compartido | **OTP recomendado**, evita otra gestión de contraseñas, depende de entrega email y redirects verificados; contraseña agrega gestión; UUID compartido incumple aislamiento. |
| Importación | Automática / opt-in conservadora | Automática reduce pasos pero puede atribuir historial a cuenta equivocada; **opt-in**, un paso explícito y copia idempotente sin borrar, reversible sin pérdida local. |
| LLM | Mantener Chat Completions / migrar Responses | **Conservar endpoint** actual sin tools, menos regresión y costo de desarrollo; Responses es válido pero no necesario. Si se requieren tools después, nuevo gate. |
| Presentación | Estado en componentes / ViewModel de chat | **ViewModel** dedicado por crecimiento de sincronización/auth; costo pequeño frente a duplicación y carreras. No migrar dashboard estático. |
| Orden | Publicar visual primero / paquete integral | **Paquete integral 0.4.0** evita versiones y despliegues intermedios. Si urge publicar CSS antes, requiere gate de release separado, sin fingir historial corregido. |

Fuentes oficiales aportadas y consultadas por coordinator: [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) y [guía de migración](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#migration-quickstart). Fundamentan ID y esfuerzo, no acceso de esta cuenta. Chat Completions con high se usa sin function calling; no configurar tools ni `none` como atajo. Esta entrega no efectuó consulta remota ni inferencia.

## 2. Componentes, capas y contrato técnico

| Capa | Componentes propuestos | Dependencia |
|---|---|---|
| Dominio | `lib/chat/`: tipos Conversation/Message/Operation, validación, revisión y estado de guardado | TypeScript puro; ninguna importación de infraestructura/UI |
| Aplicación | `lib/chat/application/`: crear/listar/enviar/importar mediante puertos ConversationRepository, Identity, HealthContext, CoachProvider | Dominio e interfaces |
| Infraestructura | `lib/infra/chat/`, `lib/infra/auth/`, `lib/infra/health/`, `lib/infra/supabase.ts`, `lib/infra/openaiModels.ts` | Supabase, fetch; implementa puertos |
| Presentación | API routes como composition root, páginas login, `components/Coach*`, `hooks/useCoachConversation.ts` | Casos de uso/ViewModel; sin reglas de negocio incrustadas |
| Persistencia | Migración aditiva de conversaciones/mensajes/operaciones/importaciones/vínculo de salud | RLS y constraints; no altera datos Garmin existentes |

`lib/supabase.ts` y `lib/openaiModels.ts` tocados se trasladan a `lib/infra/` según ADR-002; no dejar un shim que mantenga dependencias inversas. `condition.ts` conserva transformación/prompt puros; consultas pasan a infraestructura. `dashboard.ts`, `mesocycle.ts` y páginas que importen el cliente se ajustan solo en el corte necesario: IO a adaptador, cálculos sin red, imports consumidores actualizados. No refactor general de métricas. Si el grafo exige más rutas que la allowlist, se detiene para aprobación acotada.

Tablas propuestas: `coach_conversations(id,owner_id,title,revision,created_at,updated_at)`; `coach_messages(id,conversation_id,owner_id,sequence,role,content,created_at)`; `coach_operations(owner_id,operation_id,conversation_id,status,result_message_id,lease_until)`; `coach_imports(owner_id,source_id,source_digest,conversation_id,status)`; `coach_profile_links(auth_user_id,profile_id)` administrada fuera del cliente. Claves únicas de propietario/operación y source/digest; FK compuesta message→conversation evita asignar mensaje a propietario distinto. RLS `auth.uid()=owner_id` tanto USING como WITH CHECK y grants mínimos; anon sin acceso. Los roles cliente no pueden escribir directamente assistant ni completar operaciones: una credencial backend de privilegio mínimo, distinta de anon/JWT de usuario, solo puede ejecutar la función privada de finalización; esta exige operación previamente reclamada y revalida propietario. No exponer esa credencial al navegador ni usar service-role para lecturas de historial. La importación admite roles legacy únicamente como copia marcada, no como respuesta nueva del proveedor. `coach_profile_links` no admite escritura por usuario normal. P05 incluye intentos directos de completar operaciones y de falsificar respuestas.

API: GET/POST `/api/conversations`; GET `/api/conversations/:id/messages`; POST `/api/conversations/import`; POST `/api/chat` con conversation_id, texto, operation_id y revisión esperada. IDs ajenos no revelan contenido. Respuestas tipadas: 401 sesión, 403 vínculo, 404 conversación, 409 conflicto/en curso, 413 límite, 429 cuota, 502 proveedor, 503 persistencia. Confirmar «Guardado» únicamente después de commit DB. Cache `no-store` para historial y respuestas privadas.

Flujo de envío: autenticar→verificar dueño/vínculo→guardar mensaje usuario y claim de operación en transacción→leer contexto propio→llamar único modelo→guardar assistant y completar operación→responder. Una operación concurrente no hace segunda inferencia mientras lease esté vigente. Tras timeout ambiguo se permite reintento explícito, manteniendo operación/mensaje únicos; **no se promete exactly-once en proveedor externo ni costo exactamente único**. Si cae después de recibir respuesta y antes del commit, el usuario permanece guardado y se informa respuesta no guardada; se puede regenerar explícitamente con mismo modelo. No borrar mensajes confirmados ni confiar en reenvío de array completo.

Vínculo salud: humano registra una relación auth-user→perfil MVP tras identificar propietario; una cuenta no vinculada no accede al coach personal. El adaptador solo consulta readiness_daily, training_load y daily_snapshots del perfil resuelto en servidor. Revisar permisos efectivos de esas tres tablas en gate cloud; si el patrón local abierto está presente y no es resoluble dentro del vínculo acotado, bloquear habilitación del chat y solicitar alcance, sin reutilizar políticas abiertas.

## 3. Migración conservadora y pruebas aisladas

Dos migraciones distintas: **schema aditivo** humano y **copia legacy opt-in** por cada usuario. El primer login solo ofrece «Importar historial de este navegador» con cuenta destino, conteo y aviso de copia local conservada. No llama a `loadChats()` legado para importar porque corta a cuatro: lee el valor bruto, valida estructura y conserva todas las entradas supervivientes. No recupera lo ya sobrescrito.

Snapshot estable por source ID y digest completo del contenido; no usar solo título/fecha ni confiar en ID legacy global. Transacción por conversación y marcador de importación; reintentar mismo snapshot es no-op. Mismo ID con digest distinto crea copia diferenciada, no sobrescribe conversación remota; informar al usuario. Cambio de cuenta invalida confirmación pendiente. JSON inválido, lote grande o cuota dejan fuente intacta y resultado por entrada. No limpiar localStorage legacy al terminar.

Tests usan instancia Postgres/Supabase **aislada con Auth y RLS reales** y dos usuarios ficticios; variables de test separadas, guardas que rechazan URL/proyecto productivo, credenciales solo efímeras fuera del repo. Autorizar su creación y escrituras sintéticas en gate de implementación, no ahora. Mock de LLM para todas las suites; mock de repositorio sirve para unidades pero no demuestra persistencia. Evitar proxy genérico: fixtures mínimas en DB de test y responses del proveedor controladas. Si no existe entorno aislado disponible, detener pruebas de integración hasta gate de aprovisionamiento; no usar producción de sustituto.

## 4. Descomposicion en tasks, equipo y allowlists

Tamaño **L ajustado** por web+auth+datos+API LLM: planner actual, tres instancias implementer (una por task), dos viewers por área (visual y datos/modelo), coordinator principal. Ejecución serial recomendada por metadatos de versión e interfaces compartidos; multiagentes significa separación de responsabilidades, no paralelismo obligatorio. Ningún especialista ni modelo adicional se presume. Todos perfil `riguroso`, parent_task T-0022. Alias no son IDs reales: coordinator asigna T-XXXX al aprobar cada gate ejecutivo. C-GOV corresponde a T-0023, configuracion aplicada y aceptada.

Prefijo común R de implementers: `apps/web/package.json`, `apps/web/package-lock.json`, `apps/web/lib/version.test.mjs`, `apps/web/README.md`, `apps/web/CHANGELOG.md`, `deliverables/T-<propia>.md`, `deliverables/evidence/T-<propia>/`. Solo una task posee R a la vez.

| Alias / destino | Input y output esperado | REQ y acceptance | Allowlist adicional a R | Dependencia |
|---|---|---|---|---|
| C-GOV / coordinator (T-0023) | Configuracion por herramienta aplicada y aceptada; evidencia en T-0023/DEC-008/ADR-006 | 021; P21, modelos/environment validados; herencia aprobada documentada | `.ies/models.yaml`, `.ies/environment.yaml` por CLI soportado, entrega propia; fuentes de memoria solo según contrato coordinator | Gate de configuración propio |
| I-UI / implementer | Spec aprobada + baseline → CSS centrado y evidencia Safari | 001–003,020,022; P01–03,20,22 | `apps/web/app/globals.css`, `apps/web/app/(dashboard)/layout.tsx`, `apps/web/tests/layout-responsive/`, `apps/web/lib/layout-responsive.test.mjs` | T-0022 aceptada; gate I-UI |
| V-UI / viewer | SHA/entrega I-UI → APROBAR/CORREGIR/BLOQUEAR | 001–003,020,022; cotejo y reproducción focalizada | Solo entrega/evidencia propias; fuente solo lectura | Gate humano de revisión I-UI |
| I-SERVER / implementer | Base UI aceptada + contratos → auth, repositorio, aislamiento, modelo, migración SQL y tests | 004–007,009–012,014–016,018–022; P04–07,09–12,14–16,18–22 (porción API/DB) | `apps/web/lib/chat/`, `apps/web/lib/infra/`, `apps/web/lib/condition.ts`, `apps/web/lib/dashboard.ts`, `apps/web/lib/mesocycle.ts`, `apps/web/lib/supabase.ts`, `apps/web/lib/openaiModels.ts`, `apps/web/app/api/chat/`, `apps/web/app/api/conversations/`, `apps/web/app/(dashboard)/`, `apps/web/tests/chat-server/`, `apps/web/lib/chat-server.test.mjs`, `supabase/migrations/20261017_coach_history.sql`, `supabase/tests/coach_history/` | I-UI revisada, aceptada/cerrada e integrada por humano; gate I-SERVER |
| V-SERVER / viewer | SHA y DB test I-SERVER → veredicto de datos/auth/modelo | REQ I-SERVER, pruebas correspondientes y gate máquina | Solo entrega/evidencia propias | Gate humano después de I-SERVER |
| I-CLIENT / implementer | Servidor aceptado → login, ViewModel, historial/migración/errores, modelo sin selector, release candidato | 001–022 excepto implementación config021; P01–22 en conjunto | `apps/web/components/CoachChat.tsx`, `apps/web/components/CoachChatScreen.tsx`, `apps/web/components/CoachModelSelect.tsx`, `apps/web/hooks/`, `apps/web/app/login/`, `apps/web/app/(chat)/`, `apps/web/app/globals.css`, `apps/web/lib/coachStorage.ts`, `apps/web/lib/infra/auth/`, `apps/web/lib/infra/chat/`, `apps/web/tests/chat-client/`, `apps/web/lib/chat-client.test.mjs` | I-SERVER revisada, aceptada/cerrada e integrada por humano; gate I-CLIENT |
| V-INTEGRAL / viewer | SHA candidato y evidencia → veredicto integral UI/datos | Todos, P01–22, Safari y dos navegadores | Solo entrega/evidencia propias | Gate humano después de I-CLIENT |

Viewer no depende formalmente de una task implementer aún sin cierre si el CLI exige done/archived para compilar; puede depender de T-0022 cerrada y llevar SHA/entrega a revisar en input, como precedente T-0018. Coordinator bloquea despacho hasta gate humano; no cerrar implementer prematuramente para satisfacer --depends. Cada viewer es instancia independiente del implementer, incluso si su familia de modelo coincide. Si el transporte nativo no garantiza cwd/worktree efectivo, no despachar codificación hasta corregirlo; no resolver con checkout compartido.

## 5. Trazabilidad y orden tests-first

| Grupo REQ | Pruebas | Ejecutor principal / QA | Evidencia futura |
|---|---|---|---|
| 001–003 | P01–03 | I-UI / V-UI; regresión I-CLIENT / V-INTEGRAL | Mediciones Safari, capturas focalizadas, rutas reales |
| 004–006 | P04–06 | I-SERVER / V-SERVER; login final V-INTEGRAL | Auth/RLS real test, persistencia reinicio, dos navegadores |
| 007–008 | P07–08 | I-CLIENT / V-INTEGRAL | 31 entradas paginadas, estados de error |
| 009–010 | P09–10 | I-SERVER / V-SERVER | Constraints/operaciones y carrera reproducida |
| 011–013 | P11–13 | I-CLIENT / V-INTEGRAL | Original intacto, reinicio de importación, cuenta destino y logout |
| 014–016 | P14–16 | I-SERVER / V-SERVER; errores UI V-INTEGRAL | Vínculo, payload LLM, mock fallos y cero fallback |
| 017 | P17 | I-CLIENT / V-INTEGRAL | Ausencia selector y etiqueta |
| 018–019 | P18–19 | I-SERVER / V-SERVER; integral | Conteos DB/payload y revisión logs sintéticos |
| 020 | P20 | Cada implementer / su viewer | Versiones y diff, sin downgrade |
| 021 | P21 | C-GOV / viewer del paquete | Canonical config y modelo observado declarados |
| 022 | P22 | Cada implementer / su viewer | Grafo/imports nuevos y comandos ejecutados |

Estado de todas las pruebas: **pendiente**. Primero caso que falla con el defecto pertinente, después código mínimo y test verde. No volver a abrir auditorías aceptadas sin drift. V-INTEGRAL reutiliza las pruebas DB/modelo aceptadas y repite únicamente las afectadas por el diff cliente, además del recorrido end-to-end; no duplica la auditoría completa V-SERVER. Ejecutar `npm test` y `npm run build` en worktree con configuración sintética; incluir nuevas suites en comando real, no tests de mera búsqueda textual que imiten código. El test de arquitectura debe resolver imports relevantes (incluidos aliases), no afirmar pureza porque se movió un archivo.

Antes de viewer: `IES_ACTOR=implementer ies git verify --task T-XXXX`; viewer ejecuta models validate, memory validate, doctor, constitution check, git verify y gate como `IES_ACTOR=viewer`. Registrar SHA y resultados, archivos versionados intactos. Gate sin comandos de pruebas no sustituye evidencia npm/Safari/DB. VII-08 conocido sigue ligado a T-0020; no declararlo resuelto por esta entrega. Las pruebas de la regla de dependencia tocada sí son obligatorias aunque el registro global del gate siga pendiente.

## 6. Gates humanos y configuración

| Gate | Aprueba exactamente | No incluido |
|---|---|---|
| G0 aprobado (DEC-009) | Entrega T-0022 y decisiones SPEC/PLAN/ADR; coordinator materializa documentos y registra decisión por CLI | No despacha implementación ni viewer automáticamente |
| G1 configuración aceptada (DEC-008/T-0023) | Codex Astra High y retorno Gemini para Antigravity; herencia de subagentes sin override documentada en ADR-006 | Configuración no prueba el modelo efectivo de sesiones abiertas |
| G2 por implementer | Task/prompt/allowlist/worktree concretos, baseline, código y tests sintéticos aislados previstos | No producción, usuarios reales ni inferencia cloud |
| G3 por entrega | Despacho viewer sobre SHA entregado | No merge ni cierre por sí solo |
| G4 por candidato aceptado | Aceptación, cierre y **merge humano** del SHA revisado | No push/deploy implícitos; atención a auto-deploy |
| G5 cloud/auth | Proyecto/cuenta concretos, OTP/redirects, schema aditivo y vínculo owner aprobados; backup definido | No importación legacy ni publicación automática |
| G6 modelo | Una prueba sintética acotada de acceso a gpt-6-luna high con presupuesto y cuenta confirmados | No pruebas con conversaciones/salud reales ni fallback |
| G7 release | Publicación humana exacta, versión/SHA y smoke acordados | No borrar schema ni datos para rollback |
| G8 importación | Confirmación del propietario/cuenta dentro de UI y lote legacy elegido | No limpieza del original ni migración de otro usuario |

G5/G6 pueden prepararse después del viewer servidor, antes de release; secuencia de gates no equivale a permiso acumulativo. G8 exige G5/G7 completos y confirmación por cuenta. Se conserva HITL por gate hasta instrucción expresa distinta.

G1 ya fue ejecutado y aceptado en T-0023/DEC-008/ADR-006; no se repite por G0. Esa decision posterior a la propuesta del planner prevalece para la seleccion por herramienta y la herencia de subagentes sin override. No se modifica la configuracion en esta materializacion. HITL no es un rol nuevo del registry. El modelo efectivo de sesiones abiertas sigue NO_VERIFICADO y no constituye por si solo un bloqueo. Mantener los limites de concurrencia y retorno Gemini de ADR-006.

## 7. Versionado, dependencias previas y rollback

Version aceptada: **0.4.0 MINOR** por nueva identidad e historial sincronizado. La propuesta 0.3.2 de T-0021 no fue aprobada y queda sustituida en diseño. Una entrega desplegable por etapa: I-UI `0.4.0-rc.1`, I-SERVER `0.4.0-rc.2`, I-CLIENT `0.4.0`; solo se publica el paquete final, salvo nuevo gate. Actualizar manifiesto, ambos niveles del lock, test, README y CHANGELOG por etapa, sin actualización incidental de dependencias. Si hay drift de versión al despacho, resolver reserva antes de ejecutar.

Dar prioridad al paquete; reservar R de forma serial. T-0017 (objetivo histórico 0.3.1) y T-0020 (depende de ella) no se modifican ni integran aquí. Antes de retomar T-0017, gate separado para actualizar su versión al siguiente PATCH libre de la línea vigente, sin downgrade ni atribuir sus correcciones a 0.4.0. T-0020 conserva su dependencia y dueños de `.ies/gate.yaml`/herramientas de arquitectura; no despachar en paralelo sus archivos compartidos. No asumir que `ready` implica ausencia de ramas: contrastar solo diferencias/versiones compartidas al reservar escritor.

Rollback antes de release: conservar checkpoint/worktrees y rechazar candidato sin tocar principal. Después de release: deshabilitar envío/importación por configuración operativa prevista, conservar lectura privada si sigue siendo segura, mantener todas las tablas y copias. **No volver a publicar sin más la vieja app**, porque su escritor local recorta historial a cuatro y no tiene protección del nuevo flujo. Candidato de rollback debe mantener auth y lectura segura o servir mantenimiento; humano lo identifica y ensaya con datos sintéticos antes del release. Revert fuente hacia adelante en nueva versión autorizada; no drop de tablas ni force-push. Una restauración DB real requiere nueva aprobación, prueba y reconciliación de escrituras posteriores; no tratar backup como permiso para sobrescribir datos.

## 8. Entrega a producción — ejecución humana

1. Confirmar SHA final, viewer sin BLOCKING, gate máquina PASS en ese SHA, versiones y aprobación de integración. Registrar proyecto/cuenta/deployment anteriores sin secretos. Merge/push con auto-deploy cuenta como publicación y exige G7; no dispararlo desde un gate solo de código.
2. G5: inspección acotada por humano de Auth y políticas efectivas; confirmar perfil owner y las tres tablas de contexto. Preparar backup cifrado verificable del esquema/datos afectados en almacenamiento privado, nunca repo/deliverable. Registrar existencia, fecha y prueba de restauración sintética, sin contenido. Aplicar migración **aditiva** con transacción/rollback de fallo y sin drop/alter destructivo de tablas existentes; validar RLS con identidades de test aprobadas. Si hay políticas incompatibles, detener antes de habilitar chat.
3. Configurar OTP/invitaciones, redirects exactos y secretos exclusivamente del servidor. No imprimirlos. Verificar login/logout/expiración. Registrar vínculo owner real solo después de identificación explícita del humano; no tomar el primer usuario creado como propietario del MVP.
4. G6: prueba de proveedor mínima con contenido ficticio y sin contexto de salud, timeout y presupuesto aprobados. Validar respuesta/identificador y payload high. Un 403/404 bloquea release del chat; no sustituir modelo ni bajar esfuerzo. El mock previo no cumple este gate.
5. G7: desplegar desde proyecto y SHA aprobados por humano, usando panel/procedimiento vigente; no reutilizar ciegamente script `deploy:prod --yes`. Release notes 0.4.0: centrado Safari, login/historial privado sincronizado, importación voluntaria conservadora, GPT-6 Luna High exclusivo; limitaciones de datos descartados y contexto reciente explícitas. No afirmar cambios de T-0017/T-0020.
6. Smoke humano en Safari y segundo navegador con cuenta de test autorizada: guardar >4, recargar, verificar misma cuenta/aislamiento, navegación, centrado ancho grande/móvil y estado de error. Si falta permiso para persistencia sintética en entorno release, ejecutar en staging equivalente y reservar smoke productivo exacto a su gate; no llamarlo validación de producción.
7. G8: humano inicia copia legacy al confirmar cuenta y lote en UI, coteja conteos/resultado; deja original intacto. Es independiente de aplicar SQL. No enumerar ni subir historial real desde un agente por este plan.
8. Observar 15min y revisar 24h según SPEC §8. Ante acceso cruzado o pérdida confirmada, activar mantenimiento/rollback seguro preservando tablas y copias; documentar incidente sin datos personales. Aceptación final distingue tests, staging y producción observada. Ningún agente ejecuta deploy, merge o mutaciones reales por esta entrega.
