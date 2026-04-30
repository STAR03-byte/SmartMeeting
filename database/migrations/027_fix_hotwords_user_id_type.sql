USE smartmeeting;

-- Fix hotwords.user_id type: INT -> BIGINT UNSIGNED to match users.id
ALTER TABLE hotwords
  MODIFY user_id BIGINT UNSIGNED NOT NULL;
