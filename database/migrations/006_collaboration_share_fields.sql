USE smartmeeting;

ALTER TABLE meetings
  ADD COLUMN share_token VARCHAR(64) NULL COMMENT '会议分享令牌' AFTER postprocess_version,
  ADD COLUMN shared_at DATETIME NULL COMMENT '首次分享时间' AFTER share_token,
  ADD UNIQUE KEY uk_meetings_share_token (share_token);
