"""应用配置模块。"""

from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行时配置。"""

    app_name: str = "SmartMeeting API"
    app_env: str = "dev"

    # Database
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "root"
    db_name: str = "smartmeeting"
    db_backend: str = "mysql"
    db_auto_fallback_sqlite: bool = True
    sqlite_path: str = "backend/dev.db"

    # Task extraction keywords (fallback when LLM unavailable)
    action_keywords: str = "请,负责,需要,完成,提交,跟进"
    high_priority_keywords: str = "今天,今日,本周,尽快,立即,截止,风险"

    # LLM Settings
    llm_provider: str = "openai"  # openai | local | mock
    llm_api_key: str = ""  # OPENAI_API_KEY
    llm_base_url: str = ""  # Optional: for Azure/custom endpoints
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2000
    llm_timeout: int = 60  # seconds
    llm_fallback_provider: str = "ollama"  # ollama | mock | none
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1"
    ollama_timeout: int = 60  # seconds
    ollama_temperature: float = 0.3
    ollama_max_tokens: int = 2000

    # Auth Settings
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24
    auth_login_rate_limit: str = "5/minute"

    # Whisper Settings
    use_faster_whisper: bool = True
    faster_whisper_compute_type: str = "int8_float16"  # int8_float16 or int8
    whisper_model: str = "small"  # tiny | base | small | medium | large
    whisper_device: str = "cpu"  # cpu | cuda | auto
    whisper_language: str = "zh"
    whisper_hot_words: str = ""
    whisper_normalize_to_simplified: bool = True
    enable_speaker_diarization: bool = False
    meeting_audio_max_size_bytes: int = 100 * 1024 * 1024

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        """返回 SQLAlchemy MySQL 连接串。"""

        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def sqlite_database_uri(self) -> str:
        """返回 SQLAlchemy SQLite 连接串。"""

        return f"sqlite:///{self.sqlite_path}"

    @property
    def action_keyword_list(self) -> tuple[str, ...]:
        """返回任务抽取关键词列表。"""

        return tuple(item.strip() for item in self.action_keywords.split(",") if item.strip())

    @property
    def high_priority_keyword_list(self) -> tuple[str, ...]:
        """返回高优先级关键词列表。"""

        return tuple(
            item.strip() for item in self.high_priority_keywords.split(",") if item.strip()
        )

    def validate_security(self) -> None:
        env = self.app_env.strip().lower()
        if env not in {"prod", "production"}:
            return

        if self.jwt_secret_key == "change-me-in-production":
            raise ValueError("JWT_SECRET_KEY must be set to a strong secret in production")

        weak_users = {"root", "admin", "smartmeeting"}
        weak_passwords = {"root", "admin", "smartmeeting", "123456", "password"}
        if self.db_user.strip().lower() in weak_users or self.db_password in weak_passwords:
            raise ValueError("DB credentials are too weak for production")

        if self.llm_provider.strip().lower() == "openai" and not self.llm_api_key.strip():
            raise ValueError("LLM_API_KEY is required for OpenAI provider in production")


settings = Settings()
settings.validate_security()
