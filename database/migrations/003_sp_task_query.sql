-- SmartMeeting 存储过程: 任务查询
-- 依赖: 001_init_smartmeeting.sql, 002_enhance_smartmeeting.sql

USE smartmeeting;

DROP PROCEDURE IF EXISTS sp_list_tasks_by_user;

DELIMITER $$
CREATE PROCEDURE sp_list_tasks_by_user(
  IN p_user_id BIGINT UNSIGNED,
  IN p_status VARCHAR(20)
)
BEGIN
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
    t.due_at ASC,
    t.id DESC;
END$$
DELIMITER ;
