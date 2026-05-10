-- SmartMeeting 一键初始化数据库 (PostgreSQL)
-- 使用方法: psql -f scripts/db/run_all.sql

\i database/migrations/001_init_smartmeeting.sql
\i database/migrations/002_enhance_smartmeeting.sql
\i database/migrations/003_sp_task_query.sql
\i database/migrations/004_indexes_perf.sql
\i database/migrations/005_audit_and_participants.sql
\i database/migrations/006_collaboration_share_fields.sql
\i database/migrations/007_fix_meeting_audio_cascade.sql
\i database/migrations/008_participant_unique_guard.sql
\i database/migrations/009_extend_audit_logs_for_auth_events.sql
\i database/migrations/010_speaker_fields.sql
\i database/migrations/011_hotwords_table.sql
\i database/migrations/012_create_teams.sql
\i database/migrations/013_create_team_members.sql
\i database/migrations/014_add_team_id_to_meetings.sql
\i database/migrations/015_add_role_to_participants.sql
\i database/migrations/016_clear_test_data.sql
\i database/migrations/018_create_team_invite_links.sql
\i database/migrations/019_add_task_reminder_at.sql
\i database/migrations/020_create_team_invitations.sql
\i database/migrations/021_create_conversations.sql
\i database/migrations/022_create_conversation_messages.sql
\i database/migrations/023_meeting_share_lifecycle.sql
\i database/migrations/024_create_processing_jobs.sql
\i database/migrations/025_create_llm_usage.sql
\i database/migrations/027_fix_hotwords_user_id_type.sql
\i database/migrations/028_create_meeting_audios.sql
\i database/migrations/029_fix_team_tables_types.sql
\i database/migrations/030_add_tsvector_columns.sql

\i database/seeds/001_seed_basic_data.sql
\i database/seeds/002_seed_participants.sql
