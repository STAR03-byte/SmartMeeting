-- SmartMeeting 存储过程: 任务查询
-- 依赖: 001_init_smartmeeting.sql, 002_enhance_smartmeeting.sql

CREATE OR REPLACE FUNCTION sp_list_tasks_by_user(
  p_user_id BIGINT,
  p_status VARCHAR(20)
)
RETURNS TABLE (
  id BIGINT,
  title VARCHAR(200),
  description TEXT,
  priority VARCHAR(20),
  status VARCHAR(20),
  due_at TIMESTAMP,
  completed_at TIMESTAMP,
  meeting_id BIGINT,
  meeting_title VARCHAR(200),
  assignee_id BIGINT,
  reporter_id BIGINT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    t.id,
    t.title,
    t.description,
    t.priority,
    t.status,
    t.due_at,
    t.completed_at,
    t.meeting_id,
    m.title AS meeting_title,
    t.assignee_id,
    t.reporter_id,
    t.created_at,
    t.updated_at
  FROM tasks t
  JOIN meetings m ON m.id = t.meeting_id
  WHERE t.assignee_id = p_user_id
    AND (p_status IS NULL OR p_status = '' OR t.status = p_status)
  ORDER BY
    CASE t.priority
      WHEN 'urgent' THEN 1
      WHEN 'high' THEN 2
      WHEN 'medium' THEN 3
      ELSE 4
    END,
    t.due_at ASC NULLS LAST,
    t.id DESC;
END;
$$ LANGUAGE plpgsql;
