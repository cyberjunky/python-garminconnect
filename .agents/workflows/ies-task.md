<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: ies-task

Crear una task y generar su prompt.

## Pasos

1. Ejecuta `ies task add --origin human --destination planner|implementer|viewer ...` con input, expected output y `--criterion` por REQ (equipo SDD; otros roles en docs/ROLES.md).
2. Genera el prompt: `ies prompt <rol> --task T-XXXX --copy` (p. ej. `ies prompt implementer --task T-0002`).
3. Pega el prompt en el agente correspondiente y guarda la entrega en `deliverables/T-XXXX.md`.
4. Cierra con `ies task done T-XXXX` tras revision humana.
