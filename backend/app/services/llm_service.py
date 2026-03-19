"""LLM 服务层 - 支持会议摘要生成与任务提取。"""

import json
import logging
from typing import TypedDict, cast

from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError
from openai.types.chat import ChatCompletionMessageParam

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """LLM 服务异常。"""


class ExtractedTask(TypedDict):
    title: str
    description: str
    assignee_name: str | None
    priority: str
    due_hint: str | None


class LLMClient:
    """LLM 客户端封装。"""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._initialized: bool = False

    def _ensure_client(self) -> AsyncOpenAI:
        if not self._initialized:
            if not settings.llm_api_key:
                raise LLMServiceError("LLM API key not configured")
            self._client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url or None,
                timeout=settings.llm_timeout,
            )
            self._initialized = True
        if self._client is None:
            raise LLMServiceError("LLM client initialization failed")
        return self._client

    async def _call_chat(
        self,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        client = self._ensure_client()
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await client.chat.completions.create(
                    model=settings.llm_model,
                    messages=messages,
                    temperature=temperature if temperature is not None else settings.llm_temperature,
                    max_tokens=max_tokens if max_tokens is not None else settings.llm_max_tokens,
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
        return await self._call_chat(messages)

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
            response = await self._call_chat(messages, temperature=0.1)
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
            client = self._ensure_client()
            response = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return bool(response.choices)
        except Exception as exc:
            logger.error("LLM health check failed: %s", exc)
            return False


llm_client = LLMClient()


async def generate_meeting_summary(
    transcript_contents: list[str],
    meeting_title: str | None = None,
) -> str:
    return await llm_client.generate_meeting_summary(transcript_contents, meeting_title)


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
