USE smartmeeting;

ALTER TABLE tasks
  ADD COLUMN reminder_at DATETIME NULL AFTER due_at,
  ADD CONSTRAINT chk_tasks_reminder_before_due
    CHECK (reminder_at IS NULL OR due_at IS NULL OR reminder_at < due_at);
