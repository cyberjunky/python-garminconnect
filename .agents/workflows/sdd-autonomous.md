<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: sdd-autonomous

SDD: ejecucion autonoma aprobada (spec con autonomy: autonomous).

## Pasos

1. Precondicion: el humano aprobo spec.md y plan.md con `Ok`; registrala con `ies spec approve NNN-slug` (esa aprobacion cubre todo el ciclo).
2. Crea TODAS las tasks hijas del plan con `--autonomy autonomous --criterion <REQ...>`; sin criterios el CLI las rechaza.
3. Para cada task sin dependencias pendientes: checkpoint + worktree, `ies prompt implementer --task T-XXXX --output .ies/worktrees/T-XXXX/PROMPT.md`, lanza el implementer; en paralelo cuando las allowlists son disjuntas.
4. Por cada entrega lanza el viewer. APROBAR -> `ies task done T-XXXX` (exige result: success). CORREGIR -> una unica ronda correctiva consolidada y nuevo viewer. BLOQUEAR o segundo fallo -> `ies task block --reason` y detente.
5. Integra cada worktree aprobado en la rama de integracion `sdd/NNN-slug` (nunca en main). Repite hasta cerrar todas las tasks.
6. Entrega final al humano: tablero, evidencia por REQ, rama `sdd/NNN-slug` lista y UNA propuesta: el merge a main. Recuerda la seccion 8 del plan (entrega a produccion, la ejecuta el humano). `ies update` y `ies bye`.
7. Detente antes solo por: secreto, permiso de plataforma, decision material, mutacion sensible no autorizada o hecho inobservable.
