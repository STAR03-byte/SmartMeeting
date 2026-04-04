USE smartmeeting;

ALTER TABLE teams
  ADD COLUMN is_public TINYINT(1) NOT NULL DEFAULT 0 AFTER description;
