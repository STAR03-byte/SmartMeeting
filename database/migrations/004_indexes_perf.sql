-- SmartMeeting 性能索引增强脚本
-- 依赖: 001_init_smartmeeting.sql
-- 建议执行顺序: 001 -> 002 -> 003 -> 004

USE smartmeeting;

-- 说明:
-- 1) 为高频查询场景增加复合索引，减少全表扫描。
-- 2) 通过 INFORMATION_SCHEMA 判断索引是否存在，确保脚本可重复执行。

DROP PROCEDURE IF EXISTS sp_add_index_if_not_exists;

DELIMITER $$
CREATE PROCEDURE sp_add_index_if_not_exists(
  IN p_table_name VARCHAR(64),
  IN p_index_name VARCHAR(64),
  IN p_index_sql TEXT
)
BEGIN
  DECLARE v_exists INT DEFAULT 0;

  SELECT COUNT(1)
    INTO v_exists
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = p_table_name
    AND index_name = p_index_name;

  IF v_exists = 0 THEN
    SET @ddl = p_index_sql;
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END$$
DELIMITER ;

-- users: 管理后台常见筛选(是否启用 + 角色)
CALL sp_add_index_if_not_exists(
  'users',
  'idx_users_active_role',
  'CREATE INDEX idx_users_active_role ON users (is_active, role)'
);

-- meetings: 会议列表/日程查询常见组合
CALL sp_add_index_if_not_exists(
  'meetings',
  'idx_meetings_status_start',
  'CREATE INDEX idx_meetings_status_start ON meetings (status, scheduled_start_at)'
);

CALL sp_add_index_if_not_exists(
  'meetings',
  'idx_meetings_organizer_created',
  'CREATE INDEX idx_meetings_organizer_created ON meetings (organizer_id, created_at)'
);

-- meeting_transcripts: 会议转写按会议与时间读取
CALL sp_add_index_if_not_exists(
  'meeting_transcripts',
  'idx_transcripts_meeting_created',
  'CREATE INDEX idx_transcripts_meeting_created ON meeting_transcripts (meeting_id, created_at)'
);

CALL sp_add_index_if_not_exists(
  'meeting_transcripts',
  'idx_transcripts_meeting_time',
  'CREATE INDEX idx_transcripts_meeting_time ON meeting_transcripts (meeting_id, start_time_sec, end_time_sec)'
);

-- tasks: 任务看板/我的任务/会议任务高频场景
CALL sp_add_index_if_not_exists(
  'tasks',
  'idx_tasks_assignee_status_due',
  'CREATE INDEX idx_tasks_assignee_status_due ON tasks (assignee_id, status, due_at)'
);

CALL sp_add_index_if_not_exists(
  'tasks',
  'idx_tasks_meeting_status_priority',
  'CREATE INDEX idx_tasks_meeting_status_priority ON tasks (meeting_id, status, priority)'
);

CALL sp_add_index_if_not_exists(
  'tasks',
  'idx_tasks_status_priority_due',
  'CREATE INDEX idx_tasks_status_priority_due ON tasks (status, priority, due_at)'
);

CALL sp_add_index_if_not_exists(
  'tasks',
  'idx_tasks_reporter_created',
  'CREATE INDEX idx_tasks_reporter_created ON tasks (reporter_id, created_at)'
);

-- 清理临时过程
DROP PROCEDURE IF EXISTS sp_add_index_if_not_exists;

-- 可选验证示例（执行时手动运行）:
-- EXPLAIN SELECT * FROM meetings
--   WHERE status = 'planned' ORDER BY scheduled_start_at DESC LIMIT 20;
--
-- EXPLAIN SELECT * FROM tasks
--   WHERE assignee_id = 4002 AND status IN ('todo','in_progress')
--   ORDER BY due_at ASC;
--
-- EXPLAIN SELECT * FROM meeting_transcripts
--   WHERE meeting_id = 3001 ORDER BY start_time_sec ASC;
