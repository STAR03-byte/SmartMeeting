-- 008 的约束在 PostgreSQL 版本中内联定义于 005
-- 回滚时删除唯一约束
ALTER TABLE meeting_participants DROP CONSTRAINT IF EXISTS uk_meeting_participants_unique;
