USE smartmeeting;

ALTER TABLE audit_logs
  MODIFY entity_type ENUM('users', 'meetings', 'meeting_transcripts', 'tasks', 'meeting_participants') NOT NULL,
  MODIFY action ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL;
