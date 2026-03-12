-- SmartMeeting 业务增强与审计脚本
-- 依赖: 001_init_smartmeeting.sql

USE smartmeeting;

-- ==========================================
-- 1) 会议参与人关系表（替代文本 participants 的结构化能力）
-- ==========================================
CREATE TABLE IF NOT EXISTS meeting_participants (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  meeting_id BIGINT UNSIGNED NOT NULL COMMENT '会议ID',
  user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  participant_role ENUM('owner', 'required', 'optional') NOT NULL DEFAULT 'required' COMMENT '参会角色',
  attendance_status ENUM('invited', 'accepted', 'declined', 'attended') NOT NULL DEFAULT 'invited' COMMENT '参会状态',
  joined_at DATETIME NULL COMMENT '加入时间',
  left_at DATETIME NULL COMMENT '离开时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_meeting_participants_unique (meeting_id, user_id),
  KEY idx_meeting_participants_user_status (user_id, attendance_status),
  CONSTRAINT fk_meeting_participants_meeting_id
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_meeting_participants_user_id
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议参与人关系表';


-- ==========================================
-- 2) 审计日志表
-- ==========================================
CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '审计日志ID',
  actor_user_id BIGINT UNSIGNED NULL COMMENT '操作者用户ID(系统操作可为空)',
  entity_type ENUM('users', 'meetings', 'meeting_transcripts', 'tasks', 'meeting_participants') NOT NULL COMMENT '实体类型',
  entity_id BIGINT UNSIGNED NOT NULL COMMENT '实体ID',
  action ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL COMMENT '动作',
  before_data JSON NULL COMMENT '变更前数据',
  after_data JSON NULL COMMENT '变更后数据',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_audit_entity (entity_type, entity_id, created_at),
  KEY idx_audit_actor (actor_user_id, created_at),
  CONSTRAINT fk_audit_actor_user_id
    FOREIGN KEY (actor_user_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表';


-- ==========================================
-- 3) 会议与任务审计触发器
-- 说明: actor_user_id 预留, 当前置为 NULL（后续可结合会话上下文变量注入）
-- ==========================================
DROP TRIGGER IF EXISTS trg_audit_meetings_insert;
DROP TRIGGER IF EXISTS trg_audit_meetings_update;
DROP TRIGGER IF EXISTS trg_audit_meetings_delete;
DROP TRIGGER IF EXISTS trg_audit_tasks_insert;
DROP TRIGGER IF EXISTS trg_audit_tasks_update;
DROP TRIGGER IF EXISTS trg_audit_tasks_delete;

DELIMITER $$

CREATE TRIGGER trg_audit_meetings_insert
AFTER INSERT ON meetings
FOR EACH ROW
BEGIN
  INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
  VALUES (
    NULL,
    'meetings',
    NEW.id,
    'INSERT',
    NULL,
    JSON_OBJECT(
      'title', NEW.title,
      'organizer_id', NEW.organizer_id,
      'status', NEW.status,
      'scheduled_start_at', NEW.scheduled_start_at,
      'scheduled_end_at', NEW.scheduled_end_at
    )
  );
END$$

CREATE TRIGGER trg_audit_meetings_update
AFTER UPDATE ON meetings
FOR EACH ROW
BEGIN
  INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
  VALUES (
    NULL,
    'meetings',
    NEW.id,
    'UPDATE',
    JSON_OBJECT(
      'title', OLD.title,
      'organizer_id', OLD.organizer_id,
      'status', OLD.status,
      'scheduled_start_at', OLD.scheduled_start_at,
      'scheduled_end_at', OLD.scheduled_end_at
    ),
    JSON_OBJECT(
      'title', NEW.title,
      'organizer_id', NEW.organizer_id,
      'status', NEW.status,
      'scheduled_start_at', NEW.scheduled_start_at,
      'scheduled_end_at', NEW.scheduled_end_at
    )
  );
END$$

CREATE TRIGGER trg_audit_meetings_delete
AFTER DELETE ON meetings
FOR EACH ROW
BEGIN
  INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
  VALUES (
    NULL,
    'meetings',
    OLD.id,
    'DELETE',
    JSON_OBJECT(
      'title', OLD.title,
      'organizer_id', OLD.organizer_id,
      'status', OLD.status,
      'scheduled_start_at', OLD.scheduled_start_at,
      'scheduled_end_at', OLD.scheduled_end_at
    ),
    NULL
  );
END$$

CREATE TRIGGER trg_audit_tasks_insert
AFTER INSERT ON tasks
FOR EACH ROW
BEGIN
  INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
  VALUES (
    NULL,
    'tasks',
    NEW.id,
    'INSERT',
    NULL,
    JSON_OBJECT(
      'meeting_id', NEW.meeting_id,
      'title', NEW.title,
      'assignee_id', NEW.assignee_id,
      'priority', NEW.priority,
      'status', NEW.status,
      'due_at', NEW.due_at
    )
  );
END$$

CREATE TRIGGER trg_audit_tasks_update
AFTER UPDATE ON tasks
FOR EACH ROW
BEGIN
  INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
  VALUES (
    NULL,
    'tasks',
    NEW.id,
    'UPDATE',
    JSON_OBJECT(
      'meeting_id', OLD.meeting_id,
      'title', OLD.title,
      'assignee_id', OLD.assignee_id,
      'priority', OLD.priority,
      'status', OLD.status,
      'due_at', OLD.due_at
    ),
    JSON_OBJECT(
      'meeting_id', NEW.meeting_id,
      'title', NEW.title,
      'assignee_id', NEW.assignee_id,
      'priority', NEW.priority,
      'status', NEW.status,
      'due_at', NEW.due_at
    )
  );
END$$

CREATE TRIGGER trg_audit_tasks_delete
AFTER DELETE ON tasks
FOR EACH ROW
BEGIN
  INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
  VALUES (
    NULL,
    'tasks',
    OLD.id,
    'DELETE',
    JSON_OBJECT(
      'meeting_id', OLD.meeting_id,
      'title', OLD.title,
      'assignee_id', OLD.assignee_id,
      'priority', OLD.priority,
      'status', OLD.status,
      'due_at', OLD.due_at
    ),
    NULL
  );
END$$

DELIMITER ;
