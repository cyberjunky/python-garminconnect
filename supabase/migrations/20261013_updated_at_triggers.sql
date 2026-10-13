-- Idempotent triggers to automatically maintain updated_at = now() on tables with upsert operations.
-- Can be executed safely in Supabase SQL Editor.

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- 1. daily_snapshots
drop trigger if exists trigger_set_updated_at on public.daily_snapshots;
create trigger trigger_set_updated_at
before update on public.daily_snapshots
for each row execute function public.set_updated_at();

-- 2. readiness_daily
drop trigger if exists trigger_set_updated_at on public.readiness_daily;
create trigger trigger_set_updated_at
before update on public.readiness_daily
for each row execute function public.set_updated_at();

-- 3. training_load
drop trigger if exists trigger_set_updated_at on public.training_load;
create trigger trigger_set_updated_at
before update on public.training_load
for each row execute function public.set_updated_at();

-- 4. session_log
drop trigger if exists trigger_set_updated_at on public.session_log;
create trigger trigger_set_updated_at
before update on public.session_log
for each row execute function public.set_updated_at();

-- 5. weekly_sport_load
drop trigger if exists trigger_set_updated_at on public.weekly_sport_load;
create trigger trigger_set_updated_at
before update on public.weekly_sport_load
for each row execute function public.set_updated_at();

-- 6. garmin_tokens
drop trigger if exists trigger_set_updated_at on public.garmin_tokens;
create trigger trigger_set_updated_at
before update on public.garmin_tokens
for each row execute function public.set_updated_at();
