ALTER TABLE meetings DROP CONSTRAINT IF EXISTS fk_meetings_team_id;
ALTER TABLE meetings DROP COLUMN IF EXISTS team_id;
