CREATE TABLE IF NOT EXISTS hotwords (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL,
  word VARCHAR(100) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_hotwords_user_word UNIQUE (user_id, word),
  CONSTRAINT fk_hotwords_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_hotwords_user_id ON hotwords (user_id);
