USE smartmeeting;

CREATE TABLE IF NOT EXISTS meeting_audios (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  meeting_id BIGINT UNSIGNED NOT NULL,
  filename VARCHAR(255) NOT NULL,
  storage_path VARCHAR(512) NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  size_bytes INT NOT NULL,
  uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_meeting_audios_meeting_id (meeting_id),
  CONSTRAINT fk_meeting_audios_meeting_id FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
