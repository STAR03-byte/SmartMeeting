CREATE TABLE IF NOT EXISTS meeting_audios (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  meeting_id BIGINT NOT NULL,
  filename VARCHAR(255) NOT NULL,
  storage_path VARCHAR(512) NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  size_bytes INTEGER NOT NULL,
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_meeting_audios_meeting_id FOREIGN KEY (meeting_id)
    REFERENCES meetings(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX idx_meeting_audios_meeting_id ON meeting_audios (meeting_id);
