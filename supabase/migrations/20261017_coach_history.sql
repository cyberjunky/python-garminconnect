-- SPEC-002: Backend de historial privado, auth RLS y modelo exclusivo (I-SERVER)
-- Migración aditiva para conversaciones privadas, mensajes, operaciones idempotentes,
-- registro de importaciones conservadoras y vinculo de perfiles de salud.

-- 1. Tabla de conversaciones
create table if not exists public.coach_conversations (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    title text not null default 'Nueva conversación',
    revision integer not null default 1 check (revision >= 1),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint coach_conversations_id_owner_key unique (id, owner_id)
);

-- 2. Tabla de mensajes de conversación
create table if not exists public.coach_messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null,
    owner_id uuid not null references auth.users(id) on delete cascade,
    sequence integer not null check (sequence >= 1),
    role text not null check (role in ('user', 'assistant', 'system')),
    content text not null check (char_length(content) <= 4000),
    created_at timestamptz not null default now(),
    constraint coach_messages_conv_owner_fkey
        foreign key (conversation_id, owner_id)
        references public.coach_conversations(id, owner_id)
        on delete cascade,
    constraint coach_messages_conv_seq_key
        unique (conversation_id, sequence)
);

-- 3. Tabla de operaciones idempotentes con lease de concurrencia
create table if not exists public.coach_operations (
    owner_id uuid not null references auth.users(id) on delete cascade,
    operation_id uuid not null,
    conversation_id uuid not null,
    status text not null check (status in ('in_progress', 'completed', 'failed')),
    result_message_id uuid,
    lease_until timestamptz not null,
    created_at timestamptz not null default now(),
    primary key (owner_id, operation_id),
    constraint coach_operations_conv_owner_fkey
        foreign key (conversation_id, owner_id)
        references public.coach_conversations(id, owner_id)
        on delete cascade
);

-- 4. Tabla de importaciones conservadoras por snapshot y digest
create table if not exists public.coach_imports (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    source_id text not null,
    source_digest text not null,
    conversation_id uuid not null,
    status text not null check (status in ('imported', 'skipped', 'failed')),
    created_at timestamptz not null default now(),
    constraint coach_imports_conv_owner_fkey
        foreign key (conversation_id, owner_id)
        references public.coach_conversations(id, owner_id)
        on delete cascade,
    constraint coach_imports_owner_source_digest_key
        unique (owner_id, source_id, source_digest)
);

-- 5. Tabla de vinculo de salud MVP por propietario autenticado
create table if not exists public.coach_profile_links (
    auth_user_id uuid primary key references auth.users(id) on delete cascade,
    profile_id uuid not null,
    created_at timestamptz not null default now()
);

-- 6. Indices de rendimiento para consultas comunes
create index if not exists idx_coach_conversations_owner_updated
    on public.coach_conversations (owner_id, updated_at desc);

create index if not exists idx_coach_messages_conv_seq
    on public.coach_messages (conversation_id, sequence asc);

create index if not exists idx_coach_operations_owner_lease
    on public.coach_operations (owner_id, lease_until);

-- 7. Trigger para actualizacion automatica de updated_at en conversaciones
create or replace function public.touch_coach_conversation_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_coach_conversations_updated_at on public.coach_conversations;
create trigger trg_coach_conversations_updated_at
    before update on public.coach_conversations
    for each row
    execute function public.touch_coach_conversation_updated_at();

-- 8. Habilitacion estricta de Row Level Security (RLS) en todas las tablas
alter table public.coach_conversations enable row level security;
alter table public.coach_messages enable row level security;
alter table public.coach_operations enable row level security;
alter table public.coach_imports enable row level security;
alter table public.coach_profile_links enable row level security;

-- Politicas RLS para coach_conversations
create policy "coach_conversations_select_owner" on public.coach_conversations
    for select to authenticated using (auth.uid() = owner_id);

create policy "coach_conversations_insert_owner" on public.coach_conversations
    for insert to authenticated with check (auth.uid() = owner_id);

create policy "coach_conversations_update_owner" on public.coach_conversations
    for update to authenticated using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

create policy "coach_conversations_delete_owner" on public.coach_conversations
    for delete to authenticated using (auth.uid() = owner_id);

-- Politicas RLS para coach_messages
create policy "coach_messages_select_owner" on public.coach_messages
    for select to authenticated using (auth.uid() = owner_id);

create policy "coach_messages_insert_owner" on public.coach_messages
    for insert to authenticated with check (auth.uid() = owner_id);

create policy "coach_messages_update_owner" on public.coach_messages
    for update to authenticated using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

create policy "coach_messages_delete_owner" on public.coach_messages
    for delete to authenticated using (auth.uid() = owner_id);

-- Politicas RLS para coach_operations
create policy "coach_operations_select_owner" on public.coach_operations
    for select to authenticated using (auth.uid() = owner_id);

create policy "coach_operations_insert_owner" on public.coach_operations
    for insert to authenticated with check (auth.uid() = owner_id);

create policy "coach_operations_update_owner" on public.coach_operations
    for update to authenticated using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

create policy "coach_operations_delete_owner" on public.coach_operations
    for delete to authenticated using (auth.uid() = owner_id);

-- Politicas RLS para coach_imports
create policy "coach_imports_select_owner" on public.coach_imports
    for select to authenticated using (auth.uid() = owner_id);

create policy "coach_imports_insert_owner" on public.coach_imports
    for insert to authenticated with check (auth.uid() = owner_id);

create policy "coach_imports_update_owner" on public.coach_imports
    for update to authenticated using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

create policy "coach_imports_delete_owner" on public.coach_imports
    for delete to authenticated using (auth.uid() = owner_id);

-- Politicas RLS para coach_profile_links (solo lectura para el propio usuario, administrado fuera)
create policy "coach_profile_links_select_owner" on public.coach_profile_links
    for select to authenticated using (auth.uid() = auth_user_id);

-- Politicas para service_role (acceso de administracion / scripts autorizados)
create policy "service_role_coach_conversations" on public.coach_conversations
    for all to service_role using (true) with check (true);

create policy "service_role_coach_messages" on public.coach_messages
    for all to service_role using (true) with check (true);

create policy "service_role_coach_operations" on public.coach_operations
    for all to service_role using (true) with check (true);

create policy "service_role_coach_imports" on public.coach_imports
    for all to service_role using (true) with check (true);

create policy "service_role_coach_profile_links" on public.coach_profile_links
    for all to service_role using (true) with check (true);

-- 9. Asignacion estricta de permisos: anon sin acceso, authenticated restringido por RLS
revoke all on public.coach_conversations from anon;
revoke all on public.coach_messages from anon;
revoke all on public.coach_operations from anon;
revoke all on public.coach_imports from anon;
revoke all on public.coach_profile_links from anon;

grant select, insert, update, delete on public.coach_conversations to authenticated;
grant select, insert, update, delete on public.coach_messages to authenticated;
grant select, insert, update, delete on public.coach_operations to authenticated;
grant select, insert, update, delete on public.coach_imports to authenticated;
grant select on public.coach_profile_links to authenticated;

grant all on public.coach_conversations to service_role;
grant all on public.coach_messages to service_role;
grant all on public.coach_operations to service_role;
grant all on public.coach_imports to service_role;
grant all on public.coach_profile_links to service_role;
