<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: sdd-implement

SDD: ejecutar tasks en paralelo, una por agente y worktree.

## Pasos

1. Por cada task ready sin dependencias: `ies git checkpoint --task T-XXXX --worktree`.
2. Genera el prompt: `ies prompt implementer --task T-XXXX --output .ies/worktrees/T-XXXX/PROMPT.md`.
3. Abre un agente por worktree con su PROMPT.md; sandbox y review activados, nunca 'Always Proceed'.
4. Cada agente entrega `deliverables/T-XXXX.md` dentro de su worktree y se detiene.
