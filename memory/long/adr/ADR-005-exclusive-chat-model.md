# ADR-005:Modelo exclusivo de producto y selección explícita de agentes

- Estado: aceptado por aprobacion humana G0, DEC-009; implementacion pendiente
- Fecha: 2026-10-17
- Task: T-0022 (propuesta); T-0024 (materializacion)
- Contexto: el humano solicita GPT-6 Luna High solo para producto y Astra High para HITL/Coordinator; la divergencia historica fue resuelta en T-0023/DEC-008.
- Decisión: Chat Completions fijo `gpt-6-luna`, `reasoning_effort:high`, sin selector/fallback ni parámetros incompatibles; acceso cuenta requiere prueba separada. Agentes mantienen roles y bindings canonicos segun DEC-008/ADR-006: seleccion por herramienta con herencia de subagentes sin override; HITL es sesión humana de consulta, no rol nuevo.
- Alternativas: Responses es válido pero añade migración innecesaria sin tools; catálogo seleccionable viola requerimiento; imponer Astra globalmente a Antigravity incumpliria la seleccion por herramienta aprobada.
- Consecuencias: indisponibilidad del modelo es error visible y bloquea aceptación, no ocasión para sustituirlo; modelo configurado y observado deben diferenciarse. No modificar contratos framework ni generar adaptadores a mano.
