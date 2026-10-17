# ADR-003:Contenedor centrado con límite de lectura

- Estado: aceptado por aprobacion humana G0, DEC-009; implementacion pendiente
- Fecha: 2026-10-17
- Task: T-0022 (propuesta); T-0024 (materializacion)
- Contexto: dashboard limitado a 880px con margen cero, defecto observado Safari; chat independiente.
- Decisión: máximo1120px centrado en área principal, padding28/16 según breakpoint800; preservar compositor y burbujas. Matriz Safari proporcional de SPEC-002.
- Alternativas: centrar880 es más conservador pero reduce área útil; ancho ilimitado reduce legibilidad; no cambiar conserva defecto.
- Consecuencias: CSS reversible y prueba visual real requerida; no confundir centrado con rediseño ni evidencia WebKit con Safari.
