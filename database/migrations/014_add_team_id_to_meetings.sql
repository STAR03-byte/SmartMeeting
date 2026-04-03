ALTER TABLE meetings
  ADD COLUMN team_id BIGINT UNSIGNED NULL;

ALTER TABLE meetings
  ADD CONSTRAINT fk_meetings_team_id
  FOREIGN KEY (team_id) REFERENCES teams(id)
  ON DELETE SET NULL;
