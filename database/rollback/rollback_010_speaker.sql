USE smartmeeting;

ALTER TABLE meeting_transcripts
  DROP COLUMN IF EXISTS speaker_id;
