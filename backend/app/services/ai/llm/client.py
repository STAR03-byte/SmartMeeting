"""LLM 客户端 — Provider 管理与领域方法。"""

import json
import logging
import re
from collections.abc import AsyncGenerator
from typing import cast

from openai import APIConnectionError, APIError, AsyncOpenAI, OpenAIError, RateLimitError
from openai.types.chat import ChatCompletionMessageParam

from app.core.config import settings
from app.schemas.structured_summary import AgendaItem, Resolution, StructuredSummary, TodoItem
from app.services.business.task_service import is_actionable_task_text
from app.services.ai.llm.exceptions import LLMServiceError
from app.services.ai.llm.provider import LLMProviderConfig, build_provider_chain
from app.services.ai.llm.types import (
    BatchedExtractedTask,
    ExtractedTask,
    SuggestedRelatedTask,
    TaskSuggestions,
)

logger = logging.getLogger(__name__)


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

    async def _call_chat_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        provider: LLMProviderConfig,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        if provider.name == "mock":
            raise LLMServiceError("Mock provider uses rule fallback")
        client = self._ensure_client(provider)
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                stream = await client.chat.completions.create(
                    model=provider.model,
                    messages=messages,
                    temperature=temperature if temperature is not None else provider.temperature,
                    max_tokens=max_tokens if max_tokens is not None else provider.max_tokens,
                    stream=True,
                )
                async for chunk in stream:
                    for choice in chunk.choices:
                        delta = choice.delta.content
                        if delta:
                            yield delta
                return
            except (APIConnectionError, RateLimitError) as exc:
                last_error = exc
                if attempt == 2:
                    logger.error("LLM stream transient error after retries: %s", exc)
                    raise LLMServiceError(f"LLM transient error: {exc}") from exc
            except APIError as exc:
                logger.error("LLM stream API error: %s", exc)
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
        for provider in build_provider_chain():
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

    async def _call_with_fallback_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        errors: list[str] = []
        for provider in build_provider_chain():
            try:
                async for chunk in self._call_chat_stream(
                    messages,
                    provider=provider,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    yield chunk
                return
            except LLMServiceError as exc:
                errors.append(f"{provider.name}: {exc}")
                logger.warning("LLM stream provider failed, trying fallback: %s", exc)

        raise LLMServiceError("; ".join(errors) if errors else "LLM request failed")

    # ── 领域方法 ──────────────────────────────────────────────

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

        from app.services.ai.prompts.meeting_summary import (
            MEETING_SUMMARY_SYSTEM_PROMPT,
            build_meeting_summary_user_prompt,
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": MEETING_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": build_meeting_summary_user_prompt(meeting_title or "", full_transcript)},
        ]
        content, _provider = await self._call_with_fallback(messages, temperature=0.2)
        return content

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        context_info: dict[str, str] | None = None,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """多轮对话补全。"""
        from app.services.ai.prompts.chat_system import build_chat_system_prompt

        system_prompt = build_chat_system_prompt(context_info)

        full_messages = cast(
            list[ChatCompletionMessageParam],
            [{"role": "system", "content": system_prompt}] + messages,
        )

        if stream:
            return self._call_with_fallback_stream(
                messages=full_messages,
                temperature=0.7,
            )

        response, _provider = await self._call_with_fallback(
            messages=full_messages,
            temperature=0.7,
        )
        return response

    def _extract_json_from_response(self, response: str) -> dict[str, object] | None:
        response = response.strip()

        try:
            return cast(dict[str, object], json.loads(response))
        except json.JSONDecodeError:
            pass

        json_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    return cast(dict[str, object], json.loads(match.strip()))
                except json.JSONDecodeError:
                    continue

        return None

    async def generate_task_suggestions(
        self,
        title: str,
        description: str,
        meeting_context: str | None = None,
    ) -> TaskSuggestions:
        """生成任务建议。"""
        prompt = f"分析以下任务并提供执行建议：\n\n任务标题：{title}\n任务描述：{description}"

        if meeting_context:
            prompt += f"\n\n会议上下文：{meeting_context}"

        prompt += (
            '\n\n请提供以下信息（JSON 格式）：\n'
            '{\n    "steps": ["步骤1", "步骤2", ...],\n'
            '    "risks": ["风险1", "风险2", ...],\n'
            '    "suggested_roles": ["角色1", "角色2", ...],\n'
            '    "related_tasks": [{"id": 1, "title": "相关任务1"}, ...]\n'
            '}\n\n注意：直接返回JSON对象，不要添加markdown代码块标记或其他说明文字。'
        )

        response, provider = await self._call_with_fallback(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        default_result: TaskSuggestions = {
            "steps": [],
            "risks": [],
            "suggested_roles": [],
            "related_tasks": [],
        }

        parsed = self._extract_json_from_response(response)

        if parsed is None:
            logger.warning(
                f"Failed to parse task suggestions JSON from {provider} response. "
                f"Task title: {title[:50]}... Response preview: {response[:200]}..."
            )
            return {
                **default_result,
                "steps": ["AI建议生成失败，请稍后重试或手动填写任务信息"],
            }

        steps_raw = parsed.get("steps")
        risks_raw = parsed.get("risks")
        roles_raw = parsed.get("suggested_roles")
        related_raw = parsed.get("related_tasks")

        steps = [item for item in steps_raw if isinstance(item, str)] if isinstance(steps_raw, list) else []
        risks = [item for item in risks_raw if isinstance(item, str)] if isinstance(risks_raw, list) else []
        suggested_roles = [item for item in roles_raw if isinstance(item, str)] if isinstance(roles_raw, list) else []

        related_tasks: list[SuggestedRelatedTask] = []
        if isinstance(related_raw, list):
            for task in related_raw:
                if not isinstance(task, dict):
                    continue
                task_item = cast(dict[str, object], task)
                task_id = task_item.get("id")
                task_title = task_item.get("title")
                if isinstance(task_id, int) and isinstance(task_title, str):
                    related_tasks.append({"id": task_id, "title": task_title})

        return {
            "steps": steps,
            "risks": risks,
            "suggested_roles": suggested_roles,
            "related_tasks": related_tasks,
        }

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

        from app.services.ai.prompts.structured_summary import (
            STRUCTURED_SUMMARY_SYSTEM_PROMPT,
            build_structured_summary_user_prompt,
        )

        system_prompt = STRUCTURED_SUMMARY_SYSTEM_PROMPT
        user_prompt = build_structured_summary_user_prompt(meeting_title or "", formatted_transcript)

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
            from app.services.ai.llm.fallbacks import generate_fallback_structured_summary

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

        processed_todos = self._post_process_todos(todos)

        return StructuredSummary(
            agenda=agenda,
            resolutions=resolutions,
            todos=processed_todos,
            raw_summary=None,
        )

    def _post_process_todos(self, todos: list[TodoItem]) -> list[TodoItem]:
        if not settings.llm_enable_post_processing or len(todos) <= 1:
            return todos

        unique_todos: list[TodoItem] = []
        for todo in todos:
            is_duplicate = False
            for existing in unique_todos:
                similarity = self._calculate_task_similarity(todo.title, existing.title)
                if similarity >= settings.llm_task_similarity_threshold:
                    if self._is_task_more_complete(todo, existing):
                        unique_todos[unique_todos.index(existing)] = todo
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_todos.append(todo)

        validated_todos: list[TodoItem] = []
        for todo in unique_todos:
            if not todo.title or len(todo.title.strip()) < 3:
                continue
            if not is_actionable_task_text(todo.title):
                continue
            description = todo.description
            if description and description.strip() == todo.title.strip():
                description = None
            validated_todos.append(
                TodoItem(
                    title=todo.title.strip(),
                    description=description,
                    assignee=todo.assignee.strip() if todo.assignee else None,
                    due_date=self._normalize_due_date(todo.due_date),
                    priority=todo.priority if todo.priority in ("high", "medium", "low") else "medium",
                )
            )

        return validated_todos

    def _calculate_task_similarity(self, title1: str, title2: str) -> float:
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        if t1 == t2:
            return 1.0

        set1 = set(t1)
        set2 = set(t2)
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _is_task_more_complete(self, task1: TodoItem, task2: TodoItem) -> bool:
        score1 = sum([
            bool(task1.title),
            bool(task1.description),
            bool(task1.assignee),
            bool(task1.due_date),
        ])
        score2 = sum([
            bool(task2.title),
            bool(task2.description),
            bool(task2.assignee),
            bool(task2.due_date),
        ])
        return score1 >= score2

    def _normalize_due_date(self, due_date: str | None) -> str | None:
        if not due_date:
            return None

        due = due_date.strip()
        if not due:
            return None

        if re.match(r"^\d{4}-\d{2}-\d{2}$", due):
            return due

        from datetime import datetime, timedelta
        today = datetime.now()

        mapping: dict[str, str] = {
            "今天": today.strftime("%Y-%m-%d"),
            "今日": today.strftime("%Y-%m-%d"),
            "明天": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "明日": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "后天": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "本周": "本周内",
            "下周": "下周",
            "本月底": today.strftime("%Y-%m-底"),
            "月底": "月底",
        }

        for key, value in mapping.items():
            if key in due:
                return value

        day_match = re.search(r"(\d+)\s*天后", due)
        if day_match:
            days = int(day_match.group(1))
            return (today + timedelta(days=days)).strftime("%Y-%m-%d")

        return due

    async def extract_action_items(
        self,
        transcript_content: str,
        participants: list[str] | None = None,
    ) -> list[ExtractedTask]:
        if not transcript_content.strip():
            return []

        from app.services.ai.prompts.action_items import (
            build_action_items_system_prompt,
            build_action_items_user_prompt,
        )

        participants_context = (
            f"\n\n会议参与者：{', '.join(participants)}" if participants else ""
        )
        system_prompt = build_action_items_system_prompt(participants_context)
        user_prompt = build_action_items_user_prompt(transcript_content)

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

    async def extract_action_items_for_batch(
        self,
        transcript_contents: list[str],
        participants: list[str] | None = None,
    ) -> list[BatchedExtractedTask]:
        if not transcript_contents:
            return []

        numbered_transcripts = [
            f"[{index}] {content.strip()}" for index, content in enumerate(transcript_contents) if content.strip()
        ]
        if not numbered_transcripts:
            return []

        from app.services.ai.prompts.action_items import (
            build_action_items_batch_system_prompt,
            build_action_items_batch_user_prompt,
        )

        participants_context = (
            f"\n\n会议参与者：{', '.join(participants)}" if participants else ""
        )
        system_prompt = build_action_items_batch_system_prompt(participants_context)
        user_prompt = build_action_items_batch_user_prompt(numbered_transcripts)

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response, _provider = await self._call_with_fallback(messages, temperature=0.1)
            parsed = cast(object, json.loads(response))
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse batched LLM response as JSON: %s", exc)
            return []

        if not isinstance(parsed, list):
            return []

        tasks: list[BatchedExtractedTask] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            normalized_item = cast(dict[str, object], item)
            title = normalized_item.get("title")
            segment_index = normalized_item.get("segment_index")
            if not isinstance(title, str) or not title.strip() or not isinstance(segment_index, int):
                continue
            description = normalized_item.get("description")
            assignee_name = normalized_item.get("assignee_name")
            priority = normalized_item.get("priority")
            due_hint = normalized_item.get("due_hint")
            tasks.append(
                {
                    "segment_index": segment_index,
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
