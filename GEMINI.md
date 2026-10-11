<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->

# GEMINI.md — IES-OS (Google Gemini)

Proyecto gestionado por IES-OS. El contexto canonico es:

- Contratos: `/Users/alarcondiegof/ies-projects/ies-framework/contracts/roles/`
- Skills: `/Users/alarcondiegof/ies-projects/ies-framework/skills/`
- Memoria: `memory/` (usa solo la seleccionada por el prompt)
- Tasks: `memory/mid/tasks.md`

## Reglas IES (no negociables)

1. Ninguna ejecucion sin una task valida del ledger `memory/mid/tasks.md`.
2. El prompt operativo se genera SOLO con `ies prompt <rol> --task T-XXXX`.
3. Los contratos de rol canonicos viven en `/Users/alarcondiegof/ies-projects/ies-framework/contracts/roles/`.
4. Las skills canonicas viven en `/Users/alarcondiegof/ies-projects/ies-framework/skills/`.
5. Los bindings de modelo viven SOLO en `/Users/alarcondiegof/ies-projects/ies-framework/config/models.yaml` (o el
   override del proyecto `.ies/models.yaml`); nunca fijes modelos aqui.
6. Memoria por capas en `memory/` (immediate/mid/long); usa unicamente la
   memoria seleccionada por el prompt.
7. Toda entrega va a `deliverables/T-XXXX.md` con el envelope requerido.
8. Roles single-shot-hitl: una ejecucion, una entrega, aprobacion humana.
   Sin subagentes y sin loops; la unica excepcion es `coordinator`, que
   delega exclusivamente mediante tasks del ledger (una task, un prompt,
   un agente) y nunca edita codigo.
9. Validaciones: `ies models validate`, `ies memory validate`, `ies doctor`.
10. Nunca commitees secretos; nunca hagas deploy; nunca ejecutes comandos
    destructivos.

## Disciplina human-in-the-loop

Contrato canonico: `/Users/alarcondiegof/ies-projects/ies-framework/docs/WORKING_DISCIPLINE.md`.

Aprobaciones conversacionales (`Ok`, `Acepto`, `De una`, `Adelante`,
`Continua`, `De acuerdo`, `Run`, `Correr`, `Ejecutar`): cubren solo la
propuesta inmediatamente anterior, no amplian el alcance y autorizan su
ejecucion cuando la propuesta es cerrada, ejecutable y no reserva la
operacion a una ventana externa. No exigen una segunda confirmacion y no son
comandos de shell ni alias de Typer.

Controles de persistencia (`salvar`, `guardar`, `actualizar`): autorizan
unicamente la persistencia definida en el contrato canonico (estado,
decisiones, contexto, handoff); no aprueban ninguna propuesta y no
autorizan implementacion, commits, pushes, instalaciones ni despliegues.

Toda ejecucion requiere una propuesta o prompt cerrado generado con
`ies prompt <rol> --task T-XXXX` y aprobacion humana explicita antes de
actuar. Si la propuesta reserva transporte externo, la aprobacion genera el
paquete; en caso contrario permite ejecutar a la ventana designada.

## Sistema multi-agente SDD

Metodologia canonica: `/Users/alarcondiegof/ies-projects/ies-framework/docs/SDD.md` (HITL + Spec-Driven Development +
EARS). Constitucion del proyecto: `memory/long/constitution.md`.

- Destino de toda task: SOLO el equipo SDD (coordinator, planner, implementer,
  viewer). Mapeo: especificar/planificar -> planner; implementar, corregir,
  configurar, migrar, documentar -> implementer; verificar, revisar, validar
  -> viewer (incluida la causa raiz de un fallo); orquestar -> coordinator.
  Los roles especialistas (researcher, worker-local, ceo-strategy, finance,
  operations-health, marketing, sales) solo son destino si estan habilitados
  en `.ies/environment.yaml` (`ies env set --specialist ...`) o con
  `--specialist-reason "causa concreta"`; el CLI rechaza el destino sin ello.
- Roles SDD: `coordinator` (agente principal: dimensiona, crea tasks,
  despacha, consolida evidencia; no implementa), `planner` (spec.md con
  requisitos EARS + plan.md + descomposicion), `implementer` (una task
  aprobada, en su worktree, tests primero; se clona uno por task paralela) y
  `viewer` (verificacion solo lectura, hallazgos BLOCKING/NON_BLOCKING).
- Orden obligatorio: spec -> plan -> aprobacion humana (`ies spec approve`)
  -> task (`ies task add`) -> prompt (`ies prompt`) -> worktree -> entrega ->
  viewer -> humano. Las specs viven en `specs/NNN-slug/`, se crean con
  `ies spec new <slug>` y su `status` nunca se edita a mano. El despliegue lo
  ejecuta el humano siguiendo la seccion 8 del plan; ningun agente despliega.
- Paralelismo: un implementer por task y worktree
  (`ies git checkpoint --task T-XXXX --worktree`); allowlists disjuntas; el
  merge lo hace siempre el humano.
- Perfil de task (`--profile riguroso|fast-track`): fast-track acelera el
  transporte y la revision; nunca reduce criterios, tests, backups, rollback
  ni techos de iteracion.
- Autonomia (se pregunta UNA vez al crear la spec: `ies spec new`): `hitl` =
  aprobacion humana en cada gate; `autonomous` = una sola aprobacion del plan
  cubre todo el ciclo y el coordinator lanza y conduce a planner, implementers
  y viewer hasta el final sin preguntas intermedias. Puertas de calidad que
  garantizan la entrega en autonomous: criterios por REQ obligatorios, tests
  por criterio, viewer por entrega (solo BLOCKING detiene, una ronda correctiva
  consolidada), `ies task done` exige deliverable con `result: success`, y las
  condiciones de parada de la disciplina. El merge a la rama principal sigue
  siendo humano; cualquier bloqueo material detiene el ciclo y se reporta.
- Colores del ledger (derivados del estado, nunca persistidos): backlog
  ⚪, ready 🔵, in_progress 🟡, blocked 🔴, done 🟢, superseded 🟣,
  cancelled ⚫, archived 🟤. No confundir con los emojis de readiness de los
  reportes `status` de la disciplina (🟢🟡⚪🔴).

No hay credenciales en este repositorio: la API key vive en la variable de entorno `GEMINI_API_KEY`.
