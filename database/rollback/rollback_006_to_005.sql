DROP INDEX IF EXISTS uk_meetings_share_token;
ALTER TABLE meetings DROP COLUMN IF EXISTS shared_at;
ALTER TABLE meetings DROP COLUMN IF EXISTS share_token;
