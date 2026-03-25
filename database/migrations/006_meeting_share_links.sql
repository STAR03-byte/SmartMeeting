USE smartmeeting;

ALTER TABLE meetings
  ADD COLUMN share_token VARCHAR(64) NULL COMMENT '会议分享令牌' AFTER summary,
  ADD COLUMN shared_at DATETIME NULL COMMENT '分享创建时间' AFTER share_token,
  ADD UNIQUE KEY uk_meetings_share_token (share_token);
