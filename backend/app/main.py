"""FastAPI 应用入口。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import OperationalError

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.limiter import limiter
from app.services.llm_service import LLMServiceError
from app.services.whisper_service import WhisperServiceError

# 确保模型元数据注册完成
from app import models  # noqa: F401

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """开发 SQLite 模式下自动建表，便于本地联调。"""

    if engine.dialect.name == "sqlite":
        try:
            Base.metadata.create_all(bind=engine)
        except OperationalError as exc:
            if "already exists" not in str(exc).lower():
                raise
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(LLMServiceError)
@app.exception_handler(WhisperServiceError)
async def handle_ai_service_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("AI service error", exc_info=exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "AI service unavailable",
            "error_code": "AI_SERVICE_UNAVAILABLE",
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "error_code": "REQUEST_VALIDATION_ERROR",
        },
    )


def _default_error_code_for_status(status_code: int) -> str:
    if status_code == 400:
        return "BAD_REQUEST"
    if status_code == 401:
        return "UNAUTHORIZED"
    if status_code == 403:
        return "FORBIDDEN"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 409:
        return "CONFLICT"
    if status_code == 422:
        return "REQUEST_VALIDATION_ERROR"
    if 400 <= status_code < 500:
        return "CLIENT_ERROR"
    return "INTERNAL_SERVER_ERROR"


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail

    error_code: str | None = None
    if isinstance(detail, dict):
        maybe_error_code = detail.get("error_code")
        if isinstance(maybe_error_code, str) and maybe_error_code:
            error_code = maybe_error_code
        detail = detail.get("detail", detail)

    if error_code is None:
        error_code = _default_error_code_for_status(exc.status_code)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": detail,
            "error_code": error_code,
        },
        headers=exc.headers,
    )


@app.exception_handler(RateLimitExceeded)
async def handle_rate_limit(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": str(exc.detail),
            "error_code": "CLIENT_ERROR",
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """服务健康检查接口。"""

    return {"status": "ok"}
