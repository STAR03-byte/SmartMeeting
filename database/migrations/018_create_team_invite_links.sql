CREATE TABLE IF NOT EXISTS team_invite_links (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  team_id BIGINT NOT NULL,
  inviter_id BIGINT NOT NULL,
  invite_token VARCHAR(128) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  revoked BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uk_team_invite_links_token UNIQUE (invite_token),
  CONSTRAINT fk_team_invite_links_team_id FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
  CONSTRAINT fk_team_invite_links_inviter_id FOREIGN KEY (inviter_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_team_invite_links_team_id ON team_invite_links (team_id);
CREATE INDEX ix_team_invite_links_inviter_id ON team_invite_links (inviter_id);
CREATE INDEX ix_team_invite_links_expires_at ON team_invite_links (expires_at);

CREATE TRIGGER trg_team_invite_links_updated_at
  BEFORE UPDATE ON team_invite_links
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
