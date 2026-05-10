DROP INDEX IF EXISTS idx_meetings_share_lifecycle;
ALTER TABLE meetings DROP COLUMN IF EXISTS share_revoked_at;
ALTER TABLE meetings DROP COLUMN IF EXISTS share_expires_at;
