---
schema_version: 1
project_id: python-garminconnect
layer: immediate
last_updated: '2026-10-20T19:35:21Z'
source: ies bye
---

# Handoff

Ultima sesion: S-20260727-001 (cerrada 2026-10-20T19:35:21Z).

## Para reanudar

```bash
ies init          # abre nueva sesion y muestra status
ies status        # revisa bloqueos y siguiente accion
ies prompt <rol> --task T-0019   # continua la task activa
```

Task sugerida al reanudar: T-0019

## Trabajo pendiente propuesto

Followups declarados por los agentes en sus entregas. No son tasks: el humano decide cuales crear con `ies task add` (en SDD, tras reabrir o crear la spec).

- [T-0002] T-0003
- [T-0003] T-0004
- [T-0004] T-0005
- [T-0006] T-0007
- [T-0009] Saneamiento de linter y CI hygiene: corregir UP017, SIM102, SIM105 y S110 en adaptadores de SPEC-001, registrar advertencias de autenticación en garmin_auth.py y actualizar per-file-ignores o resolver deuda técnica preexistente en scripts/coaching/services/mcp.
- [T-0012] {'id': 'T-0013', 'title': 'Accesibilidad P2, copy en español, consistencia UI y marca Tri-Coach P3'}
- [T-0012] {'id': 'T-0014', 'title': 'Verificación viewer independiente de UX/UI P1-P3 (Local 1280x800 y 375x812)'}
- [T-0013] {'id': 'T-0014', 'title': 'Verificación viewer independiente de UX/UI P1-P3 (Local 1280x800 y 375x812)'}
- [T-0013] {'id': 'T-0015', 'title': 'Saneamiento linter SPEC-001, observabilidad REQ-005, deploy script y privacidad de logs CI'}
- [T-0014] {'id': 'T-0015', 'title': 'Saneamiento linter SPEC-001, observabilidad REQ-005, deploy script y privacidad de logs CI'}
- [T-0014] {'id': 'T-0011', 'title': 'Estrategia y resolución de 97 errores de linter heredados de master'}
- [T-0016] {'id': 'T-0014', 'title': 'Verificación viewer independiente de UX/UI P1-P3 (Local 1280x800 y 375x812)'}
- [T-0016] {'id': 'T-0015', 'title': 'Saneamiento linter SPEC-001, observabilidad REQ-005, deploy script y privacidad de logs CI'}
- [T-0018] {'id': 'T-0017-FIX', 'title': 'Ronda correctiva consolidada de T-0017 (saneamiento ruff, resiliencia/observabilidad de tokens, tests web y entregable)'}
- [T-0025] V-UI (destino: viewer, origen: implementer): Revision independiente de la entrega T-0025 y reproduccion focalizada de la matriz S en Safari sobre el SHA de task/T-0025, tras autorizacion humana G3.
- [T-0025] I-SERVER (destino: implementer, origen: implementer): Implementar autenticacion, repositorio privado en Supabase con RLS, modelo exclusivo gpt-6-luna high y version 0.4.0-rc.2 una vez superados G3 y G4 de I-UI.
- [T-0026] G4 Aceptación e integración humana (origen: viewer, destino: coordinator): Presentar veredicto APROBAR al humano para autorizar merge de task/T-0025 (commit 2dcd4eed848e8e9806c846b6928896940fa21401) en master.
- [T-0026] I-SERVER T-0027 (origen: coordinator, destino: implementer): Despachar etapa de backend (Supabase Auth, RLS privado, endpoint de chat con GPT-6 Luna High exclusivo y SemVer 0.4.0-rc.2) tras consolidación de G4.
- [T-0027] V-SERVER (destino: viewer, origen: implementer): Auditoria y verificacion viewer independiente de la entrega T-0027 sobre la rama task/T-0027 tras autorizacion humana G3.
- [T-0027] I-CLIENT T-0028 (destino: implementer, origen: coordinator): Implementacion del frontend de chat (ViewModel, persistencia cliente, migracion local->cloud y selector UI) con version 0.4.0.
- [T-0028] I-CLIENT (destino: implementer): Implementación de UI/ViewModel de chat y migración opt-in desde localStorage (SPEC-002 §4 / PLAN-002).
- [T-0028] T-0020 (destino: implementer): Incorporación de comando de máquina para Clean Architecture en .ies/gate.yaml (import-linter y dependency-cruiser).
- [T-0029] V-INTEGRAL (destino: viewer, origen: implementer): Auditoría y verificación viewer independiente de la entrega T-0029 sobre la rama task/T-0029 tras autorización humana G3.
- [T-0029] G4 / G5 / G7 (destino: human, origen: coordinator): Aprobación humana de merge, aplicación de migración en Supabase cloud, configuración de OTP por invitación y release a producción en Vercel.
- [T-0030] G4 / G5 / G7 (destino: human, origen: coordinator): Aprobación humana de merge, aplicación de migración en Supabase cloud, configuración de OTP por invitación y release a producción en Vercel.
- [T-0031] {'T-0032 (I-DOMAIN-RETOS)': 'Implementar motor de recomendaciones accionables y tarjeta Macrociclo en 4 bloques en apps/web/lib/ y /retos con tests P01-P12.'}
- [T-0031] {'T-0033 (I-TENDENCIA-NAV)': 'Implementar ruta /tendencia, navegación en DashboardNav, agregación mensual en lib/tendencia.ts y contenedor ADR-003 con tests P13-P19.'}
- [T-0031] {'T-0034 (I-RELEASE-050)': 'Bump de versión a 0.5.0 MINOR en grupo serial R (package.json, lock, version.test.mjs, README, CHANGELOG).'}
- [T-0031] {'T-0035 (V-INTEGRAL-050)': 'Auditoría independiente, verificación integral de los 20 requisitos EARS, QA Safari/móvil y veredicto formal.'}
- [T-0036] T-0037 (I-PATCH-051): Implementar correcciones de desborde de métricas, jerarquía compacta de CoachChat, sincronización de historial y bump SemVer 0.5.1 en Grupo R con tests P01-P09.
- [T-0036] T-0038 (V-VIEWER-051): Auditoría independiente, verificación integral de los 9 requisitos EARS, QA de geometría y veredicto formal.
- [T-0039] T-0040

## Cobertura SDLC pendiente

Bloques declarados `parcial` o `no-aplica` en entregas cerradas (ADR-011); el humano decide si generan followups.

- [T-0028] release: no-aplica
- [T-0028] despliegue: no-aplica
- [T-0030] release: no-aplica
- [T-0030] despliegue: no-aplica
- [T-0031] implementacion: no-aplica
- [T-0031] release: no-aplica
- [T-0031] despliegue: no-aplica
- [T-0032] release: no-aplica
- [T-0033] release: no-aplica
- [T-0035] pruebas: no-aplica
- [T-0035] release: no-aplica
- [T-0035] despliegue: no-aplica
- [T-0036] implementacion: no-aplica
- [T-0036] release: no-aplica
- [T-0036] despliegue: no-aplica
- [T-0039] diseno: no-aplica
- [T-0039] despliegue: no-aplica

