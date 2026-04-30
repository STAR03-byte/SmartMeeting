CREATE TABLE IF NOT EXISTS processing_jobs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id VARCHAR(36) NOT NULL,
    meeting_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    job_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress FLOAT NOT NULL DEFAULT 0.0,
    message VARCHAR(500) NOT NULL DEFAULT '',
    current_chunk INT UNSIGNED NOT NULL DEFAULT 0,
    total_chunks INT UNSIGNED NOT NULL DEFAULT 1,
    result_json TEXT NULL,
    error TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_processing_jobs_job_id (job_id),
    KEY idx_processing_jobs_meeting_id (meeting_id),
    KEY idx_processing_jobs_user_id (user_id),
    KEY idx_processing_jobs_status (status),
    CONSTRAINT fk_processing_jobs_meeting_id FOREIGN KEY (meeting_id)
        REFERENCES meetings(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_processing_jobs_user_id FOREIGN KEY (user_id)
        REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
