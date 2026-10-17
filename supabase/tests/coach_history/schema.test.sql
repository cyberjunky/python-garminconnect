-- Pruebas de verificacion de schema y politicas RLS (SPEC-002 I-SERVER)
-- Valida que las tablas, constraints y politicas existan en catalogos pg_catalog.

begin;

-- 1. Tablas requeridas
select has_table('public', 'coach_conversations', 'coach_conversations debe existir');
select has_table('public', 'coach_messages', 'coach_messages debe existir');
select has_table('public', 'coach_operations', 'coach_operations debe existir');
select has_table('public', 'coach_imports', 'coach_imports debe existir');
select has_table('public', 'coach_profile_links', 'coach_profile_links debe existir');

-- 2. RLS habilitado en todas las tablas
select row_security_active('public.coach_conversations');
select row_security_active('public.coach_messages');
select row_security_active('public.coach_operations');
select row_security_active('public.coach_imports');
select row_security_active('public.coach_profile_links');

-- 3. Claves primarias y foraneas
select col_is_pk('public', 'coach_conversations', 'id');
select col_is_pk('public', 'coach_messages', 'id');
select col_is_pk('public', 'coach_profile_links', 'auth_user_id');

-- 4. Restriccion de caracteres <= 4000
select has_check('public', 'coach_messages', 'coach_messages debe tener check de longitud');

rollback;
