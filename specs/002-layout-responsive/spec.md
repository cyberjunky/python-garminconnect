---
schema_version: 1
spec_id: SPEC-002
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

# SPEC-002: Centrado responsive, historial privado sincronizado y modelo exclusivo

Origen: propuesta T-0022, materializada por T-0024 tras aprobacion humana G0; DEC-009.
Autonomia: `hitl`; cada gate de ejecucion conserva aprobacion propia.

## 1. Problema
La distribución no está centrada dentro del área principal de Safari. El historial local se recorta a cuatro entradas y no existe recuperación desde servidor en otros dispositivos. La selección actual de modelos tampoco cumple la nueva instrucción exclusiva. El valor esperado es una interfaz equilibrada y conversaciones recuperables por su propietario, con guardado verificable y modelo fijo.

## 2. Alcance

**No objetivos:** recuperar datos ya descartados sin copia; rediseño visual general; auditar toda la plataforma; modificar Garmin, collector o tokens; compartir conversaciones entre usuarios; borrado automático; funcionamiento offline completo; streaming, herramientas LLM o cambio de endpoint por sí mismo; publicar la app; dar por seguro todo el dashboard heredado; modificar contratos del framework o bindings de todos los roles.

**Objetivos:** centrar las cuatro rutas dashboard y preservar chat; habilitar login, historial privado y sincronización al recargar/cambiar de navegador; importar de forma conservadora copias locales supervivientes; forzar modelo/esfuerzo en servidor; establecer evidencia, rollback y gates claros.

## 3. Restricciones

Sí hay código desplegable: aplica Artículo VII.2 y `clean-architecture`. Dominio puro, puertos de aplicación y adaptadores externos separados. La complejidad nueva del chat justifica ViewModel/hook dedicado; no convertir las páginas estáticas por inercia. ADR-004 mantiene la excepción existente para ellas. Todos los roles siguen SDLC, EARS, Clean Code, Clean Architecture, HITL y WORKING_DISCIPLINE. Un implementer por task/worktree; viewer independiente. Dependencias nuevas solo si el ADR y el gate las autorizan. Reutilizar SDK Supabase instalado y fetch; no añadir otro proveedor de identidad.

## 4. Requisitos EARS y criterios

Todos son `must`. Las referencias Pxx identifican pruebas reproducibles definidas aquí; no son resultados ejecutados.

| REQ | Patrón | Requisito | Prueba / aceptación |
|---|---|---|---|
| REQ-001 | Estado | MIENTRAS se muestre una ruta dashboard incluida, el sistema deberá centrar su contenedor en el área principal según G. | P01: todas las mediciones de matriz S cumplen G en Safari real. |
| REQ-002 | Estado | MIENTRAS se muestre una ruta incluida, el sistema deberá mantener sus controles accesibles sin overflow horizontal global. | P02: `max(body.scrollWidth,documentElement.scrollWidth)-documentElement.clientWidth <=1px`; controles alcanzables, sin recorte/solapamiento; scroll interno llega al extremo. |
| REQ-003 | Evento | CUANDO se active una navegación incluida, el sistema deberá mostrar el destino esperado. | P03: ciclo cuatro dashboard→chat real con ID→historial→chat→volver, a 375 y ancho grande; chat conserva compositor centrado y roles de burbuja. |
| REQ-004 | No deseado | SI no existe sesión válida, ENTONCES el servidor deberá rechazar el acceso al historial y envío de chat. | P04: ausencia, expiración y token alterado dan 401, sin consulta de salud ni llamada LLM; UI solicita login sin mostrar contenido anterior. |
| REQ-005 | Estado | MIENTRAS una identidad esté autenticada, el sistema deberá limitar cada operación de conversación a su propietario. | P05: usuarios A/B y anon intentan lectura, inserción, actualización e importación cruzada mediante API y DB/RLS; cero filas ajenas accesibles, respuestas 403/404 sin contenido. `user_id` cliente nunca determina propietario. |
| REQ-006 | Evento | CUANDO el servidor confirme guardado, el sistema deberá recuperar íntegramente ese contenido desde otro navegador de la misma cuenta. | P06: guardar seis chats y mensajes en DB aislada real, reiniciar servidor, recargar/reabrir Safari y leer en navegador B; IDs, orden y contenidos coinciden. |
| REQ-007 | Evento | CUANDO se solicite la siguiente página de historial, el sistema deberá devolver las entradas restantes sin descartarlas del almacenamiento. | P07: 31 chats sintéticos, páginas de 20, orden estable por fecha/ID, sin faltantes; total DB permanece 31. Ningún TTL o límite de cuatro. |
| REQ-008 | No deseado | SI una escritura falla o no tiene confirmación, ENTONCES la interfaz deberá identificar el mensaje como no guardado. | P08: timeout, red, cuota y 5xx no muestran «Guardado»; borrador permanece visible/exportable; recargar no sustituye servidor por lista vacía. |
| REQ-009 | Evento | CUANDO se repita una operación con el mismo identificador, el sistema deberá devolver su resultado persistido sin duplicarlo. | P09: reintento por respuesta HTTP perdida y doble clic crean un único mensaje/operación; importación repetida tampoco duplica. |
| REQ-010 | No deseado | SI dos clientes escriben sobre la misma revisión, ENTONCES el sistema deberá conservar el contenido confirmado mediante control de concurrencia. | P10: dos escritores reciben éxito/409 de forma determinista; conflicto refresca historial y conserva borrador, sin last-write-wins de toda la conversación. |
| REQ-011 | Evento | CUANDO el usuario confirme la cuenta destino de una importación local, el sistema deberá copiar las conversaciones supervivientes sin alterar los originales. | P11: cuenta visible y confirmación antes de importar; cancelación no escribe; snapshots iguales no duplican; ID colisionado con contenido distinto se copia separado; localStorage original byte a byte igual. |
| REQ-012 | No deseado | SI la importación se interrumpe, ENTONCES el sistema deberá permitir reanudarla desde los resultados confirmados. | P12: interrupción a mitad de lote, reintento y cuota producen informe por entrada sin omisiones silenciosas; JSON inválido informa error y preserva fuente. |
| REQ-013 | Evento | CUANDO cambie o cierre la sesión, el sistema deberá retirar de la interfaz los datos de la cuenta anterior. | P13: A→logout→B no conserva historial, borradores ni respuestas pendientes de A; una respuesta tardía se descarta por sesión; copia legacy queda sin importar hasta confirmación. |
| REQ-014 | No deseado | SI no existe vínculo autorizado al perfil de salud, ENTONCES el chat deberá impedir el uso de contexto personal heredado. | P14: usuario B sin vínculo no lee salud MVP ni llama al proveedor; owner A vinculado recibe solo su contexto. Alterar ID en request no cambia el perfil. |
| REQ-015 | Evento | CUANDO el servidor solicite una respuesta del coach, el sistema deberá usar exclusivamente `gpt-6-luna` con esfuerzo `high`. | P15: interceptar fetch de servidor: `model:gpt-6-luna`, `reasoning_effort:high`; sin temperature/top_p/top_logprobs/tools; inputs cliente/env/preferencia vieja no cambian payload. |
| REQ-016 | No deseado | SI el modelo no está disponible o su respuesta no puede persistirse, ENTONCES el sistema deberá presentar un error recuperable sin sustituir el modelo. | P16: 401/403/404/429/5xx proveedor y fallo DB posterior producen error tipificado, cero invocaciones de otro modelo, mensaje usuario persistido; respuesta no confirmada no se anuncia guardada. |
| REQ-017 | Estado | MIENTRAS se use el chat, la interfaz deberá identificar el modelo exclusivo sin ofrecer selección. | P17: ambas entradas del chat carecen de selector; etiqueta GPT-6 Luna · High; preferencias antiguas ignoradas sin borrado de historial. |
| REQ-018 | Ubicuo | El sistema deberá conservar los mensajes almacenados independientemente de la ventana enviada al modelo. | P18: conversación de 20 mensajes; DB conserva 20, payload lleva últimos 12 pertinentes y mensaje de sistema; no cambia contenido almacenado para truncar contexto. |
| REQ-019 | Ubicuo | La operación deberá registrar únicamente metadatos técnicos necesarios para diagnosticar guardado e inferencia. | P19: fallos sintéticos en auth/DB/importación/LLM; logs sin textos, salud, tokens, emails o claves, con operation_id opaco, código, duración y resultado. |
| REQ-020 | Ubicuo | Cada entrega desplegable deberá declarar una versión ascendente coherente con el orden aprobado. | P20: package/lock/versión visible/test/README/CHANGELOG concuerdan; ninguna integración reintroduce 0.3.1 sobre 0.4.x. |
| REQ-021 | Ubicuo | Cada ejecución de agente deberá declarar su rol, binding, modelo efectivo observado y gate autorizado. | P21: prompt generado, task válida, registro de modelo; no atribuir eficacia a YAML o modelo efectivo no observado. |
| REQ-022 | Ubicuo | El código nuevo o tocado deberá respetar la dirección de dependencias declarada. | P22: comprobación por máquina de imports y revisión: dominio sin Next/React/Supabase/red; UI usa ViewModel; infraestructura implementa puertos. |

## 5. Geometría G y matriz Safari S

Se acepta el máximo **1120px** propuesto en T-0021 mediante DEC-009 y ADR-003. Medir `.app-main` ancho A y `main` dashboard ancho W, cajas con padding: viewport >800, W=min(A,1120), padding 28px; viewport <=800, W=A, padding 16px. Desvío de ancho/padding <=2px; diferencia entre márgenes izquierdo y derecho <=2px. Centrar respecto al área después de sidebar, no al viewport entero. En chat, compositor máximo 880px y centrado respecto a su contenedor; no centrar burbujas individualmente.

Prueba proporcional: medir cuatro dashboard y chat a **375 y 1600px**, o al ancho amplio real reportado si es mayor y puede reproducirse; añadir Inicio/chat a **800 y 801px** para el breakpoint. Son 14 celdas con medición y revisión visual, no 40 capturas. Registrar viewport real, zoom100%, `clientWidth`, navegador/versión, ruta final y SHA. Baseline comparativo Inicio ancho grande + Inicio móvil + chat ancho grande; candidato esas tres capturas más una de cada otra ruta dashboard en ancho grande y chat móvil/historial. Capturas adicionales solo ante fallo. Safari macOS estrecho no certifica teclado iOS. WebKit automatizado puede complementar; no reemplaza Safari real. Toda evidencia usa datos sintéticos.

## 6. Retención y límites

Servidor conserva conversaciones y mensajes sin borrado automático; paginación no cambia retención. No se añade función de eliminación en este alcance. Contenido nuevo máximo 4000 caracteres por mensaje: excederlo se rechaza visiblemente, nunca se recorta para guardar. Importación conserva mensajes legacy completos; entradas excepcionalmente grandes se rechazan con motivo, sin modificar original ni truncar en silencio. Tamaño por request/importación limitado y validado; lotes de diez conversaciones máximo, cada conversación hasta 1MiB serializado; más requiere lotes o decisión explícita. La cuota de servicio puede impedir escribir; nunca justifica eliminar conversaciones antiguas. Presupuesto y cuota exactos de cuenta se verifican en gate cloud.

La ventana del proveedor mantiene hasta los últimos 12 mensajes y el sistema; no hay borrado por ese límite. API obtiene historia del servidor, no acepta una historia arbitraria ni un mensaje system del cliente. La UI comunica que recordar contexto reciente no equivale a borrar el historial completo.

## 7. Riesgos y condiciones de parada

Detener el gate afectado ante identidad/proyecto cloud ambiguo, necesidad de ampliar acceso a tablas heredadas, exposición cruzada, dato real en fixtures/logs, modelo sin acceso, migración incompatible o imposibilidad de probar persistencia real aislada. No bloquear planificación por diferencia de modelo de agentes. No prometer ejecución hasta verificar transportes.

No se conoce configuración productiva Auth/RLS ni plan/cuotas; requieren gate propio. Para salud, solo el vínculo acotado de owner y las tres tablas consultadas por chat están dentro del diseño. Si seguridad efectiva exige corregir políticas de más recursos o migrar collector, detener y proponer alcance adicional; no presentar este trabajo como auditoría general.

## 8. Seguridad y operación

Login de Supabase Auth por email OTP/invitación, alta pública deshabilitada; solo cuentas invitadas. Cuenta humana se confirma antes de vincular perfil MVP y antes de importar. API valida token en servidor; clave anónima/publicable no prueba identidad. Historial usa cliente con JWT del usuario y RLS, nunca service-role para eludir el aislamiento. Tokens fuera de logs/Git; no copiar conversaciones reales en evidencia. CORS mismo origen y mutaciones con Authorization explícito, sin aceptar identidad de cookies no verificadas o cuerpo cliente.

Observar durante 15min de smoke y primeras 24h tras release: fallos técnicos de guardado/importación/auth, errores de modelo y geometría reportada. Cualquier acceso cruzado o pérdida de contenido confirmado detiene aceptación inmediatamente; un error de guardado muestra aviso inmediato; tres fallos consecutivos con red disponible requieren revisar servicio y detener nuevos envíos, conservando lo pendiente. Sin monitor/automatización nuevo implícito: revisión humana de métricas/logs existentes. Reabrir spec si se solicita sharing, offline completo, tools LLM, otro modelo o eliminación automática.
