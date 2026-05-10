ALTER TABLE meetings
  ADD COLUMN share_token VARCHAR(64) NULL,
  ADD COLUMN shared_at TIMESTAMP NULL;

CREATE UNIQUE INDEX uk_meetings_share_token ON meetings (share_token) WHERE share_token IS NOT NULL;
