<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: ies-update

Sincronizar estado, memoria y documentacion.

## Pasos

1. Ejecuta `ies update`.
2. Revisa los cambios propuestos y el commit sugerido.
3. Aprueba o rechaza; nada se commitea en silencio.
4. Si hay documentacion semantica desactualizada: `ies update --create-stale-doc-task`, commit del ledger, `ies git checkpoint --task T-XXXX --worktree` y `ies prompt implementer --task T-XXXX --output .ies/worktrees/T-XXXX/PROMPT.md`; la allowlist de esa task autoriza el documento de memory/long/ (ADR-017). Tras cerrarla: `ies update --sync-doc <ref> --task T-XXXX`.
