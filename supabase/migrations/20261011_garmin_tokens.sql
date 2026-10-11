-- Store Garmin OAuth/DI tokens securely in Supabase with RLS restricted to service_role.

create table if not exists public.garmin_tokens (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    token_data jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id)
);

alter table public.garmin_tokens enable row level security;

create policy "service_role_all" on public.garmin_tokens
    for all to service_role using (true) with check (true);

revoke all on public.garmin_tokens from anon, authenticated;
grant all on public.garmin_tokens to service_role;
