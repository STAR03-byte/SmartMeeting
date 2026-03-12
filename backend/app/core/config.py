"""应用配置模块。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行时配置。"""

    app_name: str = "SmartMeeting API"
    app_env: str = "dev"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "root"
    db_name: str = "smartmeeting"

    action_keywords: str = "请,负责,需要,完成,提交,跟进"
    high_priority_keywords: str = "今天,今日,本周,尽快,立即,截止,风险"

    model_config = SettingsConfigDict(env_file="backend/.env", env_file_encoding="utf-8")

    @property
    def sqlalchemy_database_uri(self) -> str:
        """返回 SQLAlchemy MySQL 连接串。"""

        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

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
