"""LLM 服务包 - 向后兼容的重导出。"""

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
]
