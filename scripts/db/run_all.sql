-- SmartMeeting 一键初始化数据库

SOURCE database/migrations/001_init_smartmeeting.sql;
SOURCE database/migrations/002_enhance_smartmeeting.sql;
SOURCE database/migrations/003_sp_task_query.sql;
SOURCE database/migrations/004_indexes_perf.sql;
SOURCE database/migrations/005_audit_and_participants.sql;
SOURCE database/migrations/006_collaboration_share_fields.sql;
SOURCE database/migrations/006_meeting_share_links.sql;
SOURCE database/migrations/007_fix_meeting_audio_cascade.sql;

SOURCE database/seeds/001_seed_basic_data.sql;
SOURCE database/seeds/002_seed_participants.sql;
