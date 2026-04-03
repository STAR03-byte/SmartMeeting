USE smartmeeting;

ALTER TABLE meeting_transcripts
  ADD COLUMN speaker_id INT NULL AFTER speaker_user_id;
