---
schema_version: 1
project_id: python-garminconnect
layer: long
last_updated: '2026-10-15T09:44:12Z'
source: ies update (migracion ADR-018)
confidence: alta
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
4. Toda entrega que cambia un artefacto desplegable sube su version (SemVer) y registra el cambio en su CHANGELOG (ADR-009).


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

## Articulo VII. Diseno de software

1. Clean Code en todo proyecto: nombres intencionales, funciones pequenas de
   una sola responsabilidad, sin duplicacion, sin codigo muerto ni comentarios
   que sustituyan claridad.
2. Regla de dependencia (Clean Architecture): la logica de negocio no depende
   de frameworks, UI, base de datos ni red; las dependencias apuntan hacia el
   dominio. Aplica a todo proyecto con codigo de aplicacion que se despliega o
   se instala; no aplica a repositorios documentales ni de infraestructura
   declarativa. El planner responde esa prueba en la primera spec y el
   resultado se declara en `memory/long/standards.md`
   (`patron_arquitectonico: clean-architecture | n/a`, `tiene_ui`) antes de la
   primera task implementer.
3. La forma (numero y nombre de capas, patron de presentacion, rutas) es un
   estandar del proyecto en `standards.md`, decidido en el plan; toda app con
   UI (Android, iOS, web) usa MVVM como patron de presentacion, con la logica
   de negocio fuera de la View.
4. `n/a` y toda otra desviacion de este articulo se justifican por ADR en
   `memory/long/adr/`, nunca solo por YAML. Donde hay codigo, la regla de
   dependencia se comprueba por maquina con un comando de `.ies/gate.yaml`.
