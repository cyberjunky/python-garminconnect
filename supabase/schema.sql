-- Fitness Coaching MVP schema (single-user MVP; service role from worker)

create extension if not exists "pgcrypto";

-- Fixed MVP user id (replace in phase 2 with auth.users)
-- Diego single-user: 00000000-0000-0000-0000-000000000001

create table if not exists public.users (
    id uuid primary key default '00000000-0000-0000-0000-000000000001'::uuid,
    name text not null default 'Diego',
    timezone text not null default 'America/Bogota',
    created_at timestamptz not null default now()
);

insert into public.users (id, name) values ('00000000-0000-0000-0000-000000000001', 'Diego')
on conflict (id) do nothing;

create table if not exists public.event_milestones (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    code text not null,
    name text not null,
    event_date date not null,
    notes text,
    created_at timestamptz not null default now(),
    unique (user_id, code)
);

create table if not exists public.macrocycle_phases (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    code text not null,
    name text not null,
    start_date date not null,
    end_date date not null,
    focus text,
    sport text,
    hr_cap int,
    max_duration_min int,
    created_at timestamptz not null default now(),
    unique (user_id, code)
);

create table if not exists public.daily_snapshots (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    snapshot_date date not null,
    payload jsonb not null,
    health_score numeric,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, snapshot_date)
);

create table if not exists public.readiness_daily (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    readiness_date date not null,
    zone text not null,
    score_ok int,
    sleep_h numeric,
    sleep_score numeric,
    hrv numeric,
    stress numeric,
    bb_change numeric,
    hrv_status text,
    thresholds jsonb,
    recommendation text,
    payload jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, readiness_date)
);

create table if not exists public.training_load (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    load_date date not null,
    status_phrase text,
    acwr numeric,
    vo2max numeric,
    lthr jsonb,
    payload jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, load_date)
);

create table if not exists public.coaching_messages (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    message_date date not null,
    channel text not null default 'whatsapp',
    body text not null,
    session jsonb,
    guard_flags text[],
    sent_at timestamptz,
    reply text,
    reply_at timestamptz,
    created_at timestamptz not null default now()
);

create table if not exists public.session_log (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    session_date date not null,
    planned jsonb,
    executed jsonb,
    confirmed boolean default false,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, session_date)
);

create table if not exists public.weekly_sport_load (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    week_start date not null,
    block_index int,
    week_in_block int,
    kind text,
    phase_code text,
    planned_run_min numeric,
    planned_bike_min numeric,
    planned_swim_min numeric,
    planned_walk_min numeric,
    planned_total_min numeric,
    executed_run_min numeric,
    executed_bike_min numeric,
    executed_swim_min numeric,
    executed_walk_min numeric,
    executed_other_min numeric,
    executed_total_min numeric,
    payload jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, week_start)
);

create index if not exists idx_weekly_sport_load_week on public.weekly_sport_load (user_id, week_start desc);

create index if not exists idx_daily_snapshots_date on public.daily_snapshots (user_id, snapshot_date desc);
create index if not exists idx_readiness_daily_date on public.readiness_daily (user_id, readiness_date desc);
create index if not exists idx_coaching_messages_date on public.coaching_messages (user_id, message_date desc);

-- RLS (MVP: service role bypasses; anon read in phase 2)
alter table public.daily_snapshots enable row level security;
alter table public.readiness_daily enable row level security;
alter table public.training_load enable row level security;
alter table public.coaching_messages enable row level security;
alter table public.session_log enable row level security;
alter table public.event_milestones enable row level security;
alter table public.macrocycle_phases enable row level security;
alter table public.weekly_sport_load enable row level security;

create policy "service_role_all" on public.daily_snapshots for all using (true) with check (true);
create policy "service_role_all" on public.readiness_daily for all using (true) with check (true);
create policy "service_role_all" on public.training_load for all using (true) with check (true);
create policy "service_role_all" on public.coaching_messages for all using (true) with check (true);
create policy "service_role_all" on public.session_log for all using (true) with check (true);
create policy "service_role_all" on public.event_milestones for all using (true) with check (true);
create policy "service_role_all" on public.macrocycle_phases for all using (true) with check (true);
create policy "service_role_all" on public.weekly_sport_load for all using (true) with check (true);

create table if not exists public.garmin_tokens (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    token_data jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id)
);

alter table public.garmin_tokens enable row level security;
create policy "service_role_all" on public.garmin_tokens for all to service_role using (true) with check (true);
revoke all on public.garmin_tokens from anon, authenticated;
grant all on public.garmin_tokens to service_role;

-- updated_at auto-update triggers
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trigger_set_updated_at on public.daily_snapshots;
create trigger trigger_set_updated_at
before update on public.daily_snapshots
for each row execute function public.set_updated_at();

drop trigger if exists trigger_set_updated_at on public.readiness_daily;
create trigger trigger_set_updated_at
before update on public.readiness_daily
for each row execute function public.set_updated_at();

drop trigger if exists trigger_set_updated_at on public.training_load;
create trigger trigger_set_updated_at
before update on public.training_load
for each row execute function public.set_updated_at();

drop trigger if exists trigger_set_updated_at on public.session_log;
create trigger trigger_set_updated_at
before update on public.session_log
for each row execute function public.set_updated_at();

drop trigger if exists trigger_set_updated_at on public.weekly_sport_load;
create trigger trigger_set_updated_at
before update on public.weekly_sport_load
for each row execute function public.set_updated_at();

drop trigger if exists trigger_set_updated_at on public.garmin_tokens;
create trigger trigger_set_updated_at
before update on public.garmin_tokens
for each row execute function public.set_updated_at();

