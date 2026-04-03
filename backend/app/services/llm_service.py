"""LLM 服务层 - 支持会议摘要生成与任务提取。"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Literal, TypedDict, cast

from openai import APIConnectionError, APIError, AsyncOpenAI, OpenAIError, RateLimitError
from openai.types.chat import ChatCompletionMessageParam

from app.core.config import settings
from app.schemas.structured_summary import AgendaItem, Resolution, StructuredSummary, TodoItem

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """LLM 服务异常。"""


@dataclass(frozen=True)
class LLMProviderConfig:
    name: str
    model: str
    base_url: str | None
    api_key: str | None
    timeout: int
    temperature: float
    max_tokens: int


def _build_provider_chain() -> list[LLMProviderConfig]:
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


class ExtractedTask(TypedDict):
    title: str
    description: str
    assignee_name: str | None
    priority: str
    due_hint: str | None


class LLMClient:
    """LLM 客户端封装。"""

    def __init__(self) -> None:
        self._clients: dict[str, AsyncOpenAI] = {}

    def _ensure_client(self, provider: LLMProviderConfig) -> AsyncOpenAI:
        if provider.name not in self._clients:
            if provider.name == "mock":
                raise LLMServiceError("Mock provider does not create a real client")
            try:
                if provider.api_key is not None:
                    self._clients[provider.name] = AsyncOpenAI(
                        api_key=provider.api_key,
                        base_url=provider.base_url,
                        timeout=provider.timeout,
                    )
                else:
                    self._clients[provider.name] = AsyncOpenAI(
                        base_url=provider.base_url,
                        timeout=provider.timeout,
                    )
            except OpenAIError as exc:
                raise LLMServiceError(f"LLM client init failed: {exc}") from exc
        return self._clients[provider.name]

    async def _call_chat(
        self,
        messages: list[ChatCompletionMessageParam],
        provider: LLMProviderConfig,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if provider.name == "mock":
            raise LLMServiceError("Mock provider uses rule fallback")
        client = self._ensure_client(provider)
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await client.chat.completions.create(
                    model=provider.model,
                    messages=messages,
                    temperature=temperature if temperature is not None else provider.temperature,
                    max_tokens=max_tokens if max_tokens is not None else provider.max_tokens,
                )
                content = response.choices[0].message.content
                return content or ""
            except (APIConnectionError, RateLimitError) as exc:
                last_error = exc
                if attempt == 2:
                    logger.error("LLM transient error after retries: %s", exc)
                    raise LLMServiceError(f"LLM transient error: {exc}") from exc
            except APIError as exc:
                logger.error("LLM API error: %s", exc)
                raise LLMServiceError(f"LLM API error: {exc}") from exc

        if last_error is not None:
            raise LLMServiceError(f"LLM transient error: {last_error}") from last_error
        raise LLMServiceError("LLM request failed")

    async def _call_with_fallback(
        self,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[str, str]:
        errors: list[str] = []
        for provider in _build_provider_chain():
            try:
                return (
                    await self._call_chat(
                        messages,
                        provider=provider,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    provider.name,
                )
            except LLMServiceError as exc:
                errors.append(f"{provider.name}: {exc}")
                logger.warning("LLM provider failed, trying fallback: %s", exc)

        raise LLMServiceError("; ".join(errors) if errors else "LLM request failed")

    async def generate_meeting_summary(
        self,
        transcript_contents: list[str],
        meeting_title: str | None = None,
    ) -> str:
        if not transcript_contents:
            return ""

        full_transcript = "\n\n".join(
            f"[片段{i + 1}] {content}" for i, content in enumerate(transcript_contents)
        )

        system_prompt = (
            "你是一个专业的会议记录助手。你的任务是根据会议转写内容生成结构化的会议摘要。\n\n"
            "摘要格式要求：\n"
            "1. **会议主题**：一句话概括会议核心内容\n"
            "2. **主要讨论**：列出3-5个关键讨论点\n"
            "3. **重要决定**：列出会议达成的决定（如有）\n"
            "4. **后续行动**：列出需要跟进的事项（如有）\n\n"
            "请用简洁专业的语言撰写，总字数控制在200-500字。"
        )
        user_prompt = (
            f"请为以下会议转写内容生成摘要：\n\n会议标题：{meeting_title or '未命名会议'}"
            f"\n\n转写内容：\n{full_transcript}\n\n请生成会议摘要："
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        content, _provider = await self._call_with_fallback(messages)
        return content

    async def generate_structured_summary(
        self,
        transcript_contents: list[tuple[str | None, str]],
        meeting_title: str | None = None,
    ) -> StructuredSummary:
        """Generate structured summary with agenda, resolutions, and todos."""
        if not transcript_contents:
            return StructuredSummary(agenda=[], resolutions=[], todos=[], raw_summary=None)

        formatted_transcript = "\n\n".join(
            f"[{speaker or '未知'}]: {content}"
            for speaker, content in transcript_contents
        )

        system_prompt = """你是一个专业的会议记录助手。请根据会议转写内容生成结构化的会议摘要。

输出格式要求（必须是有效的JSON）：
{
  "agenda": [
    {
      "topic": "讨论主题（必填，不超过100字）",
      "speaker": "发言人姓名（可选）",
      "key_points": ["要点1", "要点2"]
    }
  ],
  "resolutions": [
    {
      "decision": "决议内容（必填，不超过200字）",
      "proposer": "提议人（可选）",
      "context": "决议背景（可选）"
    }
  ],
  "todos": [
    {
      "title": "任务标题（必填，不超过50字）",
      "description": "任务描述（可选）",
      "assignee": "负责人姓名（可选）",
      "due_date": "截止时间（可选，如'下周一'）",
      "priority": "high/medium/low"
    }
  ]
}

要求：
1. agenda（议程）：列出会议讨论的主要话题，每个话题包含主题、发言人和关键要点
2. resolutions（决议）：列出会议达成的明确决定，包含决议内容、提议人和背景
3. todos（待办）：列出需要跟进的任务，包含标题、描述、负责人、截止时间和优先级
4. 如果某类信息不存在，对应数组为空
5. 只输出JSON，不要其他内容"""

        user_prompt = f"""请为以下会议转写内容生成结构化摘要：

会议标题：{meeting_title or '未命名会议'}

转写内容：
{formatted_transcript}

请输出JSON格式的结构化摘要："""

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response, _provider = await self._call_with_fallback(messages, temperature=0.1)
            parsed = self._parse_structured_summary(response)
            return parsed
        except (json.JSONDecodeError, LLMServiceError) as exc:
            logger.warning("Failed to generate structured summary: %s", exc)
            raw_summary = await self.generate_meeting_summary(
                [content for _, content in transcript_contents],
                meeting_title,
            )
            return generate_fallback_structured_summary(
                [content for _, content in transcript_contents],
                meeting_title,
                raw_summary,
            )

    def _parse_structured_summary(self, response: str) -> StructuredSummary:
        """Parse LLM response into StructuredSummary."""
        json_match = re.search(r"\{[\s\S]*\}", response)
        if not json_match:
            raise json.JSONDecodeError("No JSON object found", response, 0)

        json_str = json_match.group()
        data = json.loads(json_str)

        agenda: list[AgendaItem] = []
        for item in data.get("agenda", []):
            if not isinstance(item, dict):
                continue
            topic = item.get("topic")
            if not isinstance(topic, str) or not topic.strip():
                continue
            speaker = item.get("speaker")
            key_points = item.get("key_points", [])
            if not isinstance(key_points, list):
                key_points = []
            key_points = [str(p) for p in key_points if isinstance(p, str)]
            agenda.append(
                AgendaItem(
                    topic=topic.strip(),
                    speaker=speaker if isinstance(speaker, str) else None,
                    key_points=key_points,
                )
            )

        resolutions: list[Resolution] = []
        for item in data.get("resolutions", []):
            if not isinstance(item, dict):
                continue
            decision = item.get("decision")
            if not isinstance(decision, str) or not decision.strip():
                continue
            proposer = item.get("proposer")
            context = item.get("context")
            resolutions.append(
                Resolution(
                    decision=decision.strip(),
                    proposer=proposer if isinstance(proposer, str) else None,
                    context=context if isinstance(context, str) else None,
                )
            )

        todos: list[TodoItem] = []
        for item in data.get("todos", []):
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            if not isinstance(title, str) or not title.strip():
                continue
            description = item.get("description")
            assignee = item.get("assignee")
            due_date = item.get("due_date")
            priority = item.get("priority", "medium")
            if priority not in ("high", "medium", "low"):
                priority = "medium"
            todos.append(
                TodoItem(
                    title=title.strip(),
                    description=description if isinstance(description, str) else None,
                    assignee=assignee if isinstance(assignee, str) else None,
                    due_date=due_date if isinstance(due_date, str) else None,
                    priority=priority,
                )
            )

        return StructuredSummary(
            agenda=agenda,
            resolutions=resolutions,
            todos=todos,
            raw_summary=None,
        )

    async def extract_action_items(
        self,
        transcript_content: str,
        participants: list[str] | None = None,
    ) -> list[ExtractedTask]:
        if not transcript_content.strip():
            return []

        participants_context = (
            f"\n\n会议参与者：{', '.join(participants)}" if participants else ""
        )
        system_prompt = (
            "你是一个任务提取助手。从会议转写中提取行动项/任务。\n\n"
            "输出格式：JSON数组，每个任务包含：\n"
            "- title: 任务标题（简洁，不超过50字）\n"
            "- description: 任务详细描述\n"
            "- assignee_name: 负责人姓名（如果能从内容推断，否则为null）\n"
            "- priority: 优先级（high/medium/low）\n"
            "- due_hint: 截止时间提示（如果提到，否则为null）\n\n"
            "示例输出：\n"
            "[{\"title\": \"完成项目报告\", \"description\": \"下周一前提交项目进度报告\", "
            "\"assignee_name\": \"张三\", \"priority\": \"high\", \"due_hint\": \"下周一\"}]\n\n"
            f"只输出JSON数组，不要其他内容。{participants_context}"
        )
        user_prompt = (
            f"从以下会议转写中提取所有行动项：\n\n{transcript_content}\n\n输出JSON数组："
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response, _provider = await self._call_with_fallback(messages, temperature=0.1)
            parsed = cast(object, json.loads(response))
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse LLM response as JSON: %s", exc)
            return []

        if not isinstance(parsed, list):
            return []

        tasks: list[ExtractedTask] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            normalized_item = cast(dict[str, object], item)
            title = normalized_item.get("title")
            if not isinstance(title, str) or not title.strip():
                continue
            description = normalized_item.get("description")
            assignee_name = normalized_item.get("assignee_name")
            priority = normalized_item.get("priority")
            due_hint = normalized_item.get("due_hint")
            tasks.append(
                {
                    "title": title.strip(),
                    "description": description if isinstance(description, str) else title.strip(),
                    "assignee_name": assignee_name if isinstance(assignee_name, str) else None,
                    "priority": priority if isinstance(priority, str) else "medium",
                    "due_hint": due_hint if isinstance(due_hint, str) else None,
                }
            )
        return tasks

    async def health_check(self) -> bool:
        try:
            response = await self._call_with_fallback(
                [{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return bool(response[0])
        except Exception as exc:
            logger.error("LLM health check failed: %s", exc)
            return False


llm_client = LLMClient()


async def generate_meeting_summary(
    transcript_contents: list[str],
    meeting_title: str | None = None,
) -> str:
    return await llm_client.generate_meeting_summary(transcript_contents, meeting_title)


async def generate_structured_summary(
    transcript_contents: list[tuple[str | None, str]],
    meeting_title: str | None = None,
) -> StructuredSummary:
    """Generate structured summary with agenda, resolutions, and todos."""
    return await llm_client.generate_structured_summary(transcript_contents, meeting_title)


async def extract_action_items(
    transcript_content: str,
    participants: list[str] | None = None,
) -> list[ExtractedTask]:
    return await llm_client.extract_action_items(transcript_content, participants)


def generate_fallback_summary(transcript_contents: list[str], meeting_title: str | None) -> str:
    if not transcript_contents:
        return "暂无转写内容，无法生成摘要。"

    title = meeting_title or "未命名会议"
    content_preview = " ".join(transcript_contents[:5])
    if len(content_preview) > 200:
        content_preview = content_preview[:200] + "..."

    return (
        f"## {title}\n\n"
        f"**主要讨论**：{content_preview}\n\n"
        f"**后续行动**：请根据转写内容确认具体任务。"
    )


def generate_fallback_structured_summary(
    transcript_contents: list[str],
    meeting_title: str | None,
    raw_summary: str | None = None,
) -> StructuredSummary:
    """Generate fallback structured summary when LLM fails."""
    if not transcript_contents:
        return StructuredSummary(agenda=[], resolutions=[], todos=[], raw_summary=None)

    title = meeting_title or "未命名会议"
    content_preview = " ".join(transcript_contents[:5])
    if len(content_preview) > 200:
        content_preview = content_preview[:200] + "..."

    agenda: list[AgendaItem] = [
        AgendaItem(
            topic=f"会议主题：{title}",
            speaker=None,
            key_points=[content_preview[:100]],
        )
    ]

    todos: list[TodoItem] = []
    sentences = [s.strip() for s in " ".join(transcript_contents).split("。") if s.strip()]
    for sentence in sentences[:3]:
        priority: Literal["high", "medium", "low"] = "medium"
        if any(kw in sentence for kw in ["尽快", "紧急", "立即"]):
            priority = "high"
        elif any(kw in sentence for kw in ["下周", "月底", "后续"]):
            priority = "low"
        todos.append(
            TodoItem(
                title=sentence[:50],
                description=sentence,
                assignee=None,
                due_date=None,
                priority=priority,
            )
        )

    return StructuredSummary(
        agenda=agenda,
        resolutions=[],
        todos=todos,
        raw_summary=raw_summary or generate_fallback_summary(transcript_contents, meeting_title),
    )


def generate_fallback_tasks(transcript_content: str) -> list[ExtractedTask]:
    if not transcript_content.strip():
        return []

    sentences = [s.strip() for s in transcript_content.split("。") if s.strip()]
    tasks: list[ExtractedTask] = []

    for sentence in sentences[:3]:
        task: ExtractedTask = {
            "title": sentence[:50],
            "description": sentence,
            "assignee_name": None,
            "priority": "medium",
            "due_hint": None,
        }
        if any(kw in sentence for kw in ["尽快", "紧急", "立即"]):
            task["priority"] = "high"
        elif any(kw in sentence for kw in ["下周", "月底", "后续"]):
            task["priority"] = "low"
        tasks.append(task)

    return tasks