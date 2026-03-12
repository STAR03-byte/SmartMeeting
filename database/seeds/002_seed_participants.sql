-- SmartMeeting 参与人关系种子数据
-- 依赖: 001_init + 005_audit_and_participants + 001_seed_basic_data

USE smartmeeting;

START TRANSACTION;

DELETE FROM meeting_participants WHERE id IN (5001, 5002, 5003, 5004, 5005);

INSERT INTO meeting_participants (
  id,
  meeting_id,
  user_id,
  participant_role,
  attendance_status,
  joined_at,
  left_at,
  created_at,
  updated_at
) VALUES
  (5001, 3001, 4001, 'owner', 'attended', '2026-03-12 10:05:00', '2026-03-12 11:02:00', NOW(), NOW()),
  (5002, 3001, 4002, 'required', 'attended', '2026-03-12 10:06:00', '2026-03-12 11:01:00', NOW(), NOW()),
  (5003, 3001, 4003, 'required', 'attended', '2026-03-12 10:08:00', '2026-03-12 10:58:00', NOW(), NOW()),
  (5004, 3002, 4002, 'owner', 'accepted', NULL, NULL, NOW(), NOW()),
  (5005, 3002, 4003, 'optional', 'invited', NULL, NULL, NOW(), NOW());

COMMIT;
