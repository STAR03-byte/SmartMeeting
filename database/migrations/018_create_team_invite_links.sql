CREATE TABLE team_invite_links (
    id INT PRIMARY KEY AUTO_INCREMENT,
    team_id INT NOT NULL,
    inviter_id INT NOT NULL,
    invite_token VARCHAR(128) NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_team_invite_links_token (invite_token),
    KEY ix_team_invite_links_team_id (team_id),
    KEY ix_team_invite_links_inviter_id (inviter_id),
    KEY ix_team_invite_links_expires_at (expires_at),
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (inviter_id) REFERENCES users(id) ON DELETE CASCADE
);
