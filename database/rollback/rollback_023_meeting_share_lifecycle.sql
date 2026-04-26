USE smartmeeting;

ALTER TABLE meetings
  DROP INDEX idx_meetings_share_lifecycle,
  DROP COLUMN share_revoked_at,
  DROP COLUMN share_expires_at;
