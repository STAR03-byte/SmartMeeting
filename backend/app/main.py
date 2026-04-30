# pyright: reportAny=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedImport=false, reportUnusedCallResult=false, reportUnusedParameter=false
"""FastAPI 应用入口。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.v1.router import api_router
from app.api.v1.endpoints import ai
from app.core.config import settings
from app.core.database import Base, engine
from app.core.errors import AppError, ErrorCode
from app.core.limiter import limiter
from app.services.ai.llm_service import LLMServiceError
from app.services.ai.whisper_service import WhisperServiceError

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
    elif engine.dialect.name == "mysql":
        _ensure_mysql_team_features()
        _ensure_mysql_ai_assistant_features()
        _ensure_mysql_processing_jobs()
    yield
    # Shutdown: cancel active async jobs
    from app.services.pipeline.job_manager import job_manager
    await job_manager.shutdown()


def _normalize_mysql_id_type(raw_type: str | None) -> str:
    if not raw_type:
        return "BIGINT UNSIGNED"
    t = raw_type.strip().lower()
    if t.startswith("bigint"):
        return "BIGINT UNSIGNED" if "unsigned" in t else "BIGINT"
    if t.startswith("int"):
        return "INT UNSIGNED" if "unsigned" in t else "INT"
    return "BIGINT UNSIGNED"


def _ensure_mysql_team_features() -> None:
    with engine.begin() as connection:
        is_public_exists = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = 'teams'
                  AND column_name = 'is_public'
                """
            )
        ).scalar_one()

        if not is_public_exists:
            connection.execute(text("ALTER TABLE teams ADD COLUMN is_public TINYINT(1) NOT NULL DEFAULT 0"))

        team_id_raw_type = connection.execute(
            text(
                """
                SELECT COLUMN_TYPE
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = 'teams'
                  AND column_name = 'id'
                LIMIT 1
                """
            )
        ).scalar_one_or_none()
        user_id_raw_type = connection.execute(
            text(
                """
                SELECT COLUMN_TYPE
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = 'users'
                  AND column_name = 'id'
                LIMIT 1
                """
            )
        ).scalar_one_or_none()

        team_id_sql_type = _normalize_mysql_id_type(team_id_raw_type)
        user_id_sql_type = _normalize_mysql_id_type(user_id_raw_type)

        if not re.fullmatch(r"[A-Z ]+", team_id_sql_type) or not re.fullmatch(r"[A-Z ]+", user_id_sql_type):
            raise RuntimeError("Invalid MySQL id type detected while ensuring team features")

        team_invitations_exists = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = 'team_invitations'
                """
            )
        ).scalar_one()

        if not team_invitations_exists:
            connection.execute(
                text(
                    f"""
                    CREATE TABLE team_invitations (
                        id {team_id_sql_type} NOT NULL AUTO_INCREMENT,
                        team_id {team_id_sql_type} NOT NULL,
                        inviter_id {user_id_sql_type} NOT NULL,
                        invitee_id {user_id_sql_type} NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        UNIQUE KEY uk_team_invitation_status (team_id, invitee_id, status),
                        KEY ix_team_invitations_team_id (team_id),
                        KEY ix_team_invitations_inviter_id (inviter_id),
                        KEY ix_team_invitations_invitee_id (invitee_id),
                        CONSTRAINT fk_team_invitations_team_id FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE CASCADE,
                        CONSTRAINT fk_team_invitations_inviter_id FOREIGN KEY (inviter_id) REFERENCES users (id) ON DELETE CASCADE,
                        CONSTRAINT fk_team_invitations_invitee_id FOREIGN KEY (invitee_id) REFERENCES users (id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                )
            )

        team_invite_links_exists = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = 'team_invite_links'
                """
            )
        ).scalar_one()

        if not team_invite_links_exists:
            connection.execute(
                text(
                    f"""
                    CREATE TABLE team_invite_links (
                        id {team_id_sql_type} NOT NULL AUTO_INCREMENT,
                        team_id {team_id_sql_type} NOT NULL,
                        inviter_id {user_id_sql_type} NOT NULL,
                        invite_token VARCHAR(128) NOT NULL,
                        expires_at DATETIME NOT NULL,
                        revoked TINYINT(1) NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        UNIQUE KEY uk_team_invite_links_token (invite_token),
                        KEY ix_team_invite_links_team_id (team_id),
                        KEY ix_team_invite_links_inviter_id (inviter_id),
                        KEY ix_team_invite_links_expires_at (expires_at),
                        CONSTRAINT fk_team_invite_links_team_id FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE CASCADE,
                        CONSTRAINT fk_team_invite_links_inviter_id FOREIGN KEY (inviter_id) REFERENCES users (id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                )
            )


def _ensure_mysql_ai_assistant_features() -> None:
    with engine.begin() as connection:
        user_id_raw_type = connection.execute(
            text(
                """
                SELECT COLUMN_TYPE
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = 'users'
                  AND column_name = 'id'
                LIMIT 1
                """
            )
        ).scalar_one_or_none()
        user_id_sql_type = _normalize_mysql_id_type(user_id_raw_type)

        if not re.fullmatch(r"[A-Z ]+", user_id_sql_type):
            raise RuntimeError("Invalid MySQL users.id type while ensuring AI assistant features")

        connection.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS conversations (
                    id {user_id_sql_type} NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    user_id {user_id_sql_type} NOT NULL,
                    title VARCHAR(255) DEFAULT '新对话',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_updated_at (updated_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        )

        connection.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id {user_id_sql_type} NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    conversation_id {user_id_sql_type} NOT NULL,
                    role ENUM('user', 'assistant') NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    INDEX idx_conversation_id (conversation_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_conversation_created (conversation_id, created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        )


def _ensure_mysql_processing_jobs() -> None:
    with engine.begin() as connection:
        exists = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = 'processing_jobs'
                """
            )
        ).scalar_one()

        if not exists:
            meeting_id_raw = connection.execute(
                text(
                    """
                    SELECT COLUMN_TYPE FROM information_schema.columns
                    WHERE table_schema = DATABASE() AND table_name = 'meetings' AND column_name = 'id' LIMIT 1
                    """
                )
            ).scalar_one_or_none()
            user_id_raw = connection.execute(
                text(
                    """
                    SELECT COLUMN_TYPE FROM information_schema.columns
                    WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'id' LIMIT 1
                    """
                )
            ).scalar_one_or_none()

            meeting_id_type = _normalize_mysql_id_type(meeting_id_raw)
            user_id_type = _normalize_mysql_id_type(user_id_raw)

            if not re.fullmatch(r"[A-Z ]+", meeting_id_type) or not re.fullmatch(r"[A-Z ]+", user_id_type):
                raise RuntimeError("Invalid MySQL id type detected while ensuring processing_jobs")

            connection.execute(
                text(
                    f"""
                    CREATE TABLE processing_jobs (
                        id {meeting_id_type} NOT NULL AUTO_INCREMENT,
                        job_id VARCHAR(36) NOT NULL,
                        meeting_id {meeting_id_type} NOT NULL,
                        user_id {user_id_type} NOT NULL,
                        job_type VARCHAR(20) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        progress FLOAT NOT NULL DEFAULT 0.0,
                        message VARCHAR(500) NOT NULL DEFAULT '',
                        current_chunk INT UNSIGNED NOT NULL DEFAULT 0,
                        total_chunks INT UNSIGNED NOT NULL DEFAULT 1,
                        result_json TEXT NULL,
                        error TEXT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        started_at DATETIME NULL,
                        completed_at DATETIME NULL,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        UNIQUE KEY uk_processing_jobs_job_id (job_id),
                        KEY idx_processing_jobs_meeting_id (meeting_id),
                        KEY idx_processing_jobs_user_id (user_id),
                        KEY idx_processing_jobs_status (status),
                        CONSTRAINT fk_processing_jobs_meeting_id FOREIGN KEY (meeting_id)
                            REFERENCES meetings(id) ON UPDATE CASCADE ON DELETE CASCADE,
                        CONSTRAINT fk_processing_jobs_user_id FOREIGN KEY (user_id)
                            REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                )
            )


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.include_router(ai.router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    """处理应用自定义错误。"""
    status_code = _error_code_to_status_code(exc.error_code)
    logger.error(
        "Application error: %s (code: %s)",
        exc.message,
        exc.error_code.value,
        extra={"details": exc.details, "suggestion": exc.suggestion},
    )
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(LLMServiceError)
@app.exception_handler(WhisperServiceError)
async def handle_ai_service_error(_: Request, exc: Exception) -> JSONResponse:
    """处理 AI 服务错误。"""
    logger.exception("AI service error", exc_info=exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "AI 服务暂时不可用，请稍后重试",
            "error_code": ErrorCode.AI_SERVICE_UNAVAILABLE.value,
            "suggestion": "系统将自动使用备用方案处理您的请求，或请稍后重试",
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理请求验证错误。"""
    errors = exc.errors()
    user_message = "请求参数校验失败"
    if errors and len(errors) > 0:
        first_error = errors[0]
        if "msg" in first_error:
            user_message = f"参数校验失败: {first_error['msg']}"
        elif "loc" in first_error:
            field = ".".join(str(x) for x in first_error["loc"])
            user_message = f"参数 {field} 校验失败"

    return JSONResponse(
        status_code=422,
        content={
            "detail": user_message,
            "error_code": ErrorCode.REQUEST_VALIDATION_ERROR.value,
            "errors": errors,
        },
    )


def _error_code_to_status_code(error_code: ErrorCode) -> int:
    """将错误码映射为 HTTP 状态码。"""
    status_map = {
        ErrorCode.BAD_REQUEST: 400,
        ErrorCode.UNAUTHORIZED: 401,
        ErrorCode.FORBIDDEN: 403,
        ErrorCode.NOT_FOUND: 404,
        ErrorCode.CONFLICT: 409,
        ErrorCode.REQUEST_VALIDATION_ERROR: 422,
        ErrorCode.TOO_MANY_REQUESTS: 429,
        ErrorCode.GPU_OUT_OF_MEMORY: 507,
        ErrorCode.GPU_NOT_AVAILABLE: 503,
        ErrorCode.GPU_PROCESSING_FAILED: 500,
        ErrorCode.MODEL_LOADING_TIMEOUT: 504,
        ErrorCode.MODEL_LOADING_FAILED: 500,
        ErrorCode.MODEL_NOT_FOUND: 404,
        ErrorCode.TRANSCRIPTION_FAILED: 500,
        ErrorCode.TRANSCRIPTION_TIMEOUT: 504,
        ErrorCode.AUDIO_PROCESSING_FAILED: 500,
        ErrorCode.INVALID_AUDIO_FORMAT: 400,
        ErrorCode.SPEAKER_DIARIZATION_FAILED: 500,
        ErrorCode.SPEAKER_DIARIZATION_TIMEOUT: 504,
        ErrorCode.AI_SERVICE_UNAVAILABLE: 503,
        ErrorCode.LLM_TIMEOUT: 504,
        ErrorCode.LLM_RATE_LIMITED: 429,
        ErrorCode.NETWORK_TIMEOUT: 504,
        ErrorCode.NETWORK_ERROR: 502,
    }
    return status_map.get(error_code, 500)


def _default_error_code_for_status(status_code: int) -> ErrorCode:
    """根据 HTTP 状态码返回默认错误码。"""
    if status_code == 400:
        return ErrorCode.BAD_REQUEST
    if status_code == 401:
        return ErrorCode.UNAUTHORIZED
    if status_code == 403:
        return ErrorCode.FORBIDDEN
    if status_code == 404:
        return ErrorCode.NOT_FOUND
    if status_code == 409:
        return ErrorCode.CONFLICT
    if status_code == 422:
        return ErrorCode.REQUEST_VALIDATION_ERROR
    if status_code == 429:
        return ErrorCode.TOO_MANY_REQUESTS
    if 400 <= status_code < 500:
        return ErrorCode.CLIENT_ERROR
    return ErrorCode.INTERNAL_SERVER_ERROR


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    """处理 HTTP 异常。"""
    detail = exc.detail
    error_code: ErrorCode | None = None

    if isinstance(detail, dict):
        maybe_error_code = detail.get("error_code")
        if isinstance(maybe_error_code, str):
            try:
                error_code = ErrorCode(maybe_error_code)
            except ValueError:
                pass
        detail = detail.get("detail", detail)

    if error_code is None:
        error_code = _default_error_code_for_status(exc.status_code)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": detail,
            "error_code": error_code.value,
        },
        headers=exc.headers,
    )


@app.exception_handler(RateLimitExceeded)
async def handle_rate_limit(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    """处理速率限制错误。"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "请求过于频繁，请稍后重试",
            "error_code": ErrorCode.TOO_MANY_REQUESTS.value,
            "suggestion": "请等待片刻后再试，或联系管理员提高配额",
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    """处理未预期的错误。"""
    logger.exception("Unhandled server error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误，请稍后重试",
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "suggestion": "如果问题持续，请联系管理员并提供错误详情",
        },
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """服务健康检查接口。"""

    return {"status": "ok"}
