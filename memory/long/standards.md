---
schema_version: 1
project_id: python-garminconnect
layer: long
last_updated: '2026-10-17T12:16:50Z'
source: coordinator T-0024, DEC-009, ADR-004
confidence: n/a
---

# Standards del proyecto python-garminconnect

Normas de codigo y arquitectura. Complementa la constitucion (Articulo VII);
`ies constitution check` lee el bloque YAML de la seccion 1.

## 1. Declaracion arquitectonica

```yaml
patron_arquitectonico: clean-architecture   # clean-architecture | n/a
tiene_ui: si                                # si | no  (apps/web, Next.js)
patron_presentacion: mvvm                   # chat interactivo; excepcion paginas estaticas ADR-001/002/004
capas:
  dominio: garmin_coaching                  # reglas de entrenamiento; solo stdlib y el propio paquete
  aplicacion: services/collector/main.py    # orquestacion FastAPI del recolector
  infraestructura: garminconnect, garmin_auth.py, services/collector/supabase_client.py   # clientes Garmin y Supabase
  web-dominio: apps/web/lib/chat, calculos puros de apps/web/lib
  web-aplicacion: apps/web/lib/chat/application
  web-infraestructura: apps/web/lib/infra
  web-presentacion: apps/web/app, apps/web/components, apps/web/hooks
```

Declarada el 2026-10-14 (DEC-006, ADR-001 patron layered); reformulada bajo ADR-018 del framework
con `memory/long/adr/ADR-002-clean-architecture-regla-de-dependencia.md`.
Actualizada en DEC-009/ADR-004 para el chat de SPEC-002: MVVM con
`hooks/useCoachConversation.ts`; la excepcion de paginas estaticas se conserva.
Es un estandar objetivo aprobado, no evidencia de implementacion completada.
Cambiarla exige ADR en `memory/long/adr/`.

## 2. Regla de dependencia (Articulo VII.2)

- El dominio no importa frameworks, UI, base de datos ni clientes de red.
- Los casos de uso dependen del dominio y de interfaces; nunca de adaptadores
  concretos.
- Direccion Python: `services/collector` -> `garmin_coaching` <- nada.
  `garmin_coaching` no importa `garminconnect`, `supabase`, `fastapi` ni
  `requests` (hoy ya se cumple: solo stdlib).
- Direccion web: Views -> ViewModel/casos de uso -> dominio/puertos;
  infraestructura implementa puertos. API routes componen dependencias.
  `lib/chat/application` depende del dominio y de interfaces; no de adaptadores.
  `lib/supabase.ts` y `lib/openaiModels.ts` se mueven a `lib/infra/` al tocarlos;
  ningun calculo puro los importa. No se mantiene un shim con dependencia inversa.
  Consultas de `condition.ts` pasan a infraestructura, conservando calculos puros.
  El corte de imports en dashboard/mesocycle se limita al aprobado en PLAN-002.
- El codigo heredado no se migra para cumplir; solo el codigo nuevo o tocado
  cruza el gate.

## 3. Clean Code (Articulo VII.1)

- Nombres intencionales; funciones pequenas de una responsabilidad.
- Sin duplicacion, sin codigo muerto, sin comentarios que sustituyan claridad.
- (anade aqui reglas propias del proyecto)

## 4. Convenciones de lenguaje y herramientas

- Lenguaje(s) y version:
- Formateador / linter:
- Estructura de modulos:

## 5. Tests

- Framework y comando canonico:
- Cobertura minima / criterios por REQ:
