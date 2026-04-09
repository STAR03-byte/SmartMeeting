USE smartmeeting;

ALTER TABLE tasks
  DROP CHECK chk_tasks_reminder_before_due,
  DROP COLUMN reminder_at;
