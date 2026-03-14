"""FastAPI 应用入口。"""

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine

# 确保模型元数据注册完成
from app import models  # noqa: F401

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def init_dev_sqlite_schema() -> None:
    """开发 SQLite 模式下自动建表，便于本地联调。"""

    if engine.dialect.name == "sqlite":
        try:
            Base.metadata.create_all(bind=engine)
        except OperationalError as exc:
            if "already exists" not in str(exc).lower():
                raise


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """服务健康检查接口。"""

    return {"status": "ok"}
