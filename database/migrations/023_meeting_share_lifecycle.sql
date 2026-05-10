-- Migration: Add meeting share lifecycle fields
-- Version: 023
-- Description: Supports expiring and revoking meeting share links

ALTER TABLE meetings
  ADD COLUMN share_expires_at TIMESTAMP NULL,
  ADD COLUMN share_revoked_at TIMESTAMP NULL;

CREATE INDEX idx_meetings_share_lifecycle ON meetings (share_token, share_revoked_at, share_expires_at);
