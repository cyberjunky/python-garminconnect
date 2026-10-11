<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->

# Instrucciones Copilot — IES-OS

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

- Roles SDD: `coordinator` (agente principal: dimensiona, crea tasks,
  despacha, consolida evidencia; no implementa), `planner` (spec.md con
  requisitos EARS + plan.md + descomposicion), `implementer` (una task
  aprobada, en su worktree, tests primero; se clona uno por task paralela) y
  `viewer` (verificacion solo lectura, hallazgos BLOCKING/NON_BLOCKING).
- Orden obligatorio: spec -> plan -> task (`ies task add`) -> prompt
  (`ies prompt`) -> worktree -> entrega -> viewer -> humano. Las specs viven
  en `specs/NNN-slug/` y se crean con `ies spec new <slug>`.
- Paralelismo: un implementer por task y worktree
  (`ies git checkpoint --task T-XXXX --worktree`); allowlists disjuntas; el
  merge lo hace siempre el humano.
- Perfil de task (`--profile riguroso|fast-track`): fast-track acelera el
  transporte y la revision; nunca reduce criterios, tests, backups, rollback
  ni techos de iteracion.
- Colores del ledger (derivados del estado, nunca persistidos): backlog
  ⚪, ready 🔵, in_progress 🟡, blocked 🔴, done 🟢, superseded 🟣,
  cancelled ⚫, archived 🟤. No confundir con los emojis de readiness de los
  reportes `status` de la disciplina (🟢🟡⚪🔴).

Nota: no se fijan modelos en estos archivos; el binding canonico esta en `config/models.yaml` del framework y puede cambiar sin tocar este repo.
