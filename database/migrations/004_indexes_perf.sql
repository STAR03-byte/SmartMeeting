-- SmartMeeting 性能索引增强脚本
-- 依赖: 001_init_smartmeeting.sql
-- 建议执行顺序: 001 -> 002 -> 003 -> 004

-- PostgreSQL 使用 CREATE INDEX IF NOT EXISTS，无需存储过程

-- users: 管理后台常见筛选(是否启用 + 角色)
CREATE INDEX IF NOT EXISTS idx_users_active_role ON users (is_active, role);

-- meetings: 会议列表/日程查询常见组合
CREATE INDEX IF NOT EXISTS idx_meetings_status_start ON meetings (status, scheduled_start_at);
CREATE INDEX IF NOT EXISTS idx_meetings_organizer_created ON meetings (organizer_id, created_at);

-- meeting_transcripts: 会议转写按会议与时间读取
CREATE INDEX IF NOT EXISTS idx_transcripts_meeting_created ON meeting_transcripts (meeting_id, created_at);
CREATE INDEX IF NOT EXISTS idx_transcripts_meeting_time ON meeting_transcripts (meeting_id, start_time_sec, end_time_sec);

-- tasks: 任务看板/我的任务/会议任务高频场景
CREATE INDEX IF NOT EXISTS idx_tasks_assignee_status_due ON tasks (assignee_id, status, due_at);
CREATE INDEX IF NOT EXISTS idx_tasks_meeting_status_priority ON tasks (meeting_id, status, priority);
CREATE INDEX IF NOT EXISTS idx_tasks_status_priority_due ON tasks (status, priority, due_at);
CREATE INDEX IF NOT EXISTS idx_tasks_reporter_created ON tasks (reporter_id, created_at);
