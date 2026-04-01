USE smartmeeting;

ALTER TABLE audit_logs
  MODIFY entity_type VARCHAR(64) NOT NULL,
  MODIFY action VARCHAR(32) NOT NULL;
