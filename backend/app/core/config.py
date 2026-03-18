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

    # Auth Settings
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24

    # Whisper Settings
    whisper_model: str = "base"  # tiny | base | small | medium | large
    whisper_device: str = "cpu"  # cpu | cuda | auto
    whisper_language: str = "zh"  # Chinese

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


settings = Settings()
