<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: sdd-verify

SDD: verificar entregas con el viewer y cerrar con aprobacion humana.

## Pasos

1. Crea la task de verificacion con `--destination viewer --depends T-XXXX` por cada entrega.
2. Genera `ies prompt viewer --task T-VVVV --copy` y pegalo en un agente de solo lectura.
3. Si el veredicto no tiene hallazgos BLOCKING, el humano ejecuta `ies task done` y el merge del worktree.
4. Si hay BLOCKING, una unica ronda correctiva consolidada; la task fast-track vuelve a riguroso.
