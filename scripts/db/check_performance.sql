-- SmartMeeting 查询性能检查脚本（EXPLAIN）

USE smartmeeting;

EXPLAIN SELECT *
FROM meetings
WHERE status = 'planned'
ORDER BY scheduled_start_at DESC
LIMIT 20;

EXPLAIN SELECT *
FROM meetings
WHERE organizer_id = 4001
ORDER BY created_at DESC
LIMIT 20;

EXPLAIN SELECT *
FROM meeting_transcripts
WHERE meeting_id = 3001
ORDER BY start_time_sec ASC;

EXPLAIN SELECT *
FROM tasks
WHERE assignee_id = 4002
  AND status IN ('todo', 'in_progress')
ORDER BY due_at ASC;

EXPLAIN SELECT *
FROM tasks
WHERE meeting_id = 3001
  AND status = 'todo'
ORDER BY priority ASC, due_at ASC;

EXPLAIN SELECT *
FROM tasks
WHERE reporter_id = 4001
ORDER BY created_at DESC;
