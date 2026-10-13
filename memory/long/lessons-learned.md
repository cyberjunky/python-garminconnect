---
schema_version: 1
project_id: python-garminconnect
layer: long
last_updated: '2026-10-13T17:15:00Z'
source: coordinator
confidence: alta
---

# Lessons learned

## Prohibición de amend y force-push sobre commits ya empujados (T-0008)

- **Incidente**: Durante la resolución de conflictos del PR 1 (T-0008), el implementer realizó `git commit --amend` y `git push --force-with-lease` para incorporar `memory/mid/tasks.md` tras haber empujado un commit previo (`96fceb8`), a pesar de la prohibición explícita de force-push en el input de la task.
- **Impacto**: No hubo pérdida de datos gracias a `--force-with-lease` sobre su propio commit, pero quebranta la inmutabilidad y trazabilidad del historial compartido.
- **Regla establecida**: Si hay que corregir o agregar archivos tras haber realizado push, se hace obligatoriamente mediante un commit nuevo hacia adelante, nunca con `amend` ni `force-push`.

## Respeto del gate de aprobación formal de la spec antes de implementar (SPEC-001)

- **Incidente**: En `SPEC-001`, las tasks de implementación y verificación (`T-0002` a `T-0007`) se despacharon y completaron mientras la especificación permanecía en `status: ready` (draft/no aprobada), omitiendo el gate mandatorio `ies spec approve <slug>` tras la aprobación humana del plan.
- **Impacto**: La verificación independiente y la validación en vivo revelaron discrepancias operativas (migración no aplicada en producción, fallos de configuración en plataforma externa) que debieron ser detectadas antes de dar por completado el ciclo, forzando una aprobación retroactiva (`DEC-003`).
- **Regla establecida**: Ninguna task de implementación (`implementer`) puede crearse o ejecutarse sin que la spec correspondiente cuente con aprobación humana formal explícita (`ies spec approve <slug>`), garantizando el flujo canónico de SDD (spec -> plan -> aprobación -> task -> implementer -> viewer).


