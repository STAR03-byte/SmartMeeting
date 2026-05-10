-- 回滚 002_enhance_smartmeeting.sql

DROP TRIGGER IF EXISTS trg_tasks_set_completed_at ON tasks;
DROP FUNCTION IF EXISTS fn_tasks_set_completed_at();

DROP VIEW IF EXISTS v_task_detail;
DROP VIEW IF EXISTS v_meeting_overview;

ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_tasks_due_after_create;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_tasks_complete_after_create;
ALTER TABLE meeting_transcripts DROP CONSTRAINT IF EXISTS chk_transcript_time_range;
ALTER TABLE meetings DROP CONSTRAINT IF EXISTS chk_meetings_time_range;
ALTER TABLE meetings DROP CONSTRAINT IF EXISTS chk_meetings_actual_time_range;

ALTER TABLE tasks DROP COLUMN IF EXISTS progress_note;
