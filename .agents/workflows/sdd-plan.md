<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: sdd-plan

SDD: registrar la aprobacion de spec/plan y crear las tasks hijas.

## Pasos

1. Tras el `Ok` humano, registra la decision en `memory/mid/decisions.md` (control `salvar`).
2. Copia el contenido aprobado de spec.md y plan.md a `specs/NNN-slug/` (sin placeholders, con REQ-NNN y la tabla de tasks hijas).
3. Registra la aprobacion: `ies spec approve NNN-slug --decision-ref memory/mid/decisions.md#<fecha>` (pone `status: approved` y audita; nunca edites el status a mano).
4. Crea las tasks hijas exactamente como las define el plan: `--parent`, `--depends`, `--criterion` por REQ, `--profile`.
5. Cierra la task de planificacion con `ies task done T-XXXX` y muestra `ies task list`.
