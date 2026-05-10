-- 回滚 004_indexes_perf.sql

DROP INDEX IF EXISTS idx_users_active_role;
DROP INDEX IF EXISTS idx_meetings_status_start;
DROP INDEX IF EXISTS idx_meetings_organizer_created;
DROP INDEX IF EXISTS idx_transcripts_meeting_created;
DROP INDEX IF EXISTS idx_transcripts_meeting_time;
DROP INDEX IF EXISTS idx_tasks_assignee_status_due;
DROP INDEX IF EXISTS idx_tasks_meeting_status_priority;
DROP INDEX IF EXISTS idx_tasks_status_priority_due;
DROP INDEX IF EXISTS idx_tasks_reporter_created;
