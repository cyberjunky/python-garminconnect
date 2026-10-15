---
schema_version: 1
project_id: python-garminconnect
layer: long
last_updated: '2026-10-14T13:20:10Z'
source: ies update (migracion ADR-010)
confidence: n/a
---

# Standards del proyecto python-garminconnect

Normas de codigo y arquitectura. Complementa la constitucion (Articulo VII);
`ies constitution check` lee el bloque YAML de la seccion 1.

## 1. Declaracion arquitectonica

```yaml
patron_arquitectonico: clean-architecture   # clean-architecture | n/a
tiene_ui: si                                # si | no  (apps/web, Next.js)
patron_presentacion: n/a                    # mvvm | n/a  (Server Components; justificado en ADR-001 y ADR-002)
capas:
  dominio: garmin_coaching                  # reglas de entrenamiento; solo stdlib y el propio paquete
  aplicacion: services/collector/main.py    # orquestacion FastAPI del recolector
  infraestructura: garminconnect, garmin_auth.py, services/collector/supabase_client.py   # clientes Garmin y Supabase
  web-dominio: apps/web/lib                 # calculos y modelos del dashboard
  web-presentacion: apps/web/app, apps/web/components
```

Declarada el 2026-10-14 (DEC-006, ADR-001 patron layered); reformulada bajo ADR-018 del framework
con `memory/long/adr/ADR-002-clean-architecture-regla-de-dependencia.md`.
Cambiarla exige ADR en `memory/long/adr/`.

## 2. Regla de dependencia (Articulo VII.2)

- El dominio no importa frameworks, UI, base de datos ni clientes de red.
- Los casos de uso dependen del dominio y de interfaces; nunca de adaptadores
  concretos.
- Direccion Python: `services/collector` -> `garmin_coaching` <- nada.
  `garmin_coaching` no importa `garminconnect`, `supabase`, `fastapi` ni
  `requests` (hoy ya se cumple: solo stdlib).
- Direccion web: `app/` y `components/` -> `lib/`. `lib/supabase.ts` y
  `lib/openaiModels.ts` son infraestructura dentro de `lib/`; se mueven a
  `lib/infra/` cuando se toquen y ningun calculo de `lib/` los importa.
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
