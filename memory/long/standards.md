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
patron_arquitectonico: layered   # mvvm | clean-architecture | hexagonal | layered | n/a
tiene_ui: si                 # si | no  (si -> patron_arquitectonico debe ser mvvm, o ADR que lo justifique)
```

Declarala antes de la primera task implementer. Cambiarla exige ADR en
`memory/long/adr/`.

## 2. Clean Code (obligatorio, Articulo VII.1)

- Nombres intencionales; funciones pequenas de una responsabilidad.
- Sin duplicacion, sin codigo muerto, sin comentarios que sustituyan claridad.
- (anade aqui reglas propias del proyecto)

## 3. Convenciones de lenguaje y herramientas

- Lenguaje(s) y version:
- Formateador / linter:
- Estructura de modulos:

## 4. Tests

- Framework y comando canonico:
- Cobertura minima / criterios por REQ:
