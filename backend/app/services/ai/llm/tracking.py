"""LLM token 用量追踪工具。"""

import logging
from dataclasses import dataclass

from app.core.database import SessionLocal
from app.models.llm_usage import LLMUsage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def extract_usage_from_response(response: object) -> TokenUsage:
    """从 OpenAI ChatCompletion 响应对象提取 token 用量。"""
    usage = getattr(response, "usage", None)
    if usage is None:
        return TokenUsage()
    return TokenUsage(
        prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        total_tokens=getattr(usage, "total_tokens", 0) or 0,
    )


def record_usage(
    provider: str,
    model: str,
    operation: str,
    usage: TokenUsage,
) -> None:
    """持久化一条 token 用量记录。fire-and-forget，失败仅 log。"""
    try:
        db = SessionLocal()
        try:
            row = LLMUsage(
                provider=provider,
                model=model,
                operation=operation,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )
            db.add(row)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Failed to record LLM usage: %s", exc)
