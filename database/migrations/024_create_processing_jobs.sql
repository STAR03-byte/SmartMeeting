CREATE TABLE IF NOT EXISTS processing_jobs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  job_id VARCHAR(36) NOT NULL,
  meeting_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  job_type VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  progress REAL NOT NULL DEFAULT 0.0,
  message VARCHAR(500) NOT NULL DEFAULT '',
  current_chunk INTEGER NOT NULL DEFAULT 0,
  total_chunks INTEGER NOT NULL DEFAULT 1,
  result_json TEXT NULL,
  error TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP NULL,
  completed_at TIMESTAMP NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uk_processing_jobs_job_id UNIQUE (job_id),
  CONSTRAINT fk_processing_jobs_meeting_id FOREIGN KEY (meeting_id)
    REFERENCES meetings(id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_processing_jobs_user_id FOREIGN KEY (user_id)
    REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX idx_processing_jobs_meeting_id ON processing_jobs (meeting_id);
CREATE INDEX idx_processing_jobs_user_id ON processing_jobs (user_id);
CREATE INDEX idx_processing_jobs_status ON processing_jobs (status);

CREATE TRIGGER trg_processing_jobs_updated_at
  BEFORE UPDATE ON processing_jobs
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
