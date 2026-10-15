<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: sdd-verify

SDD: verificar entregas con el viewer y cerrar con aprobacion humana.

## Pasos

1. Crea la task de verificacion con `--destination viewer --depends T-XXXX` por cada entrega.
2. Genera `ies prompt viewer --task T-VVVV --copy` y pegalo en un agente de solo lectura.
3. El viewer ejecuta `IES_ACTOR=viewer ies gate --task T-XXXX` (alcance, constitucion, secretos, tests/lint/build en solo lectura y contraste de `sdlc:` con la evidencia); FAIL = BLOQUEAR. Comprueba ademas la cobertura SDLC (`sdlc_coverage` en el veredicto; un bloque faltante es NON_BLOCKING salvo que esconda un defecto).
4. Si el veredicto no tiene hallazgos BLOCKING, el humano ejecuta `ies task done` (exige gate PASS sobre el commit actual y sin BLOCKING constitucional, salvo --human-override), el merge del worktree (el hook de `ies gate --install-hook` lo vuelve a exigir) y `ies git worktree remove --task T-XXXX --delete-branch`.
5. Si hay BLOCKING, una unica ronda correctiva consolidada; la task fast-track vuelve a riguroso.
