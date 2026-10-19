<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->

# Reglas IES para Antigravity

Proyecto IES-OS. Reglas minimas (detalle en archivos canonicos):

1. Ninguna accion sin task valida (`memory/mid/tasks.md`).
2. Prompts solo via `ies prompt <rol> --task T-XXXX`.
3. Contratos canonicos: `ies contract <rol>`.
4. Skills canonicas: `ies contract --skill <id>`.
5. Entregas en `deliverables/T-XXXX.md`.
6. Usa workspace isolation, sandbox y worktrees; pide review antes de
   aplicar cambios. NO habilites 'Always Proceed'.
7. Permisos minimos; nunca secretos, deploys ni comandos destructivos.
8. SDD: orden spec -> plan -> `ies spec approve` (tras el Ok humano) -> task -> prompt.
   Empieza SIEMPRE con `ies spec new <slug>`; el status de la spec nunca se edita a mano.
   Destino de toda task: SOLO coordinator | planner | implementer | viewer
   (verificar/revisar -> viewer; implementar/corregir/configurar -> implementer;
   especificar/planificar -> planner). Los especialistas (researcher, worker-local,
   finance, ...) solo si estan habilitados en .ies/environment.yaml o con
   --specialist-reason. Metodologia: `ies contract --doc sdd`. Un agente por task y worktree.
   Tasks paralelas con --allowlist; `ies git verify --task` antes del viewer (DRIFT = BLOCKING).
   Toda entrega declara `sdlc:` por bloque del rol (cubierto|parcial|no-aplica) y lo justifica en `## SDLC`.
9. Comandos como `IES_ACTOR=<rol> ies ...`; `ies doctor` confirma la raiz; `ies gate --task`
   antes de cerrar (task done exige PASS); correcciones con `ies task edit --reason`.

## Disciplina human-in-the-loop

Contrato canonico: `ies contract --doc working-discipline`
(docs/WORKING_DISCIPLINE.md del framework).

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

Las respuestas de la ventana HITL y del coordinator se entregan en una unica
caja copiable (`Copia y pega solo esta caja en este chat:` o
`Pega esto en <agente>:`) cuando la herramienta no hace el handoff
automatico (Articulo II.4 de la constitucion).
