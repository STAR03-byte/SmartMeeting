-- SmartMeeting PostgreSQL Schema
-- 说明: 包含用户、会议、会议转写、任务四张核心表

-- ==========================================
-- 0) updated_at 自动维护函数（全局复用）
-- ==========================================
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 1) users
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(120) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  last_login_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uk_users_username UNIQUE (username),
  CONSTRAINT uk_users_email UNIQUE (email)
);

CREATE INDEX idx_users_role ON users (role);

CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- ==========================================
-- 2) meetings
-- ==========================================
CREATE TABLE IF NOT EXISTS meetings (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  organizer_id BIGINT NOT NULL,
  scheduled_start_at TIMESTAMP NULL,
  scheduled_end_at TIMESTAMP NULL,
  actual_start_at TIMESTAMP NULL,
  actual_end_at TIMESTAMP NULL,
  location VARCHAR(255) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'ongoing', 'done', 'cancelled')),
  summary TEXT NULL,
  postprocessed_at TIMESTAMP NULL,
  postprocess_version VARCHAR(32) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_meetings_organizer_id
    FOREIGN KEY (organizer_id) REFERENCES users(id)
    ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX idx_meetings_organizer_id ON meetings (organizer_id);
CREATE INDEX idx_meetings_status ON meetings (status);
CREATE INDEX idx_meetings_scheduled_start_at ON meetings (scheduled_start_at);

CREATE TRIGGER trg_meetings_updated_at
  BEFORE UPDATE ON meetings
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- ==========================================
-- 3) meeting_transcripts
-- ==========================================
CREATE TABLE IF NOT EXISTS meeting_transcripts (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  meeting_id BIGINT NOT NULL,
  speaker_user_id BIGINT NULL,
  speaker_name VARCHAR(100) NULL,
  segment_index INTEGER NOT NULL,
  start_time_sec DECIMAL(10,3) NULL,
  end_time_sec DECIMAL(10,3) NULL,
  language_code VARCHAR(10) NOT NULL DEFAULT 'zh-CN',
  source VARCHAR(20) NOT NULL DEFAULT 'whisper' CHECK (source IN ('whisper', 'manual', 'imported')),
  content TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uk_transcripts_meeting_segment UNIQUE (meeting_id, segment_index),
  CONSTRAINT fk_transcripts_meeting_id
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_transcripts_speaker_user_id
    FOREIGN KEY (speaker_user_id) REFERENCES users(id)
    ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX idx_transcripts_meeting_id ON meeting_transcripts (meeting_id);
CREATE INDEX idx_transcripts_speaker_user_id ON meeting_transcripts (speaker_user_id);

CREATE TRIGGER trg_meeting_transcripts_updated_at
  BEFORE UPDATE ON meeting_transcripts
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- ==========================================
-- 4) tasks
-- ==========================================
CREATE TABLE IF NOT EXISTS tasks (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  meeting_id BIGINT NOT NULL,
  transcript_id BIGINT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  assignee_id BIGINT NULL,
  reporter_id BIGINT NULL,
  priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low')),
  status VARCHAR(20) NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'done')),
  due_at TIMESTAMP NULL,
  completed_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tasks_meeting_id
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_tasks_transcript_id
    FOREIGN KEY (transcript_id) REFERENCES meeting_transcripts(id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_tasks_assignee_id
    FOREIGN KEY (assignee_id) REFERENCES users(id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_tasks_reporter_id
    FOREIGN KEY (reporter_id) REFERENCES users(id)
    ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX idx_tasks_meeting_id ON tasks (meeting_id);
CREATE INDEX idx_tasks_transcript_id ON tasks (transcript_id);
CREATE INDEX idx_tasks_assignee_id ON tasks (assignee_id);
CREATE INDEX idx_tasks_reporter_id ON tasks (reporter_id);
CREATE INDEX idx_tasks_status ON tasks (status);
CREATE INDEX idx_tasks_due_at ON tasks (due_at);

CREATE TRIGGER trg_tasks_updated_at
  BEFORE UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
