-- 回滚 002_enhance_smartmeeting.sql

USE smartmeeting;

DROP TRIGGER IF EXISTS trg_tasks_set_completed_at;

DROP VIEW IF EXISTS v_task_detail;
DROP VIEW IF EXISTS v_meeting_overview;

DROP PROCEDURE IF EXISTS sp_drop_constraint_if_exists;

DELIMITER $$
CREATE PROCEDURE sp_drop_constraint_if_exists(
  IN p_table_name VARCHAR(64),
  IN p_constraint_name VARCHAR(64)
)
BEGIN
  DECLARE v_exists INT DEFAULT 0;

  SELECT COUNT(1)
    INTO v_exists
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = p_table_name
    AND constraint_name = p_constraint_name
    AND constraint_type = 'CHECK';

  IF v_exists > 0 THEN
    SET @ddl = CONCAT(
      'ALTER TABLE ', p_table_name,
      ' DROP CHECK ', p_constraint_name
    );
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END$$
DELIMITER ;

CALL sp_drop_constraint_if_exists('tasks', 'chk_tasks_due_after_create');
CALL sp_drop_constraint_if_exists('tasks', 'chk_tasks_complete_after_create');
CALL sp_drop_constraint_if_exists('meeting_transcripts', 'chk_transcript_time_range');
CALL sp_drop_constraint_if_exists('meetings', 'chk_meetings_time_range');
CALL sp_drop_constraint_if_exists('meetings', 'chk_meetings_actual_time_range');

DROP PROCEDURE IF EXISTS sp_drop_constraint_if_exists;
