"""规则回退生成器（不依赖 LLM 调用）。"""

from typing import Literal

from app.schemas.structured_summary import AgendaItem, StructuredSummary, TodoItem
from app.services.ai.llm.types import ExtractedTask


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
    """LLM 失败时的规则回退结构化摘要。"""
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
