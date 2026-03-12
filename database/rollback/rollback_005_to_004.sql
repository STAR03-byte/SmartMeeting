-- 回滚 005_audit_and_participants.sql

USE smartmeeting;

DROP TRIGGER IF EXISTS trg_audit_tasks_delete;
DROP TRIGGER IF EXISTS trg_audit_tasks_update;
DROP TRIGGER IF EXISTS trg_audit_tasks_insert;
DROP TRIGGER IF EXISTS trg_audit_meetings_delete;
DROP TRIGGER IF EXISTS trg_audit_meetings_update;
DROP TRIGGER IF EXISTS trg_audit_meetings_insert;

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS meeting_participants;
