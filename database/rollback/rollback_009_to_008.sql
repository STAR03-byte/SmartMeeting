-- 回滚 CHECK 约束到 005 的原始定义
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_entity_type_check;
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_action_check;

ALTER TABLE audit_logs
  ADD CONSTRAINT audit_logs_entity_type_check
    CHECK (entity_type IN ('users', 'meetings', 'meeting_transcripts', 'tasks', 'meeting_participants')),
  ADD CONSTRAINT audit_logs_action_check
    CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'));
