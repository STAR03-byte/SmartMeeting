ALTER TABLE tasks
  ADD COLUMN reminder_at TIMESTAMP NULL;

ALTER TABLE tasks
  ADD CONSTRAINT chk_tasks_reminder_before_due
    CHECK (reminder_at IS NULL OR due_at IS NULL OR reminder_at < due_at);
