-- SmartMeeting base seed data
-- Dependency: run migrations first, then this seed

USE smartmeeting;

START TRANSACTION;

SET FOREIGN_KEY_CHECKS = 0;

DELETE FROM tasks WHERE id IN (1001, 1002, 1003, 1004);
DELETE FROM meeting_transcripts WHERE id IN (2001, 2002, 2003, 2004, 2005);
DELETE FROM meetings WHERE id IN (3001, 3002);
DELETE FROM users WHERE id IN (4001, 4002, 4003);

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO users (
  id, username, email, password_hash, full_name, role, is_active, last_login_at, created_at, updated_at
) VALUES
  (4001, 'alice_admin', 'alice@example.com', '$2b$12$example_admin_hash_replace_in_prod', 'Alice Chen', 'admin', 1, NOW(), '2026-03-12 09:00:00', '2026-03-12 09:00:00'),
  (4002, 'bob_pm', 'bob@example.com', '$2b$12$example_pm_hash_replace_in_prod', 'Bob Li', 'member', 1, NOW(), '2026-03-12 09:00:00', '2026-03-12 09:00:00'),
  (4003, 'cindy_dev', 'cindy@example.com', '$2b$12$example_dev_hash_replace_in_prod', 'Cindy Wang', 'member', 1, NOW(), '2026-03-13 10:00:00', '2026-03-13 10:00:00');

INSERT INTO meetings (
  id, title, description, organizer_id, scheduled_start_at, scheduled_end_at, actual_start_at, actual_end_at, location, status, created_at, updated_at
) VALUES
  (3001, '[SEED] Product Review', 'Discuss MVP scope and milestones.', 4001, '2026-03-12 10:00:00', '2026-03-12 11:00:00', '2026-03-12 10:05:00', '2026-03-12 11:02:00', 'Tencent Meeting #8899', 'done', '2026-03-12 09:00:00', '2026-03-12 09:00:00'),
  (3002, '[SEED] Weekly Dev Sync', 'Sync development progress and risks.', 4002, '2026-03-13 09:30:00', '2026-03-13 10:00:00', NULL, NULL, 'Meeting Room A', 'planned', '2026-03-12 09:00:00', '2026-03-12 09:00:00');

INSERT INTO meeting_transcripts (
  id, meeting_id, speaker_user_id, speaker_name, segment_index, start_time_sec, end_time_sec, language_code, source, content, created_at, updated_at
) VALUES
  (2001, 3001, 4001, 'Alice Chen', 1, 0.000, 30.500, 'zh-CN', 'whisper', '大家好，今天我们确认 SmartMeeting MVP 目标，优先交付会议转写、纪要生成和任务提取。', NOW(), NOW()),
  (2002, 3001, 4002, 'Bob Li', 2, 31.000, 78.200, 'zh-CN', 'whisper', '我负责本周完成后端会议管理接口，并输出 API 文档。', NOW(), NOW()),
  (2003, 3001, 4003, 'Cindy Wang', 3, 79.000, 125.800, 'zh-CN', 'whisper', '我会在周五前完成前端会议列表和会议详情页面。', NOW(), NOW()),
  (2004, 3001, NULL, 'System', 4, 126.000, 150.000, 'zh-CN', 'manual', '会议结论：下周一进行联调，周三完成 MVP 内测。', NOW(), NOW()),
  (2005, 3002, 4002, 'Bob Li', 1, 0.000, 18.000, 'zh-CN', 'imported', '本次周例会将跟进上周遗留问题与本周计划。', NOW(), NOW());

INSERT INTO tasks (
  id, meeting_id, transcript_id, title, description, assignee_id, reporter_id, priority, status, due_at, completed_at, created_at, updated_at
) VALUES
  (1001, 3001, 2002, '完成后端会议管理 API', '实现 meetings CRUD，并提供 Swagger 示例。', 4002, 4001, 'high', 'in_progress', '2026-03-14 18:00:00', NULL, '2026-03-12 09:00:00', '2026-03-12 09:00:00'),
  (1002, 3001, 2003, '完成前端会议列表与详情', '实现会议列表、会议详情、基础状态展示。', 4003, 4001, 'medium', 'todo', '2026-03-15 18:00:00', NULL, '2026-03-12 09:00:00', '2026-03-12 09:00:00'),
  (1003, 3001, 2004, '组织下周一前后端联调', '确认联调接口、联调环境与时间安排。', 4001, 4001, 'high', 'todo', '2026-03-16 10:00:00', NULL, '2026-03-12 09:00:00', '2026-03-12 09:00:00'),
  (1004, 3002, 2005, '整理上周遗留问题清单', '补全阻塞项、责任人与预计解决时间。', 4002, 4002, 'low', 'done', '2026-03-13 12:00:00', '2026-03-13 11:20:00', '2026-03-12 09:00:00', '2026-03-12 09:00:00');

COMMIT;
