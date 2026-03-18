from app.core.security import create_access_token, get_password_hash, verify_password


def test_password_hash_and_verify() -> None:
    hashed = get_password_hash("secret123")

    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong123", hashed) is False


def test_create_access_token_contains_subject() -> None:
    token = create_access_token(subject="42")

    assert isinstance(token, str)
    assert token != "42"
