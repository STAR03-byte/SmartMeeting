"""数据库连接与会话管理。"""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings


def _build_engine():
    """根据配置构建数据库引擎，开发环境可回退 SQLite。"""

    if settings.db_backend.lower() == "sqlite":
        return create_engine(
            settings.sqlite_database_uri,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )

    mysql_engine = create_engine(settings.sqlalchemy_database_uri, pool_pre_ping=True)
    if not settings.db_auto_fallback_sqlite:
        return mysql_engine

    try:
        with mysql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return mysql_engine
    except SQLAlchemyError:
        sqlite_file = Path(settings.sqlite_path)
        if sqlite_file.parent:
            sqlite_file.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(
            settings.sqlite_database_uri,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )

engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """提供请求级数据库会话。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
