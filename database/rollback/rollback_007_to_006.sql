-- 007 是条件性修改，回滚时恢复原始外键名
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'meeting_audios') THEN
    EXECUTE 'ALTER TABLE meeting_audios DROP CONSTRAINT IF EXISTS fk_meeting_audios_meeting_id';
  END IF;
END $$;
