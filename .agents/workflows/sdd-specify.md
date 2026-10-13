<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: sdd-specify

SDD: convertir una intencion humana en spec.md (EARS) y plan.md propuestos.

## Pasos

1. Ejecuta `ies spec new <slug>`; responde la pregunta de autonomia (HITL por gate, o autonomo: una aprobacion del plan y el coordinator conduce hasta el final).
2. Crea la task de planificacion: `ies task add --destination planner --memory-ref long/constitution.md ...`.
3. Genera el prompt: `ies prompt planner --task T-XXXX --copy` y pegalo en un agente planner (solo lectura).
4. Guarda la entrega en `deliverables/T-XXXX.md` y presenta al humano un resumen con la propuesta cerrada.
