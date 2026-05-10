ALTER TABLE meeting_participants
  ADD COLUMN role VARCHAR(20) NULL DEFAULT 'participant'
    CHECK (role IN ('organizer', 'participant'));
