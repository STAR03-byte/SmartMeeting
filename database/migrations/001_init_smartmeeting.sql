-- SmartMeeting MySQL Schema
-- 说明: 包含用户、会议、会议转写、任务四张核心表

CREATE DATABASE IF NOT EXISTS smartmeeting
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smartmeeting;

-- ==========================================
-- 1) users
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  username VARCHAR(50) NOT NULL COMMENT '用户名',
  email VARCHAR(120) NOT NULL COMMENT '邮箱',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
  full_name VARCHAR(100) NOT NULL COMMENT '姓名',
  role ENUM('admin', 'member') NOT NULL DEFAULT 'member' COMMENT '角色',
  is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  last_login_at DATETIME NULL COMMENT '最后登录时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username),
  UNIQUE KEY uk_users_email (email),
  KEY idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';


-- ==========================================
-- 2) meetings
-- ==========================================
CREATE TABLE IF NOT EXISTS meetings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '会议ID',
  title VARCHAR(200) NOT NULL COMMENT '会议标题',
  description TEXT NULL COMMENT '会议描述',
  organizer_id BIGINT UNSIGNED NOT NULL COMMENT '组织者用户ID',
  scheduled_start_at DATETIME NULL COMMENT '计划开始时间',
  scheduled_end_at DATETIME NULL COMMENT '计划结束时间',
  actual_start_at DATETIME NULL COMMENT '实际开始时间',
  actual_end_at DATETIME NULL COMMENT '实际结束时间',
  location VARCHAR(255) NULL COMMENT '会议地点/链接',
  status ENUM('planned', 'ongoing', 'done', 'cancelled') NOT NULL DEFAULT 'planned' COMMENT '会议状态',
  summary TEXT NULL COMMENT '会议摘要',
  postprocessed_at DATETIME NULL COMMENT '后处理时间',
  postprocess_version VARCHAR(32) NULL COMMENT '后处理版本',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_meetings_organizer_id (organizer_id),
  KEY idx_meetings_status (status),
  KEY idx_meetings_scheduled_start_at (scheduled_start_at),
  CONSTRAINT fk_meetings_organizer_id
    FOREIGN KEY (organizer_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议表';


-- ==========================================
-- 3) meeting_transcripts
-- ==========================================
CREATE TABLE IF NOT EXISTS meeting_transcripts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '转写记录ID',
  meeting_id BIGINT UNSIGNED NOT NULL COMMENT '所属会议ID',
  speaker_user_id BIGINT UNSIGNED NULL COMMENT '发言用户ID(可为空)',
  speaker_name VARCHAR(100) NULL COMMENT '发言人名称(识别/手工)',
  segment_index INT UNSIGNED NOT NULL COMMENT '片段序号',
  start_time_sec DECIMAL(10,3) NULL COMMENT '片段开始秒',
  end_time_sec DECIMAL(10,3) NULL COMMENT '片段结束秒',
  language_code VARCHAR(10) NOT NULL DEFAULT 'zh-CN' COMMENT '语言代码',
  source ENUM('whisper', 'manual', 'imported') NOT NULL DEFAULT 'whisper' COMMENT '文本来源',
  content LONGTEXT NOT NULL COMMENT '转写文本内容',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_transcripts_meeting_segment (meeting_id, segment_index),
  KEY idx_transcripts_meeting_id (meeting_id),
  KEY idx_transcripts_speaker_user_id (speaker_user_id),
  CONSTRAINT fk_transcripts_meeting_id
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_transcripts_speaker_user_id
    FOREIGN KEY (speaker_user_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议转写表';


-- ==========================================
-- 4) tasks
-- ==========================================
CREATE TABLE IF NOT EXISTS tasks (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  meeting_id BIGINT UNSIGNED NOT NULL COMMENT '来源会议ID',
  transcript_id BIGINT UNSIGNED NULL COMMENT '来源转写片段ID',
  title VARCHAR(200) NOT NULL COMMENT '任务标题',
  description TEXT NULL COMMENT '任务描述',
  assignee_id BIGINT UNSIGNED NULL COMMENT '执行人用户ID',
  reporter_id BIGINT UNSIGNED NULL COMMENT '创建人/提取人用户ID',
  priority ENUM('high', 'medium', 'low') NOT NULL DEFAULT 'medium' COMMENT '优先级',
  status ENUM('todo', 'in_progress', 'done') NOT NULL DEFAULT 'todo' COMMENT '任务状态',
  due_at DATETIME NULL COMMENT '截止时间',
  completed_at DATETIME NULL COMMENT '完成时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_tasks_meeting_id (meeting_id),
  KEY idx_tasks_transcript_id (transcript_id),
  KEY idx_tasks_assignee_id (assignee_id),
  KEY idx_tasks_reporter_id (reporter_id),
  KEY idx_tasks_status (status),
  KEY idx_tasks_due_at (due_at),
  CONSTRAINT fk_tasks_meeting_id
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_tasks_transcript_id
    FOREIGN KEY (transcript_id) REFERENCES meeting_transcripts(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT fk_tasks_assignee_id
    FOREIGN KEY (assignee_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT fk_tasks_reporter_id
    FOREIGN KEY (reporter_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务表';
