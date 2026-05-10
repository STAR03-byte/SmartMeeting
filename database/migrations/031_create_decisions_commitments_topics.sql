-- 031: 创建 decisions / commitments / meeting_topics 表
-- Phase 2: 会议记忆能力 — 决策提取、承诺追踪、主题抽取

-- decisions: 会议决策（含 pgvector 语义搜索 + tsvector 全文搜索）
CREATE TABLE IF NOT EXISTS decisions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    meeting_id BIGINT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    proposer_name VARCHAR(100),
    proposer_user_id BIGINT REFERENCES users(id),
    context TEXT,
    confidence FLOAT DEFAULT 0.7,
    status VARCHAR(20) DEFAULT 'candidate' NOT NULL
        CHECK (status IN ('candidate', 'confirmed', 'rejected')),
    embedding vector(384),
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(content, '') || ' ' || coalesce(context, ''))
    ) STORED,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_decisions_meeting ON decisions(meeting_id);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_search ON decisions USING GIN (search_vector);

-- commitments: 会议承诺（含 pgvector 语义搜索 + tsvector 全文搜索）
CREATE TABLE IF NOT EXISTS commitments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    meeting_id BIGINT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    assignee_name VARCHAR(100),
    assignee_user_id BIGINT REFERENCES users(id),
    due_hint VARCHAR(100),
    status VARCHAR(20) DEFAULT 'candidate' NOT NULL
        CHECK (status IN ('candidate', 'confirmed', 'in_progress', 'done', 'abandoned')),
    linked_task_id BIGINT REFERENCES tasks(id),
    embedding vector(384),
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(content, '') || ' ' || coalesce(due_hint, ''))
    ) STORED,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_commitments_meeting ON commitments(meeting_id);
CREATE INDEX IF NOT EXISTS idx_commitments_status ON commitments(status);
CREATE INDEX IF NOT EXISTS idx_commitments_assignee ON commitments(assignee_user_id);
CREATE INDEX IF NOT EXISTS idx_commitments_search ON commitments USING GIN (search_vector);

-- meeting_topics: 会议主题
CREATE TABLE IF NOT EXISTS meeting_topics (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    meeting_id BIGINT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    topic VARCHAR(200) NOT NULL,
    relevance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_meeting_topics_meeting ON meeting_topics(meeting_id);

-- updated_at trigger for decisions
CREATE TRIGGER trg_decisions_updated_at
    BEFORE UPDATE ON decisions
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- updated_at trigger for commitments
CREATE TRIGGER trg_commitments_updated_at
    BEFORE UPDATE ON commitments
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
