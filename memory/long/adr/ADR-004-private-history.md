# ADR-004:Historial privado y copia conservadora por identidad

- Estado: aceptado por aprobacion humana G0, DEC-009; implementacion pendiente
- Fecha: 2026-10-17
- Task: T-0022 (propuesta); T-0024 (materializacion)
- Contexto: historial local de cuatro entradas sin recuperación entre dispositivos; el contexto de salud usa perfil MVP fijo.
- Decisión: Supabase Auth por invitación y repositorio Postgres privado por propietario/RLS; vínculos explícitos de salud; operaciones idempotentes/revisión; importación opt-in por snapshot conservando original. Reutilizar SDK ya instalado. Nuevas abstracciones se limitan a puertos de identidad, historial, contexto y proveedor para probar reglas sin red.
- Alternativas: local ilimitado incumple sincronización; proveedor/backend nuevo aumenta operación; importación automática arriesga atribución incorrecta.
- Consecuencias: nuevos gates de identidad/datos, cuotas y rollback conservador; no promete recuperar conversaciones descartadas. Chat con ViewModel en `hooks/useCoachConversation.ts` por aumento de estado bidireccional; actualizar estándar a presentación MVVM para chat con excepción de ADR-001/002 mantenida en páginas estáticas. Capas web: dominio `lib/chat` y cálculos puros; aplicación `lib/chat/application`; infraestructura `lib/infra`; presentación `app`, `components`, `hooks`. Dominio no importa infraestructura. La aprobación del ADR autoriza materialización de estándares por coordinator, no edición de memoria por implementer.
