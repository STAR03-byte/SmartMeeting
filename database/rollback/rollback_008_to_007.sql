USE smartmeeting;

ALTER TABLE meeting_participants
  DROP INDEX uk_meeting_participants_unique;
