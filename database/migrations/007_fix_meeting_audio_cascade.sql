-- meeting_audios 表在此时尚未创建（028 才创建），此迁移保留兼容性
-- 如果 meeting_audios 已存在则修改外键，否则跳过
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'meeting_audios') THEN
    EXECUTE 'ALTER TABLE meeting_audios DROP CONSTRAINT IF EXISTS meeting_audios_ibfk_1';
    EXECUTE 'ALTER TABLE meeting_audios ADD CONSTRAINT fk_meeting_audios_meeting_id
      FOREIGN KEY (meeting_id) REFERENCES meetings(id)
      ON UPDATE CASCADE ON DELETE CASCADE';
  END IF;
END $$;
