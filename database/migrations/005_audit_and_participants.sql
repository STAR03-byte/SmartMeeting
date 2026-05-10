-- SmartMeeting 业务增强与审计脚本
-- 依赖: 001_init_smartmeeting.sql

-- ==========================================
-- 1) 会议参与人关系表
-- ==========================================
CREATE TABLE IF NOT EXISTS meeting_participants (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  meeting_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  participant_role VARCHAR(20) NOT NULL DEFAULT 'required'
    CHECK (participant_role IN ('owner', 'required', 'optional')),
  attendance_status VARCHAR(20) NOT NULL DEFAULT 'invited'
    CHECK (attendance_status IN ('invited', 'accepted', 'declined', 'attended')),
  joined_at TIMESTAMP NULL,
  left_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uk_meeting_participants_unique UNIQUE (meeting_id, user_id),
  CONSTRAINT fk_meeting_participants_meeting_id
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_meeting_participants_user_id
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX idx_meeting_participants_user_status ON meeting_participants (user_id, attendance_status);

CREATE TRIGGER trg_meeting_participants_updated_at
  BEFORE UPDATE ON meeting_participants
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- ==========================================
-- 2) 审计日志表
-- ==========================================
CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_user_id BIGINT NULL,
  entity_type VARCHAR(64) NOT NULL
    CHECK (entity_type IN ('users', 'meetings', 'meeting_transcripts', 'tasks', 'meeting_participants')),
  entity_id BIGINT NOT NULL,
  action VARCHAR(32) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
  before_data JSONB NULL,
  after_data JSONB NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_actor_user_id
    FOREIGN KEY (actor_user_id) REFERENCES users(id)
    ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX idx_audit_entity ON audit_logs (entity_type, entity_id, created_at);
CREATE INDEX idx_audit_actor ON audit_logs (actor_user_id, created_at);


-- ==========================================
-- 3) 会议与任务审计触发器
-- ==========================================

-- meetings 审计函数
CREATE OR REPLACE FUNCTION fn_audit_meetings()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
    VALUES (NULL, 'meetings', NEW.id, 'INSERT', NULL,
      jsonb_build_object(
        'title', NEW.title,
        'organizer_id', NEW.organizer_id,
        'status', NEW.status,
        'scheduled_start_at', NEW.scheduled_start_at,
        'scheduled_end_at', NEW.scheduled_end_at
      ));
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
    VALUES (NULL, 'meetings', NEW.id, 'UPDATE',
      jsonb_build_object(
        'title', OLD.title,
        'organizer_id', OLD.organizer_id,
        'status', OLD.status,
        'scheduled_start_at', OLD.scheduled_start_at,
        'scheduled_end_at', OLD.scheduled_end_at
      ),
      jsonb_build_object(
        'title', NEW.title,
        'organizer_id', NEW.organizer_id,
        'status', NEW.status,
        'scheduled_start_at', NEW.scheduled_start_at,
        'scheduled_end_at', NEW.scheduled_end_at
      ));
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
    VALUES (NULL, 'meetings', OLD.id, 'DELETE',
      jsonb_build_object(
        'title', OLD.title,
        'organizer_id', OLD.organizer_id,
        'status', OLD.status,
        'scheduled_start_at', OLD.scheduled_start_at,
        'scheduled_end_at', OLD.scheduled_end_at
      ), NULL);
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_meetings
  AFTER INSERT OR UPDATE OR DELETE ON meetings
  FOR EACH ROW EXECUTE FUNCTION fn_audit_meetings();


-- tasks 审计函数
CREATE OR REPLACE FUNCTION fn_audit_tasks()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
    VALUES (NULL, 'tasks', NEW.id, 'INSERT', NULL,
      jsonb_build_object(
        'meeting_id', NEW.meeting_id,
        'title', NEW.title,
        'assignee_id', NEW.assignee_id,
        'priority', NEW.priority,
        'status', NEW.status,
        'due_at', NEW.due_at
      ));
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
    VALUES (NULL, 'tasks', NEW.id, 'UPDATE',
      jsonb_build_object(
        'meeting_id', OLD.meeting_id,
        'title', OLD.title,
        'assignee_id', OLD.assignee_id,
        'priority', OLD.priority,
        'status', OLD.status,
        'due_at', OLD.due_at
      ),
      jsonb_build_object(
        'meeting_id', NEW.meeting_id,
        'title', NEW.title,
        'assignee_id', NEW.assignee_id,
        'priority', NEW.priority,
        'status', NEW.status,
        'due_at', NEW.due_at
      ));
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_data, after_data)
    VALUES (NULL, 'tasks', OLD.id, 'DELETE',
      jsonb_build_object(
        'meeting_id', OLD.meeting_id,
        'title', OLD.title,
        'assignee_id', OLD.assignee_id,
        'priority', OLD.priority,
        'status', OLD.status,
        'due_at', OLD.due_at
      ), NULL);
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_tasks
  AFTER INSERT OR UPDATE OR DELETE ON tasks
  FOR EACH ROW EXECUTE FUNCTION fn_audit_tasks();
