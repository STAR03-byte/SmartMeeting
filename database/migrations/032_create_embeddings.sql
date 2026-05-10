-- 统一 embeddings 表：存储转写段落、摘要、会议标题等的向量
-- 支持 pgvector 语义搜索 + tsvector 全文搜索

CREATE TABLE embeddings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    meeting_id INT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    source_type VARCHAR(20) NOT NULL,  -- transcript | summary | title
    source_id BIGINT,                  -- 原始记录 ID（transcript_id 等，可为空）
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(384),
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embeddings_meeting ON embeddings(meeting_id);
CREATE INDEX idx_embeddings_source ON embeddings(source_type, source_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
CREATE INDEX idx_embeddings_search ON embeddings USING GIN (search_vector);
