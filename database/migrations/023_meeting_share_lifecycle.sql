-- Migration: Add meeting share lifecycle fields
-- Version: 023
-- Description: Supports expiring and revoking meeting share links

ALTER TABLE meetings
  ADD COLUMN share_expires_at DATETIME NULL AFTER shared_at,
  ADD COLUMN share_revoked_at DATETIME NULL AFTER share_expires_at,
  ADD INDEX idx_meetings_share_lifecycle (share_token, share_revoked_at, share_expires_at);
