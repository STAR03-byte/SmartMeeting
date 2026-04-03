ALTER TABLE meeting_participants
  ADD COLUMN role ENUM('organizer', 'participant') NULL DEFAULT 'participant';
