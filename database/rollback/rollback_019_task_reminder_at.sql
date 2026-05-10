ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_tasks_reminder_before_due;
ALTER TABLE tasks DROP COLUMN IF EXISTS reminder_at;
