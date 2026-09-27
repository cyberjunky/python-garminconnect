"""Small, dependency-free localization support for the demo interface.

The catalog deliberately lives outside ``demo.py`` so adding another language
does not require copying or branching the demo program.  The library API and
Garmin protocol values are not part of this catalog.
"""

from __future__ import annotations

import os
from typing import Any


class UnsupportedLanguageError(ValueError):
    """Raised when a requested interface language is not supported."""


# Source text is kept in English.  Entries without a Portuguese translation
# intentionally fall back to English, which makes partial future catalogs safe.
_MESSAGES: dict[str, tuple[str, str | None]] = {
    # Menu categories and option descriptions.
    "menu.user_profile": ("👤 User & Profile", "👤 Usuário e Perfil"),
    "menu.daily_health": ("📊 Daily Health & Activity", "📊 Saúde e Atividade Diárias"),
    "menu.advanced_health": (
        "🔬 Advanced Health Metrics",
        "🔬 Métricas Avançadas de Saúde",
    ),
    "menu.historical": (
        "📈 Historical Data & Trends",
        "📈 Dados Históricos e Tendências",
    ),
    "menu.activities": ("🏃 Activities & Workouts", "🏃 Atividades e Treinos"),
    "menu.body_composition_category": (
        "⚖️  Body Composition & Weight",
        "⚖️  Composição Corporal e Peso",
    ),
    "menu.goals": ("🏆 Goals & Achievements", "🏆 Metas e Conquistas"),
    "menu.device": ("⌚ Device & Technical", "⌚ Dispositivo e Informações Técnicas"),
    "menu.gear": ("🎽 Gear & Equipment", "🎽 Equipamento e Acessórios"),
    "menu.hydration_category": ("💧 Hydration & Wellness", "💧 Hidratação e Bem-estar"),
    "menu.system": ("🔧 System & Export", "🔧 Sistema e Exportação"),
    "menu.training_plans_category": ("📅 Training Plans", "📅 Planos de Treino"),
    "menu.golf": ("⛳ Golf", "⛳ Golfe"),
    "menu.editing": ("✏️  Activity Editing", "✏️  Edição de Atividades"),
    "menu.get_full_name": ("Get full name", "Obter nome completo"),
    "menu.get_unit_system": ("Get unit system", "Obter sistema de unidades"),
    "menu.get_user_profile": ("Get user profile", "Obter perfil do usuário"),
    "menu.get_userprofile_settings": (
        "Get userprofile settings",
        "Obter configurações do perfil do usuário",
    ),
    "menu.activity_data": (
        "Get activity data for '{date}'",
        "Obter dados de atividade de '{date}'",
    ),
    "menu.user_summary": (
        "Get user summary for '{date}'",
        "Obter resumo do usuário de '{date}'",
    ),
    "menu.stats_body": (
        "Get stats and body composition for '{date}'",
        "Obter estatísticas e composição corporal de '{date}'",
    ),
    "menu.steps_data": (
        "Get steps data for '{date}'",
        "Obter dados de passos de '{date}'",
    ),
    "menu.heart_rate": (
        "Get heart rate data for '{date}'",
        "Obter dados de frequência cardíaca de '{date}'",
    ),
    "menu.resting_heart_rate": (
        "Get resting heart rate from '{start}' to '{end}'",
        "Obter frequência cardíaca de repouso de '{start}' a '{end}'",
    ),
    "menu.sleep_summaries": (
        "Get daily sleep summaries from '{start}' to '{end}'",
        "Obter resumos diários do sono de '{start}' a '{end}'",
    ),
    "menu.stress_data": (
        "Get stress data for '{date}'",
        "Obter dados de estresse de '{date}'",
    ),
    "menu.lifestyle": (
        "Get lifestyle logging data for '{date}'",
        "Obter dados de registro de estilo de vida de '{date}'",
    ),
    "menu.daily_calories": (
        "Get daily calories from '{start}' to '{end}'",
        "Obter calorias diárias de '{start}' a '{end}'",
    ),
    "menu.training_readiness": (
        "Get training readiness for '{date}'",
        "Obter prontidão para treino de '{date}'",
    ),
    "menu.morning_training_readiness": (
        "Get morning training readiness for '{date}'",
        "Obter prontidão matinal para treino de '{date}'",
    ),
    "menu.training_status": (
        "Get training status for '{date}'",
        "Obter status de treinamento de '{date}'",
    ),
    "menu.respiration": (
        "Get respiration data for '{date}'",
        "Obter dados de respiração de '{date}'",
    ),
    "menu.spo2": ("Get SpO2 data for '{date}'", "Obter dados de SpO2 de '{date}'"),
    "menu.max_metrics": (
        "Get max metrics (VO2, fitness age) from '{start}' to '{end}'",
        "Obter métricas máximas (VO2, idade fitness) de '{start}' a '{end}'",
    ),
    "menu.hrv": (
        "Get Heart Rate Variability (HRV) from '{start}' to '{end}'",
        "Obter Variabilidade da Frequência Cardíaca (VFC) de '{start}' a '{end}'",
    ),
    "menu.fitness_age": (
        "Get Fitness Age data for '{date}'",
        "Obter dados de idade fitness de '{date}'",
    ),
    "menu.lactate": ("Get lactate threshold data", "Obter dados de limiar de lactato"),
    "menu.intensity": (
        "Get intensity minutes for '{date}'",
        "Obter minutos de intensidade de '{date}'",
    ),
    "menu.running_tolerance": (
        "Get running tolerance from '{start}' to '{end}'",
        "Obter tolerância à corrida de '{start}' a '{end}'",
    ),
    "menu.heart_rate_zones": (
        "Get configured heart rate zones",
        "Obter zonas de frequência cardíaca configuradas",
    ),
    "menu.power_zones": (
        "Get configured power zones for all sports",
        "Obter zonas de potência configuradas para todos os esportes",
    ),
    "menu.cycling_power_zones": (
        "Get configured cycling power zones",
        "Obter zonas de potência de ciclismo configuradas",
    ),
    "menu.ftp_range": (
        "Get functional threshold power range from '{start}' to '{end}'",
        "Obter faixa de potência de limiar funcional de '{start}' a '{end}'",
    ),
    "menu.daily_steps": (
        "Get daily steps from '{start}' to '{end}'",
        "Obter passos diários de '{start}' a '{end}'",
    ),
    "menu.body_battery": (
        "Get body battery from '{start}' to '{end}'",
        "Obter Body Battery de '{start}' a '{end}'",
    ),
    "menu.floors": (
        "Get floors data for '{start}'",
        "Obter dados de andares de '{start}'",
    ),
    "menu.blood_pressure": (
        "Get blood pressure from '{start}' to '{end}'",
        "Obter pressão arterial de '{start}' a '{end}'",
    ),
    "menu.progress": (
        "Get progress summary from '{start}' to '{end}'",
        "Obter resumo do progresso de '{start}' a '{end}'",
    ),
    "menu.body_battery_events": (
        "Get body battery events for '{start}'",
        "Obter eventos do Body Battery de '{start}'",
    ),
    "menu.weekly_steps": (
        "Get weekly steps (52 weeks ending '{date}')",
        "Obter passos semanais (52 semanas até '{date}')",
    ),
    "menu.weekly_stress": (
        "Get weekly stress (52 weeks ending '{date}')",
        "Obter estresse semanal (52 semanas até '{date}')",
    ),
    "menu.weekly_intensity": (
        "Get weekly intensity minutes from '{start}' to '{end}'",
        "Obter minutos de intensidade semanais de '{start}' a '{end}'",
    ),
    "menu.recent_activities": (
        "Get recent activities (limit {limit})",
        "Obter atividades recentes (limite {limit})",
    ),
    "menu.last_activity": ("Get last activity", "Obter última atividade"),
    "menu.activities_today": (
        "Get activities for today '{date}'",
        "Obter atividades de hoje, '{date}'",
    ),
    "menu.download_activities": (
        "Download activities by date range '{start}' to '{end}'",
        "Baixar atividades do período de '{start}' a '{end}'",
    ),
    "menu.activity_types": (
        "Get all activity types and statistics",
        "Obter todos os tipos de atividade e estatísticas",
    ),
    "menu.upload_activity": (
        "Upload activity data from {file}",
        "Enviar dados de atividade de {file}",
    ),
    "menu.get_workouts": ("Get workouts", "Obter treinos"),
    "menu.activity_splits": (
        "Get activity splits (laps)",
        "Obter parciais da atividade (voltas)",
    ),
    "menu.typed_splits": (
        "Get activity typed splits",
        "Obter parciais categorizadas da atividade",
    ),
    "menu.split_summaries": (
        "Get activity split summaries",
        "Obter resumos das parciais da atividade",
    ),
    "menu.activity_weather": (
        "Get activity weather data",
        "Obter dados meteorológicos da atividade",
    ),
    "menu.activity_hr_zones": (
        "Get activity heart rate zones",
        "Obter zonas de frequência cardíaca da atividade",
    ),
    "menu.activity_power_zones": (
        "Get activity power zones",
        "Obter zonas de potência da atividade",
    ),
    "menu.cycling_ftp": (
        "Get cycling FTP (Functional Threshold Power)",
        "Obter FTP de ciclismo (Potência de Limiar Funcional)",
    ),
    "menu.activity_details": (
        "Get detailed activity information",
        "Obter informações detalhadas da atividade",
    ),
    "menu.activity_gear": (
        "Get activity gear information",
        "Obter informações do equipamento da atividade",
    ),
    "menu.single_activity": (
        "Get single activity data",
        "Obter dados de uma atividade",
    ),
    "menu.strength_sets": (
        "Get strength training exercise sets",
        "Obter séries de exercícios de treino de força",
    ),
    "menu.workout_by_id": ("Get workout by ID", "Obter treino pelo ID"),
    "menu.download_fit": (
        "Download workout to .FIT file",
        "Baixar treino para arquivo .FIT",
    ),
    "menu.upload_workout": ("Upload workout from {file}", "Enviar treino de {file}"),
    "menu.activities_by_date": (
        "Get activities by date range '{date}'",
        "Obter atividades pelo período de '{date}'",
    ),
    "menu.set_activity_name": ("Set activity name", "Definir nome da atividade"),
    "menu.set_activity_type": ("Set activity type", "Definir tipo da atividade"),
    "menu.manual_activity": ("Create manual activity", "Criar atividade manual"),
    "menu.delete_activity": ("Delete activity", "Excluir atividade"),
    "menu.count_activities": (
        "Count activities for current user",
        "Contar atividades do usuário atual",
    ),
    "menu.schedule_workout": (
        "Schedule a workout on a date (interactive)",
        "Agendar um treino para uma data (interativo)",
    ),
    "menu.import_activity": (
        "Import activity (no Strava re-export) from {file}",
        "Importar atividade (sem reexportação para o Strava) de {file}",
    ),
    "menu.scheduled_workouts": (
        "Get scheduled workouts by year and month",
        "Obter treinos agendados por ano e mês",
    ),
    "menu.typed_running": (
        "Upload typed running workout (sample)",
        "Enviar treino de corrida tipado (exemplo)",
    ),
    "menu.typed_cycling": (
        "Upload typed cycling workout (sample)",
        "Enviar treino de ciclismo tipado (exemplo)",
    ),
    "menu.typed_swimming": (
        "Upload typed swimming workout (sample)",
        "Enviar treino de natação tipado (exemplo)",
    ),
    "menu.typed_walking": (
        "Upload typed walking workout (sample)",
        "Enviar treino de caminhada tipado (exemplo)",
    ),
    "menu.typed_hiking": (
        "Upload typed hiking workout (sample)",
        "Enviar treino de trilha tipado (exemplo)",
    ),
    "menu.filtered_activities": (
        "Get activities filtered by type/subtype (interactive)",
        "Obter atividades filtradas por tipo/subtipo (interativo)",
    ),
    "menu.next_workout": (
        "Get the earliest upcoming scheduled workout (today or later)",
        "Obter o próximo treino agendado (hoje ou depois)",
    ),
    "menu.body_composition": (
        "Get body composition for '{date}'",
        "Obter composição corporal de '{date}'",
    ),
    "menu.weigh_ins": (
        "Get weigh-ins from '{start}' to '{end}'",
        "Obter pesagens de '{start}' a '{end}'",
    ),
    "menu.daily_weigh_ins": (
        "Get daily weigh-ins for '{date}'",
        "Obter pesagens diárias de '{date}'",
    ),
    "menu.add_weigh_in": (
        "Add a weigh-in (interactive)",
        "Adicionar uma pesagem (interativo)",
    ),
    "menu.add_body_composition": (
        "Add body composition for '{date}' (interactive)",
        "Adicionar composição corporal de '{date}' (interativo)",
    ),
    "menu.delete_weigh_ins": (
        "Delete all weigh-ins for '{date}'",
        "Excluir todas as pesagens de '{date}'",
    ),
    "menu.delete_weigh_in": (
        "Delete specific weigh-in",
        "Excluir uma pesagem específica",
    ),
    "menu.personal_records": (
        "Get personal records (decodes running typeId, interactive)",
        "Obter recordes pessoais (decodifica typeId de corrida, interativo)",
    ),
    "menu.earned_badges": ("Get earned badges", "Obter medalhas conquistadas"),
    "menu.adhoc_challenges": ("Get adhoc challenges", "Obter desafios avulsos"),
    "menu.available_badge_challenges": (
        "Get available badge challenges",
        "Obter desafios de medalhas disponíveis",
    ),
    "menu.active_goals": ("Get active goals", "Obter metas ativas"),
    "menu.future_goals": ("Get future goals", "Obter metas futuras"),
    "menu.past_goals": ("Get past goals", "Obter metas passadas"),
    "menu.badge_challenges": ("Get badge challenges", "Obter desafios de medalhas"),
    "menu.incomplete_badges": (
        "Get non-completed badge challenges",
        "Obter desafios de medalhas não concluídos",
    ),
    "menu.virtual_challenges": (
        "Get virtual challenges in progress",
        "Obter desafios virtuais em andamento",
    ),
    "menu.race_predictions": ("Get race predictions", "Obter previsões de corrida"),
    "menu.hill_score": (
        "Get hill score from '{start}' to '{end}'",
        "Obter pontuação de subida de '{start}' a '{end}'",
    ),
    "menu.endurance_score": (
        "Get endurance score from '{start}' to '{end}'",
        "Obter pontuação de resistência de '{start}' a '{end}'",
    ),
    "menu.available_badges": ("Get available badges", "Obter medalhas disponíveis"),
    "menu.badges_progress": ("Get badges in progress", "Obter medalhas em andamento"),
    "menu.devices": (
        "Get all device information",
        "Obter informações de todos os dispositivos",
    ),
    "menu.device_alarms": ("Get device alarms", "Obter alarmes do dispositivo"),
    "menu.solar": (
        "Get solar data from your devices",
        "Obter dados solares dos seus dispositivos",
    ),
    "menu.reload": (
        "Request data reload (epoch) for '{date}'",
        "Solicitar recarga de dados (epoch) para '{date}'",
    ),
    "menu.device_settings": (
        "Get device settings",
        "Obter configurações do dispositivo",
    ),
    "menu.device_last_used": ("Get device last used", "Obter último dispositivo usado"),
    "menu.primary_device": (
        "Get primary training device",
        "Obter dispositivo principal de treino",
    ),
    "menu.gear_list": ("Get user gear list", "Obter lista de equipamentos do usuário"),
    "menu.gear_defaults": ("Get gear defaults", "Obter equipamentos padrão"),
    "menu.gear_stats": ("Get gear statistics", "Obter estatísticas do equipamento"),
    "menu.gear_activities": ("Get gear activities", "Obter atividades do equipamento"),
    "menu.gear_default": ("Set gear default", "Definir equipamento padrão"),
    "menu.track_gear": (
        "Track gear usage (total time used)",
        "Acompanhar uso do equipamento (tempo total de uso)",
    ),
    "menu.activity_gear_edit": (
        "Add and remove gear to/from activity (interactive)",
        "Adicionar e remover equipamento da atividade (interativo)",
    ),
    "menu.create_gear": (
        "Create new gear, e.g. shoes (interactive)",
        "Criar equipamento, por exemplo, tênis (interativo)",
    ),
    "menu.hydration": (
        "Get hydration data for '{date}'",
        "Obter dados de hidratação de '{date}'",
    ),
    "menu.add_hydration": ("Add hydration data", "Adicionar dados de hidratação"),
    "menu.set_blood_pressure": (
        "Set blood pressure and pulse (interactive)",
        "Definir pressão arterial e pulso (interativo)",
    ),
    "menu.pregnancy": ("Get pregnancy summary data", "Obter resumo da gravidez"),
    "menu.all_day_events": (
        "Get all day events for '{start}'",
        "Obter eventos do dia inteiro de '{start}'",
    ),
    "menu.menstrual_date": (
        "Get menstrual data for '{date}'",
        "Obter dados menstruais de '{date}'",
    ),
    "menu.menstrual_calendar": (
        "Get menstrual calendar from '{start}' to '{end}'",
        "Obter calendário menstrual de '{start}' a '{end}'",
    ),
    "menu.delete_blood_pressure": (
        "Delete blood pressure entry",
        "Excluir registro de pressão arterial",
    ),
    "menu.nutrition_log": (
        "Get nutrition daily food log for '{date}'",
        "Obter registro diário de alimentação de '{date}'",
    ),
    "menu.nutrition_meals": (
        "Get nutrition daily meals for '{date}'",
        "Obter refeições diárias de '{date}'",
    ),
    "menu.nutrition_settings": (
        "Get nutrition daily settings for '{date}'",
        "Obter configurações nutricionais diárias de '{date}'",
    ),
    "menu.last_cycle": (
        "Get last confirmed menstrual cycle for '{date}'",
        "Obter último ciclo menstrual confirmado de '{date}'",
    ),
    "menu.cycle_summary": (
        "Get menstrual cycle summary for '{date}'",
        "Obter resumo do ciclo menstrual de '{date}'",
    ),
    "menu.menstrual_reports": (
        "Get menstrual reports (6 cycles) ending '{date}'",
        "Obter relatórios menstruais (6 ciclos) até '{date}'",
    ),
    "menu.update_menstrual_log": (
        "Update menstrual daily log (interactive)",
        "Atualizar registro menstrual diário (interativo)",
    ),
    "menu.update_menstrual_calendar": (
        "Update menstrual calendar (interactive)",
        "Atualizar calendário menstrual (interativo)",
    ),
    "menu.init_cycle": (
        "Initialize menstrual cycle setup (interactive)",
        "Inicializar configuração do ciclo menstrual (interativo)",
    ),
    "menu.confirm_period": (
        "Confirm menstrual period start (interactive)",
        "Confirmar início do período menstrual (interativo)",
    ),
    "menu.update_menstrual_settings": (
        "Update menstrual tracking settings (interactive)",
        "Atualizar configurações de acompanhamento menstrual (interativo)",
    ),
    "menu.health_report": (
        "Create sample health report",
        "Criar relatório de saúde de exemplo",
    ),
    "menu.remove_tokens": (
        "Remove stored login tokens (logout)",
        "Remover tokens de login armazenados (sair)",
    ),
    "menu.disconnect": (
        "Disconnect from Garmin Connect",
        "Desconectar do Garmin Connect",
    ),
    "menu.graphql": ("Execute GraphQL query", "Executar consulta GraphQL"),
    "menu.health_snapshot": (
        "Download Health Snapshot ZIP for today",
        "Baixar ZIP do Health Snapshot de hoje",
    ),
    "menu.get_training_plans": ("Get training plans", "Obter planos de treino"),
    "menu.training_plan_by_id": (
        "Get training plan by ID",
        "Obter plano de treino pelo ID",
    ),
    "menu.typed_strength": (
        "Upload typed strength workout (sample)",
        "Enviar treino de força tipado (exemplo)",
    ),
    "menu.exercise_catalog": (
        "Search exercise catalog",
        "Pesquisar catálogo de exercícios",
    ),
    "menu.update_workout": (
        "Update workout in place (edit existing template)",
        "Atualizar treino no local (editar modelo existente)",
    ),
    "menu.push_workout": (
        "Push a workout to a device (interactive)",
        "Enviar um treino para um dispositivo (interativo)",
    ),
    "menu.scheduled_workout_by_id": (
        "Get scheduled workout by ID",
        "Obter treino agendado pelo ID",
    ),
    "menu.delete_workout": (
        "Delete a workout template (interactive)",
        "Excluir um modelo de treino (interativo)",
    ),
    "menu.unschedule_workout": (
        "Unschedule a scheduled workout",
        "Desagendar um treino agendado",
    ),
    "menu.golf_summary": (
        "Get golf scorecard summary",
        "Obter resumo do cartão de golfe",
    ),
    "menu.golf_scorecard": (
        "Get golf scorecard by ID",
        "Obter cartão de golfe pelo ID",
    ),
    "menu.golf_shots": (
        "Get golf shot data by scorecard ID",
        "Obter dados das tacadas pelo ID do cartão de golfe",
    ),
    "menu.golf_club_stats": (
        "Get golf club stats",
        "Obter estatísticas dos tacos de golfe",
    ),
    "menu.golf_user_stats": (
        "Get golf user stats",
        "Obter estatísticas de golfe do usuário",
    ),
    "menu.activity_description": (
        "Set activity description (latest activity)",
        "Definir descrição da atividade (atividade mais recente)",
    ),
    "menu.activity_exercise_sets": (
        "Set activity exercise sets (strength activity)",
        "Definir séries de exercícios (atividade de força)",
    ),
    # General interface and authentication messages.
    "demo.title": (
        "🚴 Full-blown Garmin Connect API Demo - Main Menu",
        "🚴 Demonstração completa da API do Garmin Connect - Menu principal",
    ),
    "demo.select_category": ("Select a category:", "Selecione uma categoria:"),
    "demo.exit": ("  [q] Exit program", "  [q] Sair do programa"),
    "language.main_option": ("  [l] 🌐 Language", "  [l] 🌐 Idioma"),
    "language.select": ("🌐 Select language:", "🌐 Selecione o idioma:"),
    "language.option_en": ("English", "English"),
    "language.option_pt_br": ("Português do Brasil", "Português do Brasil"),
    "language.changed": (
        "✅ Language changed to {language}.",
        "✅ Idioma alterado para {language}.",
    ),
    "language.saved": (
        "Language preference saved.",
        "Preferência de idioma salva.",
    ),
    "language.save_failed": (
        "Unable to save language preference.",
        "Não foi possível salvar a preferência de idioma.",
    ),
    "language.back": ("  [q] Back to main menu", "  [q] Voltar ao menu principal"),
    "demo.selection": ("Make your selection: ", "Faça sua seleção: "),
    "demo.back": ("  [q] Back to main menu", "  [q] Voltar ao menu principal"),
    "demo.mfa_code": ("MFA one-time code: ", "Código único de MFA: "),
    "demo.not_tty": (
        "WARNING: stdin is not a TTY. Falling back to input().",
        "AVISO: stdin não é um TTY. Usando input() como alternativa.",
    ),
    "demo.enter_key": (
        "Enter a key (then press Enter): ",
        "Digite uma tecla (e pressione Enter): ",
    ),
    "demo.readkey_failed": ("readkey() failed: {error}", "readkey() falhou: {error}"),
    "demo.api_call": ("\n📡 API Call: {call}", "\n📡 Chamada da API: {call}"),
    "demo.api_group": ("\n📡 API Group: {group}", "\n📡 Grupo de API: {group}"),
    "demo.no_data": ("No data returned", "Nenhum dado retornado"),
    "demo.report_created": ("📊 Report created: {path}", "📊 Relatório criado: {path}"),
    "demo.group_saved": (
        "\n✅ Grouped responses saved to: {path}",
        "\n✅ Respostas agrupadas salvas em: {path}",
    ),
    "demo.solar_loading": (
        "☀️ Getting solar data from devices...",
        "☀️ Obtendo dados solares dos dispositivos...",
    ),
    "demo.device_missing": (
        "ℹ️ No devices found or error retrieving devices",
        "ℹ️ Nenhum dispositivo encontrado ou erro ao obter dispositivos",
    ),
    "demo.import_select": (
        "Select a file to import (will NOT be re-exported to Strava):",
        "Selecione um arquivo para importar (NÃO será reexportado para o Strava):",
    ),
    "demo.gpx_select": (
        "Select a GPX file to upload:",
        "Selecione um arquivo GPX para enviar:",
    ),
    "demo.invalid_selection": (
        "Invalid selection. Try again.",
        "Seleção inválida. Tente novamente.",
    ),
    "demo.valid_number": ("Please enter a valid number.", "Digite um número válido."),
    "demo.activity_file_missing": (
        "❌ No activity files found in test_data directory.",
        "❌ Nenhum arquivo de atividade encontrado no diretório test_data.",
    ),
    "demo.add_activity_files": (
        "ℹ️ Please add FIT/GPX/TCX files to test_data before importing.",
        "ℹ️ Adicione arquivos FIT/GPX/TCX a test_data antes de importar.",
    ),
    "demo.add_gpx_files": (
        "ℹ️ Please add GPX files to test_data before uploading.",
        "ℹ️ Adicione arquivos GPX a test_data antes de enviar.",
    ),
    "demo.file_not_found": (
        "❌ File not found: {path}",
        "❌ Arquivo não encontrado: {path}",
    ),
    "demo.activity_file_current_dir": (
        "ℹ️ Please ensure the activity file exists in the current directory",
        "ℹ️ Verifique se o arquivo de atividade existe no diretório atual",
    ),
    "demo.activity_imported": (
        "📥 Importing activity from file: {path}",
        "📥 Importando atividade do arquivo: {path}",
    ),
    "demo.activity_uploaded": (
        "📤 Uploading activity from file: {path}",
        "📤 Enviando atividade do arquivo: {path}",
    ),
    "demo.activity_duplicate": (
        "⚠️ Activity already exists (duplicate)",
        "⚠️ A atividade já existe (duplicada)",
    ),
    "demo.no_training_plans": (
        "ℹ️ No training plans found in your list",
        "ℹ️ Nenhum plano de treino encontrado na sua lista",
    ),
    "demo.no_activities": ("ℹ️ No activities found", "ℹ️ Nenhuma atividade encontrada"),
    "demo.no_workouts": ("ℹ️ No workouts found", "ℹ️ Nenhum treino encontrado"),
    "demo.no_strength": (
        "ℹ️ No strength training activities found",
        "ℹ️ Nenhuma atividade de treino de força encontrada",
    ),
    "demo.no_exercise_sets": (
        "ℹ️ No activity exercise sets available",
        "ℹ️ Nenhuma série de exercícios disponível",
    ),
    "demo.no_golf": (
        "❌ No golf scorecards found",
        "❌ Nenhum cartão de golfe encontrado",
    ),
    "demo.recent_golf": (
        "\n⛳ Recent golf scorecards:",
        "\n⛳ Cartões de golfe recentes:",
    ),
    "demo.scorecard_id": ("\nEnter scorecard ID: ", "\nDigite o ID do cartão: "),
    "demo.no_scorecard_id": (
        "❌ No scorecard ID provided",
        "❌ Nenhum ID de cartão informado",
    ),
    "demo.available_workouts": (
        "\nAvailable workouts (most recent):",
        "\nTreinos disponíveis (mais recentes):",
    ),
    "demo.available_devices": ("\nAvailable devices:", "\nDispositivos disponíveis:"),
    "demo.no_search_term": (
        "ℹ️ No search term entered",
        "ℹ️ Nenhum termo de pesquisa informado",
    ),
    "demo.personal_records": ("\nPersonal records:", "\nRecordes pessoais:"),
    "demo.available_activity_types": (
        "\nAvailable activity types:",
        "\nTipos de atividade disponíveis:",
    ),
    "demo.new_gear": ("Creating new gear...", "Criando novo equipamento..."),
    "demo.gear_details": (
        "Enter gear details (press Enter for defaults):",
        "Digite os detalhes do equipamento (pressione Enter para usar os padrões):",
    ),
    "demo.manual_activity": (
        "Creating manual activity...",
        "Criando atividade manual...",
    ),
    "demo.activity_details": (
        "Enter activity details (press Enter for defaults):",
        "Digite os detalhes da atividade (pressione Enter para usar os padrões):",
    ),
    "demo.graphql_queries": (
        "Available GraphQL queries:",
        "Consultas GraphQL disponíveis:",
    ),
    "demo.custom_query": ("  [c] Custom query", "  [c] Consulta personalizada"),
    "demo.no_virtual_challenges": (
        "ℹ️ No in-progress virtual challenges found",
        "ℹ️ Nenhum desafio virtual em andamento encontrado",
    ),
    "demo.hydration_added": (
        "✅ Hydration data added successfully!",
        "✅ Dados de hidratação adicionados com sucesso!",
    ),
    "demo.menstrual_notes": (
        "Omitted lists/scalars are cleared. Omitted notes are kept.",
        "Listas/escalares omitidos são apagados. Observações omitidas são mantidas.",
    ),
    "demo.clear_notes": (
        "Use a single '-' for notes to clear existing notes.",
        "Use um único '-' nas observações para apagá-las.",
    ),
    "demo.period_warning": (
        "Do not post predicted cycles as confirmed period dates.",
        "Não envie ciclos previstos como datas confirmadas do período.",
    ),
    "demo.period_groups": (
        "Enter period groups as comma-separated dates, groups separated by ';'.",
        "Digite grupos de datas do período separados por vírgulas; separe os grupos por ';'.",
    ),
    "demo.settings_json": (
        "Paste a JSON object of fields to change. Other menstrual settings are kept.",
        "Cole um objeto JSON com os campos a alterar. As outras configurações menstruais serão mantidas.",
    ),
    "demo.blood_pressure": (
        "🩸 Adding blood pressure (and pulse) measurement",
        "🩸 Adicionando medição de pressão arterial (e pulso)",
    ),
    "demo.blood_pressure_values": (
        "Enter blood pressure values (press Enter for defaults):",
        "Digite os valores da pressão arterial (pressione Enter para usar os padrões):",
    ),
    "demo.api_unavailable": ("API not available", "API indisponível"),
    "demo.tokens_removed": (
        "✅ Stored login token file removed",
        "✅ Arquivo de tokens de login armazenado removido",
    ),
    "demo.snapshot_saved": (
        "✅ Health Snapshot saved to: {path}",
        "✅ Health Snapshot salvo em: {path}",
    ),
    "demo.login_tokens": (
        "Attempting to login using stored tokens from: {path}",
        "Tentando fazer login usando tokens armazenados em: {path}",
    ),
    "demo.login_tokens_success": (
        "Successfully logged in using stored tokens!",
        "Login realizado com sucesso usando tokens armazenados!",
    ),
    "demo.fresh_login": (
        "No valid tokens found. Requesting fresh login credentials.",
        "Nenhum token válido encontrado. Solicitando novas credenciais de login.",
    ),
    "demo.logging_in": (
        "Logging in with credentials...",
        "Fazendo login com as credenciais...",
    ),
    "demo.mfa_required": (
        "Multi-factor authentication required",
        "Autenticação multifator necessária",
    ),
    "demo.mfa_submit": ("🔄 Submitting MFA code...", "🔄 Enviando código MFA..."),
    "demo.mfa_success": (
        "✅ MFA authentication successful!",
        "✅ Autenticação MFA realizada com sucesso!",
    ),
    "demo.mfa_too_many": ("❌ Too many MFA attempts", "❌ Muitas tentativas de MFA"),
    "demo.mfa_wait": (
        "💡 Please wait 30 minutes before trying again",
        "💡 Aguarde 30 minutos antes de tentar novamente",
    ),
    "demo.mfa_invalid": ("❌ Invalid MFA code", "❌ Código MFA inválido"),
    "demo.mfa_check": (
        "💡 Please verify your MFA code and try again",
        "💡 Verifique o código MFA e tente novamente",
    ),
    "demo.login_cancelled": (
        "\nLogin cancelled by user",
        "\nLogin cancelado pelo usuário",
    ),
    "demo.interrupted": (
        "\nInterrupted by user. Press q to quit.",
        "\nInterrompido pelo usuário. Pressione q para sair.",
    ),
    "demo.exit_message": (
        "Be active, generate some data to play with next time ;-) Bye!",
        "Mantenha-se ativo, gere alguns dados para explorar na próxima vez ;-) Até logo!",
    ),
    "demo.password": ("Password: ", "Senha: "),
    # Prompts and common operation results.
    "prompt.enter_number": (
        "Enter number (1-{maximum}): ",
        "Digite o número (1-{maximum}): ",
    ),
    "prompt.enter_weight": (
        "Enter weight (30-300, default: 85.1): ",
        "Digite o peso (30-300, padrão: 85,1): ",
    ),
    "prompt.enter_weight_kg": (
        "Enter weight in kg (30-300, default: 85.1): ",
        "Digite o peso em kg (30-300, padrão: 85,1): ",
    ),
    "prompt.enter_unit": (
        "Enter unit (kg/lbs, default: kg): ",
        "Digite a unidade (kg/lbs, padrão: kg): ",
    ),
    "prompt.email": ("Email address: ", "Endereço de e-mail: "),
    "prompt.exercise": (
        "Enter exercise name or search term: ",
        "Digite o nome do exercício ou termo de pesquisa: ",
    ),
    "prompt.notes": (
        "Notes (empty keep, '-' clear): ",
        "Observações (vazio mantém, '-' apaga): ",
    ),
    "prompt.symptoms": (
        "Symptoms (comma-separated): ",
        "Sintomas (separados por vírgulas): ",
    ),
    "prompt.moods": ("Moods (comma-separated): ", "Humores (separados por vírgulas): "),
    "prompt.discharge": (
        "Discharge (comma-separated): ",
        "Corrimento (separado por vírgulas): ",
    ),
    "prompt.flow": (
        "Flow [LIGHT|MEDIUM|HEAVY, empty omit]: ",
        "Fluxo [LIGHT|MEDIUM|HEAVY, vazio omite]: ",
    ),
    "prompt.sex_drive": (
        "Sex drive [LOW|AVERAGE|HIGH, empty omit]: ",
        "Libido [LOW|AVERAGE|HIGH, vazio omite]: ",
    ),
    "prompt.sexual_activity": (
        "Sexual activity [PROTECTED|UNPROTECTED, empty omit]: ",
        "Atividade sexual [PROTECTED|UNPROTECTED, vazio omite]: ",
    ),
    "prompt.date": ("Date [{date}]: ", "Data [{date}]: "),
    "prompt.start_date": ("Start date (YYYY-MM-DD): ", "Data inicial (AAAA-MM-DD): "),
    "prompt.end_date": ("End date (YYYY-MM-DD): ", "Data final (AAAA-MM-DD): "),
    "prompt.period_groups": ("Period date groups: ", "Grupos de datas do período: "),
    "prompt.period_start": (
        "Period start date (YYYY-MM-DD): ",
        "Data de início do período (AAAA-MM-DD): ",
    ),
    "prompt.period_length": ("Period length (days): ", "Duração do período (dias): "),
    "prompt.cycle_length": ("Cycle length (days): ", "Duração do ciclo (dias): "),
    "prompt.settings_json": ("Settings JSON: ", "JSON das configurações: "),
    "prompt.systolic": ("Systolic pressure [120]: ", "Pressão sistólica [120]: "),
    "prompt.diastolic": ("Diastolic pressure [80]: ", "Pressão diastólica [80]: "),
    "prompt.pulse": (
        "Pulse rate (optional, press Enter to omit): ",
        "Frequência do pulso (opcional, pressione Enter para omitir): ",
    ),
    "prompt.notes_optional": ("Notes (optional): ", "Observações (opcional): "),
    "prompt.ovulation": ("Ovulation day? [y/N]: ", "Dia da ovulação? [y/N]: "),
    "prompt.predicted_cycle": ("Predicted cycle? [y/N]: ", "Ciclo previsto? [y/N]: "),
    "prompt.query": ("Query: ", "Consulta: "),
    "prompt.custom_query": (
        "\nEnter your custom GraphQL query:",
        "\nDigite sua consulta GraphQL personalizada:",
    ),
    "prompt.query_choice": (
        "\nEnter choice (1-16, c): ",
        "\nDigite uma opção (1-16, c): ",
    ),
    "prompt.holes": (
        "Enter hole numbers 1-9, comma/dash separated (10-18 cannot be fetched with a filter; the API returns all 18 holes, or Enter for all): ",
        "Digite os números dos buracos de 1 a 9, separados por vírgula/hífen (10-18 não podem ser filtrados; a API retorna os 18 buracos, ou pressione Enter para todos): ",
    ),
    "prompt.year": ("Enter year (YYYY): ", "Digite o ano (AAAA): "),
    "prompt.month": ("Enter month (1-12): ", "Digite o mês (1-12): "),
    "prompt.scheduled_id": (
        "Enter scheduled workout ID: ",
        "Digite o ID do treino agendado: ",
    ),
    "prompt.unschedule_id": (
        "Enter scheduled workout ID to unschedule: ",
        "Digite o ID do treino agendado a desagendar: ",
    ),
    "prompt.device_index": (
        "\nEnter device index (0-{maximum}, blank for last used device): ",
        "\nDigite o índice do dispositivo (0-{maximum}, vazio para o último usado): ",
    ),
    "prompt.weigh_in_delete": (
        "Enter the index of the weigh-in to delete (or 'q' to cancel): ",
        "Digite o índice da pesagem a excluir (ou 'q' para cancelar): ",
    ),
    "prompt.activity_type_index": (
        "\nEnter activity type index to filter by (blank for no filter): ",
        "\nDigite o índice do tipo de atividade para filtrar (vazio para não filtrar): ",
    ),
    "prompt.activity_subtype": (
        "Activity subtype{hint} (blank for none): ",
        "Subtipo da atividade{hint} (vazio para nenhum): ",
    ),
    "prompt.activity_type": (
        "Enter activity type index: (or 'q' to cancel): ",
        "Digite o índice do tipo de atividade (ou 'q' para cancelar): ",
    ),
    "prompt.new_description": (
        "Enter new description (or 'q' to cancel): ",
        "Digite a nova descrição (ou 'q' para cancelar): ",
    ),
    "prompt.resubmit_sets": (
        "Re-submit current sets? (yes/no): ",
        "Reenviar as séries atuais? (yes/no): ",
    ),
    "prompt.workout_index": (
        "\nEnter workout index (0-{maximum}, or 'q' to cancel): ",
        "\nDigite o índice do treino (0-{maximum}, ou 'q' para cancelar): ",
    ),
    "prompt.push_workout_index": (
        "\nEnter workout index to push (0-{maximum}, blank for last workout, or 'q' to cancel): ",
        "\nDigite o índice do treino a enviar (0-{maximum}, vazio para o último treino, ou 'q' para cancelar): ",
    ),
    "prompt.delete_workout_index": (
        "\nEnter workout index to delete (0-{maximum}, or 'q' to cancel): ",
        "\nDigite o índice do treino a excluir (0-{maximum}, ou 'q' para cancelar): ",
    ),
    "prompt.update_workout_index": (
        "\nEnter workout index to update (0-{maximum}, or 'q' to cancel): ",
        "\nDigite o índice do treino a atualizar (0-{maximum}, ou 'q' para cancelar): ",
    ),
    "prompt.schedule_date": (
        "Enter date to schedule '{name}' (YYYY-MM-DD, default: today): ",
        "Digite a data para agendar '{name}' (AAAA-MM-DD, padrão: hoje): ",
    ),
    "prompt.delete_workout": (
        "Delete '{name}' (ID: {workout_id})? (y/N): ",
        "Excluir '{name}' (ID: {workout_id})? (y/N): ",
    ),
    "prompt.new_workout_name": (
        "New name for '{name}' (blank to keep): ",
        "Novo nome para '{name}' (vazio mantém): ",
    ),
    "prompt.gear_type": ("Gear type [SHOES]: ", "Tipo de equipamento [SHOES]: "),
    "prompt.brand": ("Brand [Anta]: ", "Marca [Anta]: "),
    "prompt.model": ("Model [A-Flash]: ", "Modelo [A-Flash]: "),
    "prompt.nickname": ("Nickname [Test]: ", "Apelido [Test]: "),
    "prompt.first_use": (
        "First use date [{date}]: ",
        "Data do primeiro uso [{date}]: ",
    ),
    "prompt.usage_type": (
        "Usage tracking type [DISTANCE]: ",
        "Tipo de acompanhamento de uso [DISTANCE]: ",
    ),
    "prompt.gear_threshold": (
        "Max use threshold in km (blank for none): ",
        "Limite máximo de uso em km (vazio para nenhum): ",
    ),
    "prompt.default_types": (
        "Default activity types, comma-separated [running]: ",
        "Tipos de atividade padrão, separados por vírgulas [running]: ",
    ),
    "prompt.gear_notes": (
        "Notes (blank for none): ",
        "Observações (vazio para nenhuma): ",
    ),
    "prompt.new_activity_name": (
        "Enter new activity name: (or 'q' to cancel): ",
        "Digite o novo nome da atividade (ou 'q' para cancelar): ",
    ),
    "prompt.delete_activity": (
        "Enter activity index to delete: (or 'q' to cancel): ",
        "Digite o índice da atividade a excluir (ou 'q' para cancelar): ",
    ),
    "prompt.delete_activity_confirm": (
        "Delete '{name}'? (yes/no): ",
        "Excluir '{name}'? (yes/no): ",
    ),
    "prompt.delete_entry": (
        "\nEnter entry index to delete: (or 'q' to cancel): ",
        "\nDigite o índice do registro a excluir (ou 'q' para cancelar): ",
    ),
    "prompt.delete_entry_confirm": (
        "Delete entry '{entry}'? (yes/no): ",
        "Excluir o registro '{entry}'? (yes/no): ",
    ),
    "prompt.delete_weigh_in_confirm": (
        "Delete weigh-in {weight} {unit} from {date}? (yes/no): ",
        "Excluir a pesagem de {weight} {unit} em {date}? (yes/no): ",
    ),
    "prompt.activity_name": (
        "Activity name [Manual Activity]: ",
        "Nome da atividade [Manual Activity]: ",
    ),
    "prompt.activity_type_key": (
        "Activity type key [running]: ",
        "Chave do tipo de atividade [running]: ",
    ),
    "prompt.duration": ("Duration in minutes [60]: ", "Duração em minutos [60]: "),
    "prompt.distance": (
        "Distance in kilometers [5]: ",
        "Distância em quilômetros [5]: ",
    ),
    "prompt.timezone": ("Timezone [UTC]: ", "Fuso horário [UTC]: "),
    "prompt.exported": (
        "📁 Exported data will be saved to the directory: '{path}'",
        "📁 Os dados exportados serão salvos no diretório: '{path}'",
    ),
    "prompt.responses_file": (
        "📄 All API responses are written to: 'response.json'",
        "📄 Todas as respostas da API são gravadas em: 'response.json'",
    ),
    "result.activity_download": (
        "📥 Downloading activities by date range ({start} to {end})...",
        "📥 Baixando atividades do período ({start} a {end})...",
    ),
    "result.activities_found": (
        "📊 Found {count} activities to download",
        "📊 {count} atividades encontradas para download",
    ),
    "result.download_complete": (
        "✅ Activity downloads completed! Files saved to: {path}",
        "✅ Downloads de atividades concluídos! Arquivos salvos em: {path}",
    ),
    "result.weigh_in_added": (
        "✅ Weigh-in data added successfully!",
        "✅ Dados da pesagem adicionados com sucesso!",
    ),
    "result.body_added": (
        "✅ Body composition data added successfully!",
        "✅ Dados de composição corporal adicionados com sucesso!",
    ),
    "result.weigh_ins_deleted": (
        "✅ Weigh-ins deleted successfully!",
        "✅ Pesagens excluídas com sucesso!",
    ),
    "result.workout_uploaded": (
        "✅ Workout uploaded successfully!",
        "✅ Treino enviado com sucesso!",
    ),
    "result.workout_downloaded": (
        "✅ Workout downloaded to: {path}",
        "✅ Treino baixado para: {path}",
    ),
    "result.no_workout_data": (
        "❌ No workout data available",
        "❌ Nenhum dado de treino disponível",
    ),
    "result.workout_scheduled": (
        "✅ Workout scheduled successfully!",
        "✅ Treino agendado com sucesso!",
    ),
    "result.workout_deleted": (
        "✅ Workout deleted successfully!",
        "✅ Treino excluído com sucesso!",
    ),
    "result.workout_updated": (
        "✅ Workout updated successfully!",
        "✅ Treino atualizado com sucesso!",
    ),
    "result.workout_pushed": (
        "✅ Workout pushed to device successfully!",
        "✅ Treino enviado ao dispositivo com sucesso!",
    ),
    "result.workout_unscheduled": (
        "✅ Workout unscheduled successfully!",
        "✅ Treino desagendado com sucesso!",
    ),
    "result.manual_created": (
        "✅ Manual activity created!",
        "✅ Atividade manual criada!",
    ),
    "result.activity_deleted": ("✅ Activity deleted!", "✅ Atividade excluída!"),
    "result.activity_name_updated": (
        "✅ Activity name updated!",
        "✅ Nome da atividade atualizado!",
    ),
    "result.activity_type_updated": (
        "✅ Activity type updated!",
        "✅ Tipo da atividade atualizado!",
    ),
    "result.description_updated": (
        "✅ Activity description updated!",
        "✅ Descrição da atividade atualizada!",
    ),
    "result.exercise_sets_submitted": (
        "✅ Exercise sets submitted!",
        "✅ Séries de exercícios enviadas!",
    ),
    "result.gear_created": ("✅ Gear created!", "✅ Equipamento criado!"),
    "result.gear_added": (
        "✅ Gear added successfully!",
        "✅ Equipamento adicionado com sucesso!",
    ),
    "result.gear_removed": (
        "✅ Gear removed successfully!",
        "✅ Equipamento removido com sucesso!",
    ),
    "result.gear_default": (
        "✅ Gear default set successfully!",
        "✅ Equipamento padrão definido com sucesso!",
    ),
    "result.bp_set": (
        "✅ Blood pressure data set successfully!",
        "✅ Dados da pressão arterial definidos com sucesso!",
    ),
    "result.bp_deleted": (
        "✅ Blood pressure entry deleted!",
        "✅ Registro de pressão arterial excluído!",
    ),
    "result.virtual_challenges": (
        "✅ Virtual challenges data retrieved successfully",
        "✅ Dados dos desafios virtuais obtidos com sucesso",
    ),
    "error.no_data_range": (
        "ℹ️ No activities found in the specified date range",
        "ℹ️ Nenhuma atividade encontrada no período informado",
    ),
    "error.no_weigh_today": (
        "ℹ️ No weigh-ins found for today",
        "ℹ️ Nenhuma pesagem encontrada para hoje",
    ),
    "error.no_devices": ("ℹ️ No devices found", "ℹ️ Nenhum dispositivo encontrado"),
    "error.no_gear": ("ℹ️ No gear found", "ℹ️ Nenhum equipamento encontrado"),
    "error.no_records": (
        "ℹ️ No personal records found",
        "ℹ️ Nenhum recorde pessoal encontrado",
    ),
    "error.cancelled": ("❌ Cancelled", "❌ Cancelado"),
    "error.invalid_index": ("❌ Invalid index", "❌ Índice inválido"),
    "error.invalid_input": ("❌ Invalid input", "❌ Entrada inválida"),
    "error.invalid_selection": ("❌ Invalid selection", "❌ Seleção inválida"),
    "error.invalid_number": (
        "❌ Please enter a valid number",
        "❌ Digite um número válido",
    ),
    "error.invalid_numeric": (
        "❌ Invalid numeric input",
        "❌ Entrada numérica inválida",
    ),
    "error.invalid_plan": ("❌ Invalid plan ID", "❌ ID de plano inválido"),
    "error.invalid_choice": ("❌ Invalid choice", "❌ Opção inválida"),
    "error.kg_lbs": ("❌ Please enter 'kg' or 'lbs'", "❌ Digite 'kg' ou 'lbs'"),
    "error.weight": (
        "❌ Weight must be between 30 and 300",
        "❌ O peso deve estar entre 30 e 300",
    ),
    "error.weight_kg": (
        "❌ Weight must be between 30 and 300 kg",
        "❌ O peso deve estar entre 30 e 300 kg",
    ),
    "error.no_activity_id": (
        "ℹ️ This record entry has no activityId to look up",
        "ℹ️ Este registro não possui activityId para consulta",
    ),
    "error.no_profile": (
        "❌ Could not get user profile number",
        "❌ Não foi possível obter o número do perfil do usuário",
    ),
    "error.no_gear_uuid": (
        "❌ No gear UUID found",
        "❌ Nenhum UUID de equipamento encontrado",
    ),
    "error.no_blood_pressure": (
        "❌ No blood pressure entries found for past week",
        "❌ Nenhum registro de pressão arterial encontrado na última semana",
    ),
    "error.no_query": ("❌ No query provided", "❌ Nenhuma consulta informada"),
    "error.virtual_unavailable": (
        "ℹ️ Virtual challenges are not available for your account",
        "ℹ️ Desafios virtuais não estão disponíveis para sua conta",
    ),
    "error.no_gear_user": (
        "No gear found for this user.",
        "Nenhum equipamento encontrado para este usuário.",
    ),
    "error.no_activities_gear": (
        "No activities found for the given gear uuid.",
        "Nenhuma atividade encontrada para o UUID de equipamento informado.",
    ),
    "error.file_format": (
        "❌ Invalid file format: The activity file format is not supported or corrupted",
        "❌ Formato de arquivo inválido: o formato do arquivo de atividade não é compatível ou está corrompido",
    ),
    "error.supported_formats": (
        "ℹ️ Supported formats: FIT, GPX, TCX",
        "ℹ️ Formatos compatíveis: FIT, GPX, TCX",
    ),
    "error.duplicate_full": (
        "⚠️ Activity already exists: This activity has already been uploaded to Garmin Connect",
        "⚠️ A atividade já existe: ela já foi enviada ao Garmin Connect",
    ),
    "error.duplicate_info": (
        "ℹ️ Garmin Connect prevents duplicate activities from being uploaded",
        "ℹ️ O Garmin Connect impede o envio de atividades duplicadas",
    ),
    "error.modify_file": (
        "💡 Try modifying the activity timestamps or creating a new activity file",
        "💡 Tente alterar os horários da atividade ou criar um novo arquivo",
    ),
    "error.file_too_large": (
        "❌ File too large: The activity file exceeds Garmin Connect's size limit",
        "❌ Arquivo grande demais: o arquivo de atividade excede o limite de tamanho do Garmin Connect",
    ),
    "error.compress_file": (
        "💡 Try compressing the file or reducing the number of data points",
        "💡 Tente compactar o arquivo ou reduzir o número de pontos de dados",
    ),
    "error.bad_request": (
        "❌ Bad request: Invalid activity data or malformed file",
        "❌ Solicitação inválida: dados de atividade inválidos ou arquivo malformado",
    ),
    "error.check_gps": (
        "💡 Check if the activity file contains valid GPS coordinates and timestamps",
        "💡 Verifique se o arquivo contém coordenadas GPS e horários válidos",
    ),
    "error.auth_upload": (
        "💡 Authentication failed - please login again",
        "💡 Falha na autenticação — faça login novamente",
    ),
    "error.session_expired": (
        "💡 Your session may have expired",
        "💡 Sua sessão pode ter expirado",
    ),
    "error.rate_limit_upload": (
        "❌ Rate limit exceeded: Too many upload requests",
        "❌ Limite de requisições excedido: muitas solicitações de envio",
    ),
    "error.wait": (
        "💡 Please wait a few minutes before trying again",
        "💡 Aguarde alguns minutos antes de tentar novamente",
    ),
    "error.permission": (
        "💡 Permission denied - check account permissions",
        "💡 Permissão negada — verifique as permissões da conta",
    ),
    "error.workout_invalid": (
        "💡 The workout data may be invalid or malformed",
        "💡 Os dados do treino podem ser inválidos ou estar malformados",
    ),
    "error.workout_exists": (
        "💡 Workout may already exist",
        "💡 O treino pode já existir",
    ),
    "error.workout_validation": (
        "💡 Workout data validation failed",
        "💡 Falha na validação dos dados do treino",
    ),
    "error.pydantic": (
        "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]",
        "💡 Instale pydantic com: pip install pydantic ou pip install garminconnect[workout]",
    ),
}

# Messages emitted by the less frequently used interactive operations.  They
# are kept in a separate block to make the main menu catalog easier to scan.
_MESSAGES.update(
    {
        "ui.fetch_gear": (
            "🔄 Fetching user gear list...",
            "🔄 Obtendo a lista de equipamentos do usuário...",
        ),
        "ui.fetch_gear_defaults": (
            "🔄 Fetching gear defaults...",
            "🔄 Obtendo equipamentos padrão...",
        ),
        "ui.fetch_gear_stats": (
            "🔄 Fetching comprehensive gear statistics...",
            "🔄 Obtendo estatísticas completas do equipamento...",
        ),
        "ui.fetch_gear_activities": (
            "🔄 Fetching gear activities...",
            "🔄 Obtendo atividades do equipamento...",
        ),
        "ui.virtual_loading": (
            "🏆 Attempting to get virtual challenges data...",
            "🏆 Tentando obter dados dos desafios virtuais...",
        ),
        "ui.challenge_alternatives": (
            "💡 You can try other challenge-related endpoints instead:",
            "💡 Você pode tentar outros endpoints relacionados a desafios:",
        ),
        "ui.badge_menu": (
            "   - Badge challenges (menu option 7-8)",
            "   - Desafios de medalhas (opção 7-8 do menu)",
        ),
        "ui.available_badge_menu": (
            "   - Available badge challenges (menu option 7-4)",
            "   - Desafios de medalhas disponíveis (opção 7-4 do menu)",
        ),
        "ui.adhoc_menu": (
            "   - Adhoc challenges (menu option 7-3)",
            "   - Desafios avulsos (opção 7-3 do menu)",
        ),
        "ui.disconnected": (
            "✅ Disconnected from Garmin Connect",
            "✅ Desconectado do Garmin Connect",
        ),
        "ui.weigh_in_loading": ("⚖️ Adding weigh-in entry", "⚖️ Adicionando pesagem"),
        "ui.running_upload": (
            "🏃 Creating and uploading running workout...",
            "🏃 Criando e enviando treino de corrida...",
        ),
        "ui.cycling_upload": (
            "🚴 Creating and uploading cycling workout...",
            "🚴 Criando e enviando treino de ciclismo...",
        ),
        "ui.swimming_upload": (
            "🏊 Creating and uploading swimming workout...",
            "🏊 Criando e enviando treino de natação...",
        ),
        "ui.walking_upload": (
            "🚶 Creating and uploading walking workout...",
            "🚶 Criando e enviando treino de caminhada...",
        ),
        "ui.hiking_upload": (
            "🥾 Creating and uploading hiking workout...",
            "🥾 Criando e enviando treino de trilha...",
        ),
        "ui.strength_upload": (
            "🏋️ Creating and uploading strength workout...",
            "🏋️ Criando e enviando treino de força...",
        ),
        "ui.replace_sets": (
            "⚠️  This REPLACES all exercise sets (replace-all). The demo re-submits the same payload unchanged, so nothing actually changes.",
            "⚠️  Isto SUBSTITUI todas as séries de exercícios (substituição total). A demonstração reenvia o mesmo payload sem alterações, portanto nada muda.",
        ),
        "ui.graphql_activities": (
            "  [1] Activities (recent activities with details)",
            "  [1] Atividades (atividades recentes com detalhes)",
        ),
        "ui.graphql_health": (
            "  [2] Health Snapshot (comprehensive health data)",
            "  [2] Health Snapshot (dados completos de saúde)",
        ),
        "ui.graphql_weight": (
            "  [3] Weight Data (weight measurements)",
            "  [3] Dados de peso (medições de peso)",
        ),
        "ui.graphql_bp": (
            "  [4] Blood Pressure (blood pressure data)",
            "  [4] Pressão arterial (dados de pressão arterial)",
        ),
        "ui.graphql_sleep": (
            "  [5] Sleep Summaries (sleep analysis)",
            "  [5] Resumos do sono (análise do sono)",
        ),
        "ui.graphql_hrv": (
            "  [6] Heart Rate Variability (HRV data)",
            "  [6] Variabilidade da Frequência Cardíaca (dados de VFC)",
        ),
        "ui.graphql_summary": (
            "  [7] User Daily Summary (comprehensive daily stats)",
            "  [7] Resumo diário do usuário (estatísticas diárias completas)",
        ),
        "ui.graphql_readiness": (
            "  [8] Training Readiness (training readiness metrics)",
            "  [8] Prontidão para Treino (métricas de prontidão)",
        ),
        "ui.graphql_status": (
            "  [9] Training Status (training status data)",
            "  [9] Status de Treinamento (dados do status)",
        ),
        "ui.graphql_activity_stats": (
            "  [10] Activity Stats (aggregated activity statistics)",
            "  [10] Estatísticas de atividade (estatísticas agregadas)",
        ),
        "ui.graphql_vo2": (
            "  [11] VO2 Max (VO2 max data)",
            "  [11] VO2 Max (dados de VO2 máximo)",
        ),
        "ui.graphql_endurance": (
            "  [12] Endurance Score (endurance scoring)",
            "  [12] Pontuação de resistência (pontuação de resistência)",
        ),
        "ui.graphql_goals": (
            "  [13] User Goals (current goals)",
            "  [13] Metas do usuário (metas atuais)",
        ),
        "ui.graphql_stress": (
            "  [14] Stress Data (epoch chart with stress)",
            "  [14] Dados de estresse (gráfico de épocas com estresse)",
        ),
        "ui.graphql_badges": (
            "  [15] Badge Challenges (available challenges)",
            "  [15] Desafios de medalhas (desafios disponíveis)",
        ),
        "ui.graphql_adhoc": (
            "  [16] Adhoc Challenges (adhoc challenges)",
            "  [16] Desafios avulsos (desafios avulsos)",
        ),
        "ui.gpx_missing": (
            "❌ No .gpx files found in test_data directory.",
            "❌ Nenhum arquivo .gpx encontrado no diretório test_data.",
        ),
        "ui.check_credentials": (
            "💡 Please check your login credentials and try again",
            "💡 Verifique suas credenciais de login e tente novamente",
        ),
        "ui.check_connection": (
            "💡 Please check your internet connection and try again",
            "💡 Verifique sua conexão com a internet e tente novamente",
        ),
        "ui.no_plans_id": (
            "❌ No training plans available and no ID provided",
            "❌ Nenhum plano de treino disponível e nenhum ID informado",
        ),
        "ui.workout_json_missing": (
            "ℹ️ Please ensure the workout JSON file exists in the test_data directory",
            "ℹ️ Verifique se o arquivo JSON do treino existe no diretório test_data",
        ),
        "ui.check_json": (
            "ℹ️ Please check the JSON file format",
            "ℹ️ Verifique o formato do arquivo JSON",
        ),
        "ui.year_month_required": (
            "❌ Year and month are required",
            "❌ Ano e mês são obrigatórios",
        ),
        "ui.scheduled_id_required": (
            "❌ Scheduled workout ID is required",
            "❌ O ID do treino agendado é obrigatório",
        ),
        "ui.add_test_weigh": (
            "💡 You can add a test weigh-in using menu option [4]",
            "💡 Você pode adicionar uma pesagem de teste usando a opção [4] do menu",
        ),
        "ui.add_test_measurement": (
            "💡 You can add a test measurement using menu option [3]",
            "💡 Você pode adicionar uma medição de teste usando a opção [3] do menu",
        ),
        "ui.limit_activity_types": (
            "\nAvailable activity types: (limit=10)",
            "\nTipos de atividade disponíveis: (limite=10)",
        ),
        "ui.recent_activities": ("\nRecent activities:", "\nAtividades recentes:"),
        "ui.bp_range": (
            "❌ Invalid systolic pressure (should be between 70-260)",
            "❌ Pressão sistólica inválida (deve estar entre 70 e 260)",
        ),
        "ui.bp_diastolic_range": (
            "❌ Invalid diastolic pressure (should be between 40-150)",
            "❌ Pressão diastólica inválida (deve estar entre 40 e 150)",
        ),
        "ui.pulse_range": (
            "❌ Invalid pulse rate (should be between 20-250)",
            "❌ Frequência de pulso inválida (deve estar entre 20 e 250)",
        ),
        "ui.numeric_values": (
            "❌ Invalid input - please enter numeric values",
            "❌ Entrada inválida — digite valores numéricos",
        ),
        "ui.no_tokens": (
            "ℹ️ No stored login tokens found",
            "ℹ️ Nenhum token de login armazenado encontrado",
        ),
        "ui.no_snapshot": (
            "❌ No Health Snapshot content available for this date",
            "❌ Nenhum conteúdo de Health Snapshot disponível para esta data",
        ),
        "ui.no_weigh_response": (
            "📊 No weigh-in data found in response",
            "📊 Nenhum dado de pesagem encontrado na resposta",
        ),
        "ui.delete_cancelled": ("❌ Delete cancelled", "❌ Exclusão cancelada"),
        "ui.number_required": (
            "❌ Invalid input - please enter a number",
            "❌ Entrada inválida — digite um número",
        ),
        "ui.source_activity": (
            "\nEnter index to look up the source activity's details (blank to skip): ",
            "\nDigite o índice para consultar os detalhes da atividade de origem (vazio para ignorar): ",
        ),
        "ui.rename_cancelled": ("❌ Rename cancelled", "❌ Renomeação cancelada"),
        "ui.no_name": ("❌ No name provided", "❌ Nenhum nome informado"),
        "ui.type_cancelled": (
            "❌ Type change cancelled",
            "❌ Alteração de tipo cancelada",
        ),
        "ui.entry_cancelled": (
            "❌ Entry deletion cancelled",
            "❌ Exclusão do registro cancelada",
        ),
        "ui.retry_file_format": (
            "💡 Try converting to a different format or check file integrity",
            "💡 Tente converter para outro formato ou verifique a integridade do arquivo",
        ),
        "ui.weigh_deleted": (
            "✅ Weigh-in deleted successfully!",
            "✅ Pesagem excluída com sucesso!",
        ),
        "ui.confirm_garmin": (
            "Go check Garmin to confirm, then press Enter to continue",
            "Verifique no Garmin para confirmar e pressione Enter para continuar",
        ),
        "ui.move_legs": (
            "🐌 Time to get those legs moving!",
            "🐌 Hora de mexer as pernas!",
        ),
        "ui.crushing_it": (
            "🏃‍♂️ You're crushing it today!",
            "🏃‍♂️ Você está mandando muito bem hoje!",
        ),
        "ui.nice_progress": (
            "👍 Nice progress! Keep it up!",
            "👍 Bom progresso! Continue assim!",
        ),
        "ui.check_format": (
            "💡 Please check the file format and try again",
            "💡 Verifique o formato do arquivo e tente novamente",
        ),
        "ui.workout_no_content": (
            "  ❌ {format}: No content available",
            "  ❌ {format}: Nenhum conteúdo disponível",
        ),
        "stats.today": (
            "\n📊 Your Stats Today: {stats}",
            "\n📊 Suas estatísticas de hoje: {stats}",
        ),
        "stats.steps": ("{value} steps", "{value} passos"),
        "stats.water_goal": (
            "{value}ml water ({percent}% of goal)",
            "{value} ml de água ({percent}% da meta)",
        ),
        "stats.water_cups": (
            "{value}ml water ({cups} cups)",
            "{value} ml de água ({cups} copos)",
        ),
        "stats.kcal": ("{value} kcal", "{value} kcal"),
        "ui.upload_error": (
            "❌ Unexpected error uploading activity: {error}",
            "❌ Erro inesperado ao enviar atividade: {error}",
        ),
    }
)


# Repeated error prefixes are intentionally explicit: this preserves the
# exception text and any Garmin status details exactly as returned.
for _error_name, _english, _portuguese in (
    (
        "authentication",
        "❌ Authentication error: {error}",
        "❌ Erro de autenticação: {error}",
    ),
    ("connection", "❌ Connection error: {error}", "❌ Erro de conexão: {error}"),
    (
        "too_many_requests",
        "❌ Too many requests: {error}",
        "❌ Muitas solicitações: {error}",
    ),
    (
        "download_activities",
        "❌ Error downloading activities: {error}",
        "❌ Erro ao baixar atividades: {error}",
    ),
    (
        "add_weigh_in_error",
        "❌ Error adding weigh-in: {error}",
        "❌ Erro ao adicionar pesagem: {error}",
    ),
    (
        "workout_download_error",
        "❌ Error downloading workout: {error}",
        "❌ Erro ao baixar treino: {error}",
    ),
    (
        "workout_upload_error",
        "❌ Error uploading workout: {error}",
        "❌ Erro ao enviar treino: {error}",
    ),
    (
        "delete_workout_error",
        "❌ Error deleting workout: {error}",
        "❌ Erro ao excluir treino: {error}",
    ),
    (
        "update_workout_error",
        "❌ Error updating workout: {error}",
        "❌ Erro ao atualizar treino: {error}",
    ),
    (
        "body_error",
        "❌ Error adding body composition: {error}",
        "❌ Erro ao adicionar composição corporal: {error}",
    ),
    (
        "delete_weigh_error",
        "❌ Error deleting weigh-ins: {error}",
        "❌ Erro ao excluir pesagens: {error}",
    ),
    (
        "delete_single_weigh_error",
        "❌ Error deleting weigh-in: {error}",
        "❌ Erro ao excluir pesagem: {error}",
    ),
    (
        "gear_default_error",
        "❌ Error setting gear default: {error}",
        "❌ Erro ao definir equipamento padrão: {error}",
    ),
    (
        "gear_add_error",
        "❌ Error adding gear: {error}",
        "❌ Erro ao adicionar equipamento: {error}",
    ),
    (
        "gear_filter_error",
        "❌ Error getting filtered activities: {error}",
        "❌ Erro ao obter atividades filtradas: {error}",
    ),
    (
        "gear_create_error",
        "❌ Error creating gear: {error}",
        "❌ Erro ao criar equipamento: {error}",
    ),
    (
        "record_error",
        "❌ Error getting personal records: {error}",
        "❌ Erro ao obter recordes pessoais: {error}",
    ),
    (
        "activity_name_error",
        "❌ Error setting activity name: {error}",
        "❌ Erro ao definir nome da atividade: {error}",
    ),
    (
        "activity_type_error",
        "❌ Error setting activity type: {error}",
        "❌ Erro ao definir tipo da atividade: {error}",
    ),
    (
        "description_error",
        "❌ Error setting activity description: {error}",
        "❌ Erro ao definir descrição da atividade: {error}",
    ),
    (
        "exercise_sets_error",
        "❌ Error setting exercise sets: {error}",
        "❌ Erro ao definir séries de exercícios: {error}",
    ),
    (
        "manual_error",
        "❌ Error creating manual activity: {error}",
        "❌ Erro ao criar atividade manual: {error}",
    ),
    (
        "activity_delete_error",
        "❌ Error deleting activity: {error}",
        "❌ Erro ao excluir atividade: {error}",
    ),
    (
        "blood_pressure_delete_error",
        "❌ Error deleting blood pressure: {error}",
        "❌ Erro ao excluir pressão arterial: {error}",
    ),
    (
        "graphql_error",
        "❌ Error executing GraphQL query: {error}",
        "❌ Erro ao executar consulta GraphQL: {error}",
    ),
    (
        "hydration_error",
        "❌ Error adding hydration data: {error}",
        "❌ Erro ao adicionar dados de hidratação: {error}",
    ),
    (
        "menstrual_log_error",
        "❌ Error updating menstrual daily log: {error}",
        "❌ Erro ao atualizar registro menstrual diário: {error}",
    ),
    (
        "menstrual_calendar_error",
        "❌ Error updating menstrual calendar: {error}",
        "❌ Erro ao atualizar calendário menstrual: {error}",
    ),
    (
        "cycle_init_error",
        "❌ Error initializing menstrual cycle setup: {error}",
        "❌ Erro ao inicializar configuração do ciclo menstrual: {error}",
    ),
    (
        "period_confirm_error",
        "❌ Error confirming menstrual period start: {error}",
        "❌ Erro ao confirmar início do período menstrual: {error}",
    ),
    (
        "menstrual_settings_error",
        "❌ Error updating menstrual settings: {error}",
        "❌ Erro ao atualizar configurações menstruais: {error}",
    ),
    (
        "blood_pressure_error",
        "❌ Error setting blood pressure: {error}",
        "❌ Erro ao definir pressão arterial: {error}",
    ),
    (
        "token_remove_error",
        "❌ Error removing stored login tokens: {error}",
        "❌ Erro ao remover tokens de login armazenados: {error}",
    ),
    (
        "snapshot_error",
        "❌ Error downloading Health Snapshot: {error}",
        "❌ Erro ao baixar Health Snapshot: {error}",
    ),
):
    _MESSAGES[f"error.{_error_name}"] = (_english, _portuguese)

_MESSAGES.update(
    {
        "ui.exercise_matches": (
            "🔍 {count} exercise(s) matching '{term}' (showing up to 20):",
            "🔍 {count} exercício(s) correspondentes a '{term}' (mostrando até 20):",
        ),
        "ui.exact_exercise": (
            "✅ Exact match for '{term}':",
            "✅ Correspondência exata para '{term}':",
        ),
        "ui.exercise_location": (
            "   category={category} exercise={exercise}",
            "   categoria={category} exercício={exercise}",
        ),
        "ui.no_exercises": (
            "❌ No exercises found matching '{term}'",
            "❌ Nenhum exercício encontrado para '{term}'",
        ),
        "ui.exercise_item": (
            "   {name}: category={category} exercise={exercise}",
            "   {name}: categoria={category} exercício={exercise}",
        ),
        "ui.indexed_item": ("  [{index}] {name}", "  [{index}] {name}"),
        "ui.indexed_workout": (
            "  [{index}] {name} (ID: {workout_id})",
            "  [{index}] {name} (ID: {workout_id})",
        ),
        "ui.weighing": (
            "⚖️ Adding weigh-in: {weight} {unit}",
            "⚖️ Adicionando pesagem: {weight} {unit}",
        ),
        "ui.body_composition_loading": (
            "⚖️ Adding body composition data for {date}",
            "⚖️ Adicionando dados de composição corporal para {date}",
        ),
        "ui.daily_weigh_loading": (
            "🔍 Checking daily weigh-ins for today ({date})...",
            "🔍 Verificando pesagens diárias de hoje ({date})...",
        ),
        "ui.weighings_for_delete": (
            "\n⚖️ Found {count} weigh-in(s) available for deletion:",
            "\n⚖️ Encontradas {count} pesagem(ns) disponíveis para exclusão:",
        ),
        "ui.weighing_row": (
            "  [{index}] {weight} {unit} on {date} at {time}",
            "  [{index}] {weight} {unit} em {date} às {time}",
        ),
        "ui.record_row": (
            "{index}: {label} — {formatted}  (typeId={type_id}, raw value={value})",
            "{index}: {label} — {formatted}  (typeId={type_id}, valor bruto={value})",
        ),
        "ui.unconfirmed_record": (
            "{index}: Unconfirmed record type (typeId={type_id}, activityType={activity_type}, raw value={value})",
            "{index}: Tipo de registro não confirmado (typeId={type_id}, activityType={activity_type}, valor bruto={value})",
        ),
        "ui.activity_summary": (
            "Activity: {name} (id {activity_id})",
            "Atividade: {name} (id {activity_id})",
        ),
        "ui.current_description": (
            "Current description: {description}",
            "Descrição atual: {description}",
        ),
        "ui.exercise_count": (
            "Activity {activity_id} has {count} exercise set(s).",
            "A atividade {activity_id} tem {count} série(s) de exercícios.",
        ),
        "ui.format_error": (
            "Error formatting output: {error}",
            "Erro ao formatar a saída: {error}",
        ),
        "ui.save_group_error": (
            "Error saving grouped responses: {error}",
            "Erro ao salvar respostas agrupadas: {error}",
        ),
        "ui.file_number": ("  {index}. {name}", "  {index}. {name}"),
        "ui.download_item": (
            "📥 Downloading: {name} (ID: {activity_id})",
            "📥 Baixando: {name} (ID: {activity_id})",
        ),
        "ui.plan_missing": (
            "ℹ️ Plan ID {plan_id} not found in your plans; attempting fetch anyway",
            "ℹ️ O ID de plano {plan_id} não foi encontrado nos seus planos; tentando obter mesmo assim",
        ),
        "ui.plan_download": (
            "📥 Downloading workout: {name}",
            "📥 Baixando treino: {name}",
        ),
        "ui.gear_settings_error": (
            "❌ Error getting settings for device {device}: {error}",
            "❌ Erro ao obter configurações do dispositivo {device}: {error}",
        ),
        "ui.profile_action_error": (
            "❌ Error getting gear for track_gear_usage_data: {error}",
            "❌ Erro ao obter equipamento para track_gear_usage_data: {error}",
        ),
        "ui.current_activity_name": (
            "Current name of fetched activity: {name}",
            "Nome atual da atividade obtida: {name}",
        ),
        "ui.current_activity_type": (
            "Current type of fetched activity '{name}': {activity_type}",
            "Tipo atual da atividade obtida '{name}': {activity_type}",
        ),
        "ui.no_sets": (
            "ℹ️ Activity {activity_id} has no exercise sets to replace",
            "ℹ️ A atividade {activity_id} não possui séries de exercícios para substituir",
        ),
        "ui.activity_item": (
            "{index}: {name} ({activity_id}) - {start_time}",
            "{index}: {name} ({activity_id}) - {start_time}",
        ),
        "ui.bp_entries": (
            "\n📊 Found {count} blood pressure entries:",
            "\n📊 Encontrados {count} registros de pressão arterial:",
        ),
        "ui.error_execute": (
            "❌ Error executing {key}: {error}",
            "❌ Erro ao executar {key}: {error}",
        ),
        "ui.error_execute_option": (
            "❌ Error processing option {option}: {error}",
            "❌ Erro ao processar a opção {option}: {error}",
        ),
        "ui.error_health_report": (
            "Error creating health report: {error}",
            "Erro ao criar relatório de saúde: {error}",
        ),
        "ui.solar_device": (
            "\n☀️ Getting solar data for device: {name} (ID: {device_id})",
            "\n☀️ Obtendo dados solares do dispositivo: {name} (ID: {device_id})",
        ),
        "ui.import_error": (
            "❌ Import failed: {error}",
            "❌ Falha na importação: {error}",
        ),
        "ui.scorecard_short_row": (
            "  [{index}] ID={scorecard_id} - {course}",
            "  [{index}] ID={scorecard_id} - {course}",
        ),
        "ui.stats_weighings": (
            "📊 Found {count} weigh-in(s) for today",
            "📊 Encontradas {count} pesagem(ns) para hoje",
        ),
        "ui.stats_weighings_error": (
            "⚠️ Could not fetch daily weigh-ins: {error}",
            "⚠️ Não foi possível obter as pesagens diárias: {error}",
        ),
        "ui.connection_virtual": (
            "⚠️ Connection error accessing virtual challenges: {error}",
            "⚠️ Erro de conexão ao acessar desafios virtuais: {error}",
        ),
        "ui.unexpected_virtual": (
            "⚠️ Unexpected error accessing virtual challenges: {error}",
            "⚠️ Erro inesperado ao acessar desafios virtuais: {error}",
        ),
        "ui.tracking_gear": (
            "Tracking usage for gear: {name} (UUID: {uuid})",
            "Acompanhando uso do equipamento: {name} (UUID: {uuid})",
        ),
        "ui.executing": ("\n🔄 Executing: {key}", "\n🔄 Executando: {key}"),
        "ui.not_implemented": (
            "❌ API method '{key}' not implemented yet. You can add it later!",
            "❌ O método da API '{key}' ainda não foi implementado. Você pode adicioná-lo depois!",
        ),
        "ui.login_error": ("\n❌ {error}", "\n❌ {error}"),
        "ui.login_saved": (
            "Login successful! Tokens saved to: {path}",
            "Login realizado com sucesso! Tokens salvos em: {path}",
        ),
        "ui.skipping": (
            "Skipping data for {date}: {error}",
            "Ignorando dados de {date}: {error}",
        ),
        "ui.download_format_error": (
            "  ❌ {format}: Error downloading - {error}",
            "  ❌ {format}: Erro ao baixar — {error}",
        ),
        "ui.mfa_debug": (
            "🔍 Debug: MFA error details: {error}",
            "🔍 Depuração: detalhes do erro de MFA: {error}",
        ),
        "ui.mfa_error": (
            "❌ MFA authentication failed: {error}",
            "❌ Falha na autenticação MFA: {error}",
        ),
        "ui.unexpected": ("Unexpected error: {error}", "Erro inesperado: {error}"),
        "ui.invalid_option": (
            "❌ Invalid option selection. Valid options: {options}",
            "❌ Seleção de opção inválida. Opções válidas: {options}",
        ),
        "ui.http_error": (
            "❌ HTTP Error {status}: {error}",
            "❌ Erro HTTP {status}: {error}",
        ),
        "ui.stats_unavailable": (
            "Unable to fetch stats for display: {error}",
            "Não foi possível obter estatísticas para exibição: {error}",
        ),
        "ui.api_method_error": (
            "⚠️ {method} failed: {error}",
            "⚠️ {method} falhou: {error}",
        ),
        "ui.invalid_selection_categories": (
            "❌ Invalid selection. Use {categories} for categories or 'q' to quit",
            "❌ Seleção inválida. Use {categories} para categorias ou 'q' para sair",
        ),
        "ui.workout_file_upload": (
            "📤 Uploading workout from file: {path}",
            "📤 Enviando treino do arquivo: {path}",
        ),
        "ui.workout_uploading": (
            "📤 Uploading workout: {name}",
            "📤 Enviando treino: {name}",
        ),
        "ui.recording_bp": (
            "📊 Recording: {systolic}/{diastolic} mmHg, {pulse}",
            "📊 Registrando: {systolic}/{diastolic} mmHg, {pulse}",
        ),
        "ui.scorecard_row_with_date": (
            "  [{index}] ID={scorecard_id} - {course} ({date})",
            "  [{index}] ID={scorecard_id} - {course} ({date})",
        ),
    }
)

for _message_name, _english, _portuguese in (
    (
        "running_uploaded",
        "✅ Running workout uploaded successfully!",
        "✅ Treino de corrida enviado com sucesso!",
    ),
    (
        "running_failed",
        "❌ Failed to upload running workout",
        "❌ Falha ao enviar treino de corrida",
    ),
    (
        "cycling_uploaded",
        "✅ Cycling workout uploaded successfully!",
        "✅ Treino de ciclismo enviado com sucesso!",
    ),
    (
        "cycling_failed",
        "❌ Failed to upload cycling workout",
        "❌ Falha ao enviar treino de ciclismo",
    ),
    (
        "swimming_uploaded",
        "✅ Swimming workout uploaded successfully!",
        "✅ Treino de natação enviado com sucesso!",
    ),
    (
        "swimming_failed",
        "❌ Failed to upload swimming workout",
        "❌ Falha ao enviar treino de natação",
    ),
    (
        "walking_uploaded",
        "✅ Walking workout uploaded successfully!",
        "✅ Treino de caminhada enviado com sucesso!",
    ),
    (
        "walking_failed",
        "❌ Failed to upload walking workout",
        "❌ Falha ao enviar treino de caminhada",
    ),
    (
        "hiking_uploaded",
        "✅ Hiking workout uploaded successfully!",
        "✅ Treino de trilha enviado com sucesso!",
    ),
    (
        "hiking_failed",
        "❌ Failed to upload hiking workout",
        "❌ Falha ao enviar treino de trilha",
    ),
    (
        "strength_uploaded",
        "✅ Strength workout uploaded successfully!",
        "✅ Treino de força enviado com sucesso!",
    ),
    (
        "strength_failed",
        "❌ Failed to upload strength workout",
        "❌ Falha ao enviar treino de força",
    ),
    ("no_activity_error", "❌ No activities found", "❌ Nenhuma atividade encontrada"),
    (
        "credentials_check",
        "💡 Please check your username and password and try again",
        "💡 Verifique seu nome de usuário e senha e tente novamente",
    ),
    (
        "no_weigh_id",
        "❌ No weigh-in ID found for selected entry",
        "❌ Nenhum ID de pesagem encontrado para o registro selecionado",
    ),
    (
        "invalid_type_filter",
        "❌ Invalid index, no type filter applied",
        "❌ Índice inválido; nenhum filtro de tipo aplicado",
    ),
    (
        "auth_failed_error",
        "❌ Authentication failed: Please login again",
        "❌ Falha na autenticação: faça login novamente",
    ),
    (
        "upload_workout_failed",
        "❌ Failed to upload workout from {path}",
        "❌ Falha ao enviar treino de {path}",
    ),
    (
        "lactate_error",
        "❌ Error getting lactate threshold data: {error}",
        "❌ Erro ao obter dados de limiar de lactato: {error}",
    ),
    (
        "activity_splits_error",
        "❌ Error getting activity splits: {error}",
        "❌ Erro ao obter parciais da atividade: {error}",
    ),
    (
        "typed_splits_error",
        "❌ Error getting activity typed splits: {error}",
        "❌ Erro ao obter parciais categorizadas da atividade: {error}",
    ),
    (
        "split_summaries_error",
        "❌ Error getting activity split summaries: {error}",
        "❌ Erro ao obter resumos das parciais da atividade: {error}",
    ),
    (
        "activity_weather_error",
        "❌ Error getting activity weather: {error}",
        "❌ Erro ao obter clima da atividade: {error}",
    ),
    (
        "activity_hr_error",
        "❌ Error getting activity HR timezones: {error}",
        "❌ Erro ao obter fusos horários de frequência cardíaca da atividade: {error}",
    ),
    (
        "activity_power_error",
        "❌ Error getting activity power timezones: {error}",
        "❌ Erro ao obter fusos horários de potência da atividade: {error}",
    ),
    (
        "activity_details_error",
        "❌ Error getting activity details: {error}",
        "❌ Erro ao obter detalhes da atividade: {error}",
    ),
    (
        "activity_gear_error",
        "❌ Error getting activity gear: {error}",
        "❌ Erro ao obter equipamento da atividade: {error}",
    ),
    (
        "single_activity_error",
        "❌ Error getting single activity: {error}",
        "❌ Erro ao obter atividade: {error}",
    ),
    (
        "golf_scorecard_error",
        "❌ Error getting golf scorecard: {error}",
        "❌ Erro ao obter cartão de golfe: {error}",
    ),
    (
        "golf_shot_error",
        "❌ Error getting golf shot data: {error}",
        "❌ Erro ao obter dados das tacadas de golfe: {error}",
    ),
    (
        "workout_by_id_error",
        "❌ Error getting workout by ID: {error}",
        "❌ Erro ao obter treino pelo ID: {error}",
    ),
    (
        "running_upload_error",
        "❌ Error uploading running workout: {error}",
        "❌ Erro ao enviar treino de corrida: {error}",
    ),
    (
        "cycling_upload_error",
        "❌ Error uploading cycling workout: {error}",
        "❌ Erro ao enviar treino de ciclismo: {error}",
    ),
    (
        "swimming_upload_error",
        "❌ Error uploading swimming workout: {error}",
        "❌ Erro ao enviar treino de natação: {error}",
    ),
    (
        "walking_upload_error",
        "❌ Error uploading walking workout: {error}",
        "❌ Erro ao enviar treino de caminhada: {error}",
    ),
    (
        "hiking_upload_error",
        "❌ Error uploading hiking workout: {error}",
        "❌ Erro ao enviar treino de trilha: {error}",
    ),
    (
        "strength_upload_error",
        "❌ Error uploading strength workout: {error}",
        "❌ Erro ao enviar treino de força: {error}",
    ),
    ("generic_error", "❌ Error: {error}", "❌ Erro: {error}"),
    (
        "json_error",
        "❌ Invalid JSON format in {path}: {error}",
        "❌ Formato JSON inválido em {path}: {error}",
    ),
    (
        "schedule_error",
        "❌ Error scheduling workout: {error}",
        "❌ Erro ao agendar treino: {error}",
    ),
    (
        "scheduled_by_month_error",
        "❌ Error getting scheduled workouts by year and month: {error}",
        "❌ Erro ao obter treinos agendados por ano e mês: {error}",
    ),
    (
        "next_workout_error",
        "❌ Error getting next scheduled workout: {error}",
        "❌ Erro ao obter o próximo treino agendado: {error}",
    ),
    (
        "scheduled_by_id_error",
        "❌ Error getting scheduled workout by ID: {error}",
        "❌ Erro ao obter treino agendado pelo ID: {error}",
    ),
    (
        "push_error",
        "❌ Error pushing workout to device: {error}",
        "❌ Erro ao enviar treino ao dispositivo: {error}",
    ),
    (
        "unschedule_error",
        "❌ Error unscheduling workout: {error}",
        "❌ Erro ao desagendar treino: {error}",
    ),
    (
        "device_settings_error",
        "❌ Error getting device settings: {error}",
        "❌ Erro ao obter configurações do dispositivo: {error}",
    ),
    (
        "activity_type_row",
        "{index}: {type_key} - {display}",
        "{index}: {type_key} - {display}",
    ),
    ("login_error", "\n❌ {error}", "\n❌ {error}"),
    ("download_success", "  ✅ {format}: {filename}", "  ✅ {format}: {filename}"),
):
    _MESSAGES[f"ui.{_message_name}"] = (_english, _portuguese)


_MESSAGES.update(
    {
        "ui.category_header": (
            "\n📋 #{category_key} {category_name} - Options",
            "\n📋 #{category_key} {category_name} - Opções",
        ),
        "demo.api_method_header": (
            "\n📋 {call}",
            "\n📋 {call}",
        ),
        "demo.graphql_example": (
            "Example: query{{userGoalsScalar}}",
            "Exemplo: query{{userGoalsScalar}}",
        ),
        "demo.training_plan_id": (
            "Enter training plan ID: ",
            "Digite o ID do plano de treino: ",
        ),
        "demo.training_plan_id_recent": (
            "Enter training plan ID (press Enter for most recent): ",
            "Digite o ID do plano de treino (pressione Enter para usar o mais recente): ",
        ),
        "demo.activity_count": (
            "Found {count} activities.",
            "{count} atividades encontradas.",
        ),
        "demo.activity_gear_row": (
            "Activity: {start_time}{activity_name}",
            "Atividade: {start_time}{activity_name}",
        ),
        "demo.activity_gear_duration": (
            "  Duration: {duration}",
            "  Duração: {duration}",
        ),
        "demo.total_duration": (
            "Total Duration: {duration}",
            "Duração total: {duration}",
        ),
        "report.title": (
            "Garmin Health Report - {user}",
            "Relatório de Saúde da Garmin - {user}",
        ),
        "report.heading": ("Garmin Health Report", "Relatório de Saúde da Garmin"),
        "report.generated": ("Generated:", "Gerado:"),
        "report.date": ("Date:", "Data:"),
        "report.today_activity_summary": (
            "Today's Activity Summary",
            "Resumo da Atividade de Hoje",
        ),
        "report.steps": ("Steps", "Passos"),
        "report.steps_unit": ("steps", "passos"),
        "report.calories": ("Calories", "Calorias"),
        "report.total": ("total", "total"),
        "report.active": ("active", "ativos"),
        "report.distance": ("Distance", "Distância"),
        "report.no_activity_today": (
            "No activity data available for today",
            "Nenhum dado de atividade disponível para hoje",
        ),
        "report.health_metrics": ("Health Metrics", "Métricas de Saúde"),
        "report.heart_rate": ("Heart Rate", "Frequência Cardíaca"),
        "report.resting_bpm": ("bpm (resting)", "bpm (em repouso)"),
        "report.max": ("Max:", "Máx.:"),
        "report.sleep": ("Sleep", "Sono"),
        "report.hours": ("hours", "horas"),
        "report.deep_sleep": ("Deep Sleep:", "Sono Profundo:"),
        "report.step_goal": ("Step Goal", "Meta de Passos"),
        "report.of": ("of", "de"),
        "report.goal": ("Goal:", "Meta:"),
        "report.stress_level": ("Stress Level", "Nível de Estresse"),
        "report.avg": ("avg", "média"),
        "report.body_battery": ("Body Battery", "Body Battery"),
        "report.charged": ("charged", "carregado"),
        "report.drained": ("drained", "drenado"),
        "report.no_health_metrics": (
            "No health metrics data available",
            "Nenhum dado de métricas de saúde disponível",
        ),
        "report.weekly_trends": (
            "Weekly Trends (Last 7 Days)",
            "Tendências Semanais (Últimos 7 Dias)",
        ),
        "report.recent_activities": (
            "Recent Activities",
            "Atividades Recentes",
        ),
        "report.no_recent_activities": (
            "No recent activities found",
            "Nenhuma atividade recente encontrada",
        ),
        "report.duration": ("Duration:", "Duração:"),
        "report.avg_hr": ("Avg HR:", "FC Média:"),
        "report.device_information": (
            "Device Information",
            "Informações do Dispositivo",
        ),
        "report.model": ("Model:", "Modelo:"),
        "report.software": ("Software:", "Software:"),
        "report.footer_generated": (
            "Generated by Garmin Connect API Demo on {timestamp}",
            "Gerado pelo Demo da API do Garmin Connect em {timestamp}",
        ),
        "report.footer_disclaimer": (
            "This report is for informational purposes only. Consult healthcare professionals for medical advice.",
            "Este relatório é apenas informativo. Consulte profissionais de saúde para obter orientação médica.",
        ),
        "report.unknown_user": ("Unknown User", "Usuário Desconhecido"),
        "report.unknown": ("Unknown", "Desconhecido"),
        "report.unknown_activity": (
            "Unknown Activity",
            "Atividade Desconhecida",
        ),
        "report.unknown_device": ("Unknown Device", "Dispositivo Desconhecido"),
        "report.unknown_model": ("Unknown Model", "Modelo Desconhecido"),
        "report.not_available": ("N/A", "N/D"),
        "error.endpoint_not_found": (
            "Endpoint not found (404) - This feature may have been moved or removed",
            "Endpoint não encontrado (404) — Este recurso pode ter sido movido ou removido",
        ),
        "error.endpoint_not_available": (
            "Endpoint not available (400 Bad Request) - This feature may not be enabled for your account or region",
            "Endpoint indisponível (400 — requisição inválida) — Este recurso pode não estar habilitado para sua conta ou região",
        ),
        "error.authentication_required": (
            "Authentication required (401 Unauthorized) - Please re-authenticate",
            "Autenticação necessária (401 — não autorizado) — Faça a autenticação novamente",
        ),
        "error.access_denied": (
            "Access denied (403 Forbidden) - Your account may not have permission for this feature",
            "Acesso negado (403 — proibido) — Sua conta pode não ter permissão para este recurso",
        ),
        "error.resource_unavailable": (
            "Resource no longer available (410 Gone) - This data does not exist or the endpoint has been retired",
            "Recurso não está mais disponível (410 — removido) — Esses dados não existem ou o endpoint foi desativado",
        ),
        "error.rate_limit_exceeded": (
            "Rate limit exceeded (429) - Please wait before making more requests",
            "Limite de requisições excedido (429) — Aguarde antes de fazer novas solicitações",
        ),
        "error.server_error": (
            "Server error (500) - Garmin's servers are experiencing issues",
            "Erro do servidor (500) — Os servidores da Garmin estão apresentando problemas",
        ),
        "error.service_unavailable": (
            "Service unavailable (503) - Garmin's servers are temporarily unavailable",
            "Serviço indisponível (503) — Os servidores da Garmin estão temporariamente indisponíveis",
        ),
        "error.http": ("HTTP error: {error}", "Erro HTTP: {error}"),
        "error.authentication_issue": (
            "Authentication issue: {error}",
            "Problema de autenticação: {error}",
        ),
        "error.connection_issue": (
            "Connection issue: {error}",
            "Problema de conexão: {error}",
        ),
        "error.unexpected": (
            "Unexpected error: {error}",
            "Erro inesperado: {error}",
        ),
    }
)


_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {key: english for key, (english, _portuguese) in _MESSAGES.items()},
    "pt-BR": {
        key: portuguese or english for key, (english, portuguese) in _MESSAGES.items()
    },
}
SUPPORTED_LANGUAGES = tuple(_TRANSLATIONS)
_LANGUAGE_ALIASES = {
    "en": "en",
    "pt-br": "pt-BR",
}


_LANGUAGE_STATE = {"current": "en"}


def normalize_language(language: str) -> str:
    """Normalize a language tag and return its canonical supported value."""
    normalized = language.strip().replace("_", "-").split(".", 1)[0].casefold()
    canonical = _LANGUAGE_ALIASES.get(normalized)
    if canonical is not None:
        return canonical
    raise UnsupportedLanguageError(
        f"Unsupported language: {language}\n"
        f"Available languages: {', '.join(SUPPORTED_LANGUAGES)}"
    )


def resolve_language(
    cli_language: str | None = None,
    env: str | None = None,
    persisted: str | None = None,
) -> str:
    """Resolve CLI, environment, persisted, and default language in order."""
    for requested in (cli_language, env, persisted):
        if requested:
            return normalize_language(requested)
    return "en"


def set_language(language: str) -> str:
    """Set the active interface language and return its canonical tag."""
    canonical = normalize_language(language)
    _LANGUAGE_STATE["current"] = canonical
    return canonical


def get_language() -> str:
    """Return the active interface language."""
    return _LANGUAGE_STATE["current"]


def translate(message_key: str, locale: str | None = None, **values: Any) -> str:
    """Translate a catalog key, formatting named dynamic values safely."""
    source = _TRANSLATIONS["en"].get(message_key)
    if source is None:
        return message_key
    active = normalize_language(locale) if locale else get_language()
    target = _TRANSLATIONS[active].get(message_key, source)
    return target.format(**values) if values else target


def configure_from_environment() -> str:
    """Select the language from ``GARMIN_LANG`` or deterministic English."""
    return set_language(resolve_language(env=os.getenv("GARMIN_LANG")))
