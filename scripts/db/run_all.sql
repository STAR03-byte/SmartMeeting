-- SmartMeeting 一键初始化数据库

SOURCE database/migrations/001_init_smartmeeting.sql;
SOURCE database/migrations/002_enhance_smartmeeting.sql;
SOURCE database/migrations/003_sp_task_query.sql;
SOURCE database/migrations/004_indexes_perf.sql;
SOURCE database/migrations/005_audit_and_participants.sql;
SOURCE database/migrations/006_collaboration_share_fields.sql;
SOURCE database/migrations/007_fix_meeting_audio_cascade.sql;
SOURCE database/migrations/008_participant_unique_guard.sql;
SOURCE database/migrations/009_extend_audit_logs_for_auth_events.sql;
SOURCE database/migrations/010_speaker_fields.sql;
SOURCE database/migrations/011_hotwords_table.sql;
SOURCE database/migrations/012_create_teams.sql;
SOURCE database/migrations/013_create_team_members.sql;
SOURCE database/migrations/014_add_team_id_to_meetings.sql;
SOURCE database/migrations/015_add_role_to_participants.sql;
SOURCE database/migrations/016_clear_test_data.sql;
SOURCE database/migrations/018_create_team_invite_links.sql;
SOURCE database/migrations/019_add_task_reminder_at.sql;
SOURCE database/migrations/020_create_team_invitations.sql;

SOURCE database/seeds/001_seed_basic_data.sql;
SOURCE database/seeds/002_seed_participants.sql;
