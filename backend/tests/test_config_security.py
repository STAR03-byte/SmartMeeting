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


def test_production_rejects_weak_database_credentials() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret_key="strong-secret-value",
        db_user="root",
        db_password="root",
    )

    with pytest.raises(ValueError, match="DB credentials are too weak for production"):
        settings.validate_security()


def test_production_requires_llm_api_key_for_openai_provider() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret_key="strong-secret-value",
        db_user="prod_user",
        db_password="strong-db-password",
        llm_provider="openai",
        llm_api_key="",
    )

    with pytest.raises(ValueError, match="LLM_API_KEY is required for OpenAI provider in production"):
        settings.validate_security()
