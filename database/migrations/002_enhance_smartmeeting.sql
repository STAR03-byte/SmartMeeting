-- SmartMeeting 数据库增强脚本
-- 依赖: 先执行 001_init_smartmeeting.sql

USE smartmeeting;

-- 1) 数据有效性约束（MySQL 8.0.16+ 支持 CHECK）
ALTER TABLE meetings
  ADD CONSTRAINT chk_meetings_time_range
    CHECK (
      scheduled_end_at IS NULL
      OR scheduled_start_at IS NULL
      OR scheduled_end_at >= scheduled_start_at
    ),
  ADD CONSTRAINT chk_meetings_actual_time_range
    CHECK (
      actual_end_at IS NULL
      OR actual_start_at IS NULL
      OR actual_end_at >= actual_start_at
    );

ALTER TABLE meeting_transcripts
  ADD CONSTRAINT chk_transcript_time_range
    CHECK (
      end_time_sec IS NULL
      OR start_time_sec IS NULL
      OR end_time_sec >= start_time_sec
    );

ALTER TABLE tasks
  ADD CONSTRAINT chk_tasks_due_after_create
    CHECK (due_at IS NULL OR due_at >= created_at),
  ADD CONSTRAINT chk_tasks_complete_after_create
    CHECK (completed_at IS NULL OR completed_at >= created_at);

-- 2) 聚合查询视图
CREATE OR REPLACE VIEW v_meeting_overview AS
SELECT
  m.id AS meeting_id,
  m.title,
  m.status AS meeting_status,
  m.organizer_id,
  u.full_name AS organizer_name,
  m.scheduled_start_at,
  m.scheduled_end_at,
  COUNT(DISTINCT mt.id) AS transcript_count,
  COUNT(DISTINCT t.id) AS task_count,
  SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) AS task_done_count,
  m.created_at,
  m.updated_at
FROM meetings m
JOIN users u ON u.id = m.organizer_id
LEFT JOIN meeting_transcripts mt ON mt.meeting_id = m.id
LEFT JOIN tasks t ON t.meeting_id = m.id
GROUP BY
  m.id,
  m.title,
  m.status,
  m.organizer_id,
  u.full_name,
  m.scheduled_start_at,
  m.scheduled_end_at,
  m.created_at,
  m.updated_at;

CREATE OR REPLACE VIEW v_task_detail AS
SELECT
  t.id AS task_id,
  t.title AS task_title,
  t.status AS task_status,
  t.priority,
  t.due_at,
  t.completed_at,
  t.meeting_id,
  m.title AS meeting_title,
  t.assignee_id,
  ua.full_name AS assignee_name,
  t.reporter_id,
  ur.full_name AS reporter_name,
  t.created_at,
  t.updated_at
FROM tasks t
JOIN meetings m ON m.id = t.meeting_id
LEFT JOIN users ua ON ua.id = t.assignee_id
LEFT JOIN users ur ON ur.id = t.reporter_id;

-- 3) 任务状态自动维护 completed_at
DROP TRIGGER IF EXISTS trg_tasks_set_completed_at;

DELIMITER $$
CREATE TRIGGER trg_tasks_set_completed_at
BEFORE UPDATE ON tasks
FOR EACH ROW
BEGIN
  IF NEW.status = 'done' AND OLD.status <> 'done' AND NEW.completed_at IS NULL THEN
    SET NEW.completed_at = CURRENT_TIMESTAMP;
  END IF;

  IF NEW.status <> 'done' THEN
    SET NEW.completed_at = NULL;
  END IF;
END$$
DELIMITER ;
