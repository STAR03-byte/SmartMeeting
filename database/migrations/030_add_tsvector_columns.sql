-- 全文搜索预埋：为 meetings 和 meeting_transcripts 添加 tsvector 列和 GIN 索引
-- 为 Phase 2 跨会议语义搜索做准备

-- meetings 表：标题 + 描述 + 摘要的全文索引
ALTER TABLE meetings
  ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
      to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || coalesce(summary, ''))
    ) STORED;

CREATE INDEX idx_meetings_search_vector ON meetings USING GIN (search_vector);


-- meeting_transcripts 表：转写内容的全文索引
ALTER TABLE meeting_transcripts
  ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
      to_tsvector('simple', coalesce(content, '') || ' ' || coalesce(speaker_name, ''))
    ) STORED;

CREATE INDEX idx_transcripts_search_vector ON meeting_transcripts USING GIN (search_vector);
