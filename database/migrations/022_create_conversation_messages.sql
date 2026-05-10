-- Migration: Create conversation_messages table for AI Assistant module
-- Version: 022
-- Description: Stores messages in AI assistant conversations

CREATE TABLE IF NOT EXISTS conversation_messages (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  conversation_id BIGINT NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_conversation_messages_conversation_id
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_conversation_messages_conversation_id ON conversation_messages (conversation_id);
CREATE INDEX idx_conversation_messages_created_at ON conversation_messages (created_at);
CREATE INDEX idx_conversation_messages_conversation_created ON conversation_messages (conversation_id, created_at);
