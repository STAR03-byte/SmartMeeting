USE smartmeeting;

ALTER TABLE meeting_audios
  DROP FOREIGN KEY meeting_audios_ibfk_1,
  ADD CONSTRAINT fk_meeting_audios_meeting_id
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE;
