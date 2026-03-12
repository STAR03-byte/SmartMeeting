-- 回滚 004_indexes_perf.sql

USE smartmeeting;

DROP PROCEDURE IF EXISTS sp_drop_index_if_exists;

DELIMITER $$
CREATE PROCEDURE sp_drop_index_if_exists(
  IN p_table_name VARCHAR(64),
  IN p_index_name VARCHAR(64)
)
BEGIN
  DECLARE v_exists INT DEFAULT 0;

  SELECT COUNT(1)
    INTO v_exists
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = p_table_name
    AND index_name = p_index_name;

  IF v_exists > 0 THEN
    SET @ddl = CONCAT('DROP INDEX ', p_index_name, ' ON ', p_table_name);
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END$$
DELIMITER ;

CALL sp_drop_index_if_exists('users', 'idx_users_active_role');

CALL sp_drop_index_if_exists('meetings', 'idx_meetings_status_start');
CALL sp_drop_index_if_exists('meetings', 'idx_meetings_organizer_created');

CALL sp_drop_index_if_exists('meeting_transcripts', 'idx_transcripts_meeting_created');
CALL sp_drop_index_if_exists('meeting_transcripts', 'idx_transcripts_meeting_time');

CALL sp_drop_index_if_exists('tasks', 'idx_tasks_assignee_status_due');
CALL sp_drop_index_if_exists('tasks', 'idx_tasks_meeting_status_priority');
CALL sp_drop_index_if_exists('tasks', 'idx_tasks_status_priority_due');
CALL sp_drop_index_if_exists('tasks', 'idx_tasks_reporter_created');

DROP PROCEDURE IF EXISTS sp_drop_index_if_exists;
