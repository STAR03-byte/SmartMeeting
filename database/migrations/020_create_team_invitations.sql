CREATE TABLE IF NOT EXISTS team_invitations (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  team_id BIGINT NOT NULL,
  inviter_id BIGINT NOT NULL,
  invitee_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_team_invitations_team_id FOREIGN KEY (team_id) REFERENCES teams(id),
  CONSTRAINT fk_team_invitations_inviter_id FOREIGN KEY (inviter_id) REFERENCES users(id),
  CONSTRAINT fk_team_invitations_invitee_id FOREIGN KEY (invitee_id) REFERENCES users(id)
);

CREATE TRIGGER trg_team_invitations_updated_at
  BEFORE UPDATE ON team_invitations
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
