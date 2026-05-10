-- 回滚 005_audit_and_participants.sql

DROP TRIGGER IF EXISTS trg_audit_tasks ON tasks;
DROP FUNCTION IF EXISTS fn_audit_tasks();
DROP TRIGGER IF EXISTS trg_audit_meetings ON meetings;
DROP FUNCTION IF EXISTS fn_audit_meetings();

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS meeting_participants;
