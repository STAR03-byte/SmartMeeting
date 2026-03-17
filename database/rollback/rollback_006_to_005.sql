USE smartmeeting;

ALTER TABLE meetings
  DROP INDEX uk_meetings_share_token,
  DROP COLUMN shared_at,
  DROP COLUMN share_token;
