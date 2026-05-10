CREATE TABLE IF NOT EXISTS llm_usage (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  provider VARCHAR(50) NOT NULL,
  model VARCHAR(100) NOT NULL,
  operation VARCHAR(50) NOT NULL,
  prompt_tokens INTEGER NOT NULL DEFAULT 0,
  completion_tokens INTEGER NOT NULL DEFAULT 0,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llm_usage_provider ON llm_usage (provider);
CREATE INDEX idx_llm_usage_operation ON llm_usage (operation);
CREATE INDEX idx_llm_usage_created_at ON llm_usage (created_at);
