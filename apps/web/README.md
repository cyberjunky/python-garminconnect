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
