CREATE TABLE team_members (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  team_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  role ENUM('owner', 'admin', 'member') DEFAULT 'member',
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uk_team_user (team_id, user_id)
);
