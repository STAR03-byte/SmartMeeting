"""LLM Provider 配置与链构建。"""

import logging
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMProviderConfig:
    name: str
    model: str
    base_url: str | None
    api_key: str | None
    timeout: int
    temperature: float
    max_tokens: int


def build_provider_chain() -> list[LLMProviderConfig]:
    """构建有序的 LLM provider 列表（主 + 回退）。"""
    providers: list[LLMProviderConfig] = []

    def add_mock_provider() -> None:
        providers.append(
            LLMProviderConfig(
                name="mock",
                model="mock",
                base_url=None,
                api_key="mock",
                timeout=1,
                temperature=0.0,
                max_tokens=5,
            )
        )

    def add_openai_provider() -> None:
        api_key = settings.llm_api_key.strip() or None
        if api_key is None:
            logger.warning("Skipping OpenAI LLM provider because no API key is configured")
            return
        providers.append(
            LLMProviderConfig(
                name="openai",
                model=settings.llm_model,
                base_url=settings.llm_base_url or None,
                api_key=api_key,
                timeout=settings.llm_timeout,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        )

    def add_ollama_provider() -> None:
        base_url = settings.ollama_base_url.strip() or None
        if base_url is None:
            logger.warning("Skipping Ollama LLM provider because no base URL is configured")
            return
        providers.append(
            LLMProviderConfig(
                name="ollama",
                model=settings.ollama_model,
                base_url=base_url,
                api_key="ollama",
                timeout=settings.ollama_timeout,
                temperature=settings.ollama_temperature,
                max_tokens=settings.ollama_max_tokens,
            )
        )

    primary_provider = settings.llm_provider.strip().lower()
    fallback_provider = settings.llm_fallback_provider.strip().lower()

    if primary_provider == "openai":
        add_openai_provider()
    elif primary_provider == "ollama":
        add_ollama_provider()
    elif primary_provider == "mock":
        add_mock_provider()
    else:
        logger.warning("Unknown LLM_PROVIDER=%s; using rule-based fallback", settings.llm_provider)

    if fallback_provider == "openai" and primary_provider != "openai":
        add_openai_provider()
    elif fallback_provider == "ollama" and primary_provider != "ollama":
        add_ollama_provider()

    return providers
