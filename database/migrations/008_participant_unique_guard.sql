USE smartmeeting;

ALTER TABLE meeting_participants
  ADD CONSTRAINT uk_meeting_participants_unique
  UNIQUE (meeting_id, user_id);
