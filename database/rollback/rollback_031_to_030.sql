-- rollback: 031 → 030
DROP TRIGGER IF EXISTS trg_commitments_updated_at ON commitments;
DROP TRIGGER IF EXISTS trg_decisions_updated_at ON decisions;
DROP TABLE IF EXISTS meeting_topics;
DROP TABLE IF EXISTS commitments;
DROP TABLE IF EXISTS decisions;
