# Tri-Coach Web (Phase 2)

Read-only Next.js dashboard for Supabase coaching data.

## Setup

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

## Deploy (Vercel)

Set environment variables:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

No Garmin credentials on Vercel — data comes from Supabase only.

## Versión y cambios

- **Versión actual**: `0.4.0-rc.1`
- **Regla SemVer**: Este proyecto sigue versionado semántico ([SemVer](https://semver.org/lang/es/)) unificado para todo el ecosistema Tri-Coach (aplicación web, recolector Python, workflows de GitHub Actions y esquema Supabase). La versión se incrementa en **MINOR** (0.x.0) para Pull Requests con nuevas funcionalidades o módulos, y en **PATCH** (0.x.y) para correcciones y parches.
- **Historial de cambios**: Consulta [CHANGELOG.md](./CHANGELOG.md) para el detalle de cambios por versión.
