---
schema_version: 1
project_id: python-garminconnect
layer: long
last_updated: '2026-10-11T12:52:03Z'
source: ies init
confidence: n/a
---

# Constitucion del proyecto python-garminconnect

Principios no negociables. Prevalece sobre specs, planes, tasks y reglas de
IDE. Se enmienda solo por ADR en `memory/long/adr/` y decision humana en
`memory/mid/decisions.md`. Disciplina canonica: `docs/WORKING_DISCIPLINE.md`
y `docs/SDD.md` del framework.

## Articulo I. Autoridad

1. El humano es la unica autoridad de decision; una aprobacion cubre solo
   la propuesta inmediatamente anterior.
2. Ninguna ejecucion sin task valida en `memory/mid/tasks.md`.
3. Ningun merge a la rama principal sin veredicto del viewer sin hallazgos
   BLOCKING y aprobacion humana.

## Articulo II. Spec primero

1. Toda funcionalidad nace en `specs/NNN-slug/spec.md` con requisitos EARS.
2. Una spec aprobada se congela; un cambio crea una version nueva, nunca se
   parchea en el codigo.
3. `plan.md` deriva de `spec.md`; las tasks derivan de `plan.md`; cada task
   referencia sus REQ-NNN.

## Articulo III. Calidad

1. Tests primero: un acceptance criterion sin test es un criterio incumplido.
2. Toda entrega declara verificacion reproducible (skill verification-gates).
3. La suite existente nunca empeora respecto al checkpoint.

## Articulo IV. Seguridad

1. Cero secretos en Git, tasks, memoria o deliverables.
2. Prohibido el deploy a produccion para cualquier agente.
3. Mutaciones sobre datos persistentes, schemas o credenciales exigen
   aprobacion explicita por task.

## Articulo V. Simplicidad

1. Alcance minimo que satisface los criterios; sin dependencias nuevas sin
   ADR.
2. Toda abstraccion nueva se justifica en el plan.

## Articulo VI. Aceleracion

1. El perfil `fast-track` solo aplica a tasks rutinarias, de riesgo bajo o
   medio, completamente reversibles, de un componente y sin sensibilidad.
2. `fast-track` nunca reduce criterios, tests, backups, rollback ni los
   techos de iteracion del framework.
