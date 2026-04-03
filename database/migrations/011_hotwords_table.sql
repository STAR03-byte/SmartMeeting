USE smartmeeting;

CREATE TABLE hotwords (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  word VARCHAR(100) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_hotwords_user_word (user_id, word),
  KEY idx_hotwords_user_id (user_id),
  CONSTRAINT fk_hotwords_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
