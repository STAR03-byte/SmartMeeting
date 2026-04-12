"""LLM 服务层 - 支持会议摘要生成与任务提取。"""

import json
import logging
import re
from collections.abc import AsyncGenerator
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


class SuggestedRelatedTask(TypedDict):
    id: int
    title: str


class TaskSuggestions(TypedDict):
    steps: list[str]
    risks: list[str]
    suggested_roles: list[str]
    related_tasks: list[SuggestedRelatedTask]


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

        system_prompt = """你是一个专业的会议记录助手。你的任务是根据会议转写内容生成结构化的会议摘要。

请遵循以下原则：
1. 忠实记录：只记录转写中实际讨论的内容，不要编造
2. 结构清晰：按主题组织，便于快速浏览
3. 重点突出：标注关键决定和行动项
4. 简洁专业：去除口语化表达，保留核心信息

输出格式：
━━━━━━━━━━━━━━━━━━━━━━━━
📋 会议主题：[一句话概括核心议题]

👥 与会人员：[从转写中提取提到的参与者]

💬 主要讨论：
• [讨论点1：简要描述]
• [讨论点2：简要描述]
• [讨论点3：如有]

✅ 重要决定：
• [决定1：具体内容及决策人]
• [决定2：如有]

📝 后续行动：
• [行动项1] - [负责人] - [截止时间]
• [行动项2] - [负责人] - [截止时间]

💡 风险提示：[如有提及的风险或注意事项]
━━━━━━━━━━━━━━━━━━━━━━━━

示例：
📋 会议主题：Q4产品发布计划评审

👥 与会人员：张三（产品经理）、李四（技术负责人）、王五（设计）

💬 主要讨论：
• 发布时间节点：原定12月初，讨论后认为需延后至12月中旬
• 技术实现方案：微服务架构已就绪，需补充压力测试
• 设计资源：UI稿已完成80%，剩余交互细节待确认

✅ 重要决定：
• 发布日期确定为12月15日（张三决定）
• 压力测试必须在12月5日前完成（李四承诺）

📝 后续行动：
• 完成压力测试报告 - 李四 - 12月5日
• 提交最终UI稿 - 王五 - 11月30日
"""
        user_prompt = (
            f"请为以下会议转写内容生成摘要：\n\n会议标题：{meeting_title or '未命名会议'}"
            f"\n\n转写内容：\n{full_transcript}\n\n请按照上述格式生成结构化的会议摘要，务必忠实记录转写内容，不要添加转写中没有的信息。"
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
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
        system_prompt = """你是 SmartMeeting 的 AI 助理，帮助用户管理会议和任务。

重要提示：用户已通过界面选择了以下真实数据，这些数据来自 SmartMeeting 数据库，你有权访问并基于这些数据回答用户问题。不要说自己无法访问数据。"""
        
        if context_info:
            if "meeting_title" in context_info:
                system_prompt += f"\n\n【当前关联会议】\n标题：{context_info['meeting_title']}"
                if "meeting_description" in context_info:
                    system_prompt += f"\n描述：{context_info['meeting_description']}"
            
            if "task_title" in context_info:
                system_prompt += f"\n\n【当前关联任务】\n标题：{context_info['task_title']}"
                if "task_description" in context_info:
                    system_prompt += f"\n描述：{context_info['task_description']}"
                if "task_status" in context_info:
                    system_prompt += f"\n状态：{context_info['task_status']}"
                if "task_priority" in context_info:
                    system_prompt += f"\n优先级：{context_info['task_priority']}"
            
            if "task_not_found" in context_info:
                system_prompt += f"\n\n注意：{context_info['task_not_found']}"

        full_messages = cast(
            list[ChatCompletionMessageParam],
            [{"role": "system", "content": system_prompt}] + messages,
        )

        if stream:
            # TODO: 实现真正的流式响应（SSE/增量token）
            async def _single_chunk_generator() -> AsyncGenerator[str, None]:
                response, _provider = await self._call_with_fallback(
                    messages=full_messages,
                    temperature=0.7,
                )
                yield response

            return _single_chunk_generator()

        response, _provider = await self._call_with_fallback(
            messages=full_messages,
            temperature=0.7,
        )
        return response

    async def generate_task_suggestions(
        self,
        title: str,
        description: str,
        meeting_context: str | None = None,
    ) -> TaskSuggestions:
        """生成任务建议。"""
        prompt = f"""分析以下任务并提供执行建议：

任务标题：{title}
任务描述：{description}"""

        if meeting_context:
            prompt += f"\n\n会议上下文：{meeting_context}"

        prompt += """\n\n请提供以下信息（JSON 格式）：
{
    "steps": ["步骤1", "步骤2", ...],
    "risks": ["风险1", "风险2", ...],
    "suggested_roles": ["角色1", "角色2", ...],
    "related_tasks": [{"id": 1, "title": "相关任务1"}, ...]
}"""

        response, _provider = await self._call_with_fallback(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        default_result: TaskSuggestions = {
            "steps": [],
            "risks": [],
            "suggested_roles": [],
            "related_tasks": [],
        }

        try:
            parsed = cast(dict[str, object], json.loads(response))
        except json.JSONDecodeError:
            return default_result

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

        system_prompt = """你是一个专业的会议记录助手。请根据会议转写内容生成结构化的会议摘要。

输出格式要求（必须是有效的JSON，不要包含markdown代码块标记）：
{
  "agenda": [
    {
      "topic": "讨论主题（必填，从转写中提炼）",
      "speaker": "发言人姓名（可选，从转写中提取）",
      "key_points": ["要点1（简洁，20字内）", "要点2"]
    }
  ],
  "resolutions": [
    {
      "decision": "决议内容（必填，必须是会议明确达成的决定）",
      "proposer": "提议人（可选，从转写中提取）",
      "context": "决议背景（可选，简要说明）"
    }
  ],
  "todos": [
    {
      "title": "任务标题（必填，简洁明确）",
      "description": "任务描述（可选，补充上下文）",
      "assignee": "负责人姓名（从转写中提取，确保真实存在）",
      "due_date": "截止时间（可选，标准化格式如'2024-01-15'或'下周一'）",
      "priority": "high/medium/low（根据紧急程度判断：high-紧急/今天/立即，medium-本周，low-后续/月底）"
    }
  ]
}

提取规则（严格遵守）：
1. agenda：提取3-5个核心讨论主题，不要罗列所有对话
2. resolutions：只包含会议明确达成的决定，不要推测
3. todos：只提取转写中明确提到的任务，必须有action verb（完成、提交、审核等）
4. assignee：必须从转写中提取真实人名，不确定时留空
5. priority：
   - high: 今天、立即、尽快、紧急、截止
   - medium: 本周、下周、3天内
   - low: 月底、后续、待定

Few-shot示例：

输入："张三：我们需要在今天下班前完成API文档。李四：我来负责，明天上午可以提交初稿。王五：设计方案还需要一周时间。"

输出：
{
  "agenda": [
    {"topic": "API文档完成", "speaker": "张三", "key_points": ["今天下班前必须完成"]}
  ],
  "resolutions": [],
  "todos": [
    {"title": "完成API文档", "description": "编写完整的API接口文档", "assignee": "李四", "due_date": "明天上午", "priority": "high"},
    {"title": "完成设计方案", "description": "输出最终设计方案", "assignee": "王五", "due_date": "一周后", "priority": "medium"}
  ]
}
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

        # 对todos进行后处理：去重、校验、时间标准化
        processed_todos = self._post_process_todos(todos)

        return StructuredSummary(
            agenda=agenda,
            resolutions=resolutions,
            todos=processed_todos,
            raw_summary=None,
        )

    def _post_process_todos(self, todos: list[TodoItem]) -> list[TodoItem]:
        """对任务列表进行后处理：去重、校验、时间标准化。"""
        if not settings.llm_enable_post_processing or len(todos) <= 1:
            return todos

        # 1. 去重：基于标题相似度
        unique_todos: list[TodoItem] = []
        for todo in todos:
            is_duplicate = False
            for existing in unique_todos:
                similarity = self._calculate_task_similarity(todo.title, existing.title)
                if similarity >= settings.llm_task_similarity_threshold:
                    # 保留信息更完整的任务
                    if self._is_task_more_complete(todo, existing):
                        unique_todos[unique_todos.index(existing)] = todo
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_todos.append(todo)

        # 2. 校验与清理
        validated_todos: list[TodoItem] = []
        for todo in unique_todos:
            # 确保title不为空且长度合理
            if not todo.title or len(todo.title.strip()) < 3:
                continue
            # 清理description（如果与title重复）
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
        """计算两个任务标题的相似度（0-1）。"""
        # 简单的相似度计算：基于字符重叠和关键词匹配
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        if t1 == t2:
            return 1.0

        # 使用集合计算Jaccard相似度
        set1 = set(t1)
        set2 = set(t2)
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _is_task_more_complete(self, task1: TodoItem, task2: TodoItem) -> bool:
        """判断任务1是否比任务2信息更完整。"""
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
        """标准化截止时间表达。"""
        if not due_date:
            return None

        due = due_date.strip()
        if not due:
            return None

        # 如果已经是标准日期格式，直接返回
        import re
        if re.match(r"^\d{4}-\d{2}-\d{2}$", due):
            return due

        # 标准化常见表达
        from datetime import datetime, timedelta
        today = datetime.now()

        # 映射表
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

        # 处理"X天后"、"X天后"等相对时间
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
