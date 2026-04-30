"""LLM 服务层 — 向后兼容的重导出 shim。

所有实现已迁移至 app.services.ai.llm 包。
外部调用方的 import 路径无需变更。
"""

from app.services.ai.llm.exceptions import LLMServiceError
from app.services.ai.llm.types import (
    BatchedExtractedTask,
    ExtractedTask,
    SuggestedRelatedTask,
    TaskSuggestions,
)
from app.services.ai.llm.provider import LLMProviderConfig, build_provider_chain
from app.services.ai.llm.client import LLMClient
from app.services.ai.llm.fallbacks import (
    generate_fallback_structured_summary,
    generate_fallback_summary,
    generate_fallback_tasks,
)
from app.schemas.structured_summary import StructuredSummary

# ── 模块级单例 ──────────────────────────────────────────────
llm_client = LLMClient()


# ── 模块级便捷函数（委托给 llm_client）──────────────────────
async def generate_meeting_summary(
    transcript_contents: list[str],
    meeting_title: str | None = None,
) -> str:
    return await llm_client.generate_meeting_summary(transcript_contents, meeting_title)


async def generate_structured_summary(
    transcript_contents: list[tuple[str | None, str]],
    meeting_title: str | None = None,
) -> StructuredSummary:
    return await llm_client.generate_structured_summary(transcript_contents, meeting_title)


async def extract_action_items(
    transcript_content: str,
    participants: list[str] | None = None,
) -> list[ExtractedTask]:
    return await llm_client.extract_action_items(transcript_content, participants)


async def extract_action_items_for_batch(
    transcript_contents: list[str],
    participants: list[str] | None = None,
) -> list[BatchedExtractedTask]:
    return await llm_client.extract_action_items_for_batch(transcript_contents, participants)


__all__ = [
    "LLMServiceError",
    "LLMProviderConfig",
    "LLMClient",
    "ExtractedTask",
    "BatchedExtractedTask",
    "SuggestedRelatedTask",
    "TaskSuggestions",
    "build_provider_chain",
    "generate_fallback_summary",
    "generate_fallback_structured_summary",
    "generate_fallback_tasks",
    "llm_client",
    "generate_meeting_summary",
    "generate_structured_summary",
    "extract_action_items",
    "extract_action_items_for_batch",
]
