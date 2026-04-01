import pytest

from app.core.config import Settings


def test_production_rejects_default_jwt_secret() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret_key="change-me-in-production",
    )

    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be set to a strong secret in production"):
        settings.validate_security()


def test_development_allows_default_jwt_secret() -> None:
    settings = Settings(
        app_env="dev",
        jwt_secret_key="change-me-in-production",
    )

    settings.validate_security()
