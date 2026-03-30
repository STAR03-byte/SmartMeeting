USE smartmeeting;

ALTER TABLE meeting_audios
  DROP FOREIGN KEY fk_meeting_audios_meeting_id,
  ADD CONSTRAINT meeting_audios_ibfk_1
    FOREIGN KEY (meeting_id) REFERENCES meetings(id);
