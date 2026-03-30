from __future__ import annotations

from pathlib import Path


def test_env_example_has_single_jwt_block() -> None:
    content = Path(".env.example").read_text(encoding="utf-8")
    assert content.count("JWT_SECRET_KEY=") == 1
    assert content.count("JWT_ALGORITHM=") == 1
    assert content.count("JWT_ACCESS_TOKEN_EXPIRE_MINUTES=") == 1


def test_backend_env_example_keeps_secret_defaults_out_of_readme() -> None:
    backend_readme = Path("backend/README.md").read_text(encoding="utf-8")
    assert "Default account: `alice_admin` / `admin123`" not in backend_readme
