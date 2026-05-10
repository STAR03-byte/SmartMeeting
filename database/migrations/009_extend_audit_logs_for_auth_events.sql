-- PostgreSQL 中 CHECK 约束需先删后加，以扩展 entity_type 枚举
-- 注意：迁移文件按序执行，此文件确保 entity_type 包含更多值

-- 先删除旧约束（如果存在）
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_entity_type_check;
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_action_check;

-- 重新添加（与 005 中定义一致，此处确保可重复执行）
ALTER TABLE audit_logs
  ADD CONSTRAINT audit_logs_entity_type_check
    CHECK (entity_type IN ('users', 'meetings', 'meeting_transcripts', 'tasks', 'meeting_participants')),
  ADD CONSTRAINT audit_logs_action_check
    CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'));
