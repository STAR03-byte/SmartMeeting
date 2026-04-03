ALTER TABLE meetings
  DROP FOREIGN KEY fk_meetings_team_id;

ALTER TABLE meetings
  DROP COLUMN team_id;
