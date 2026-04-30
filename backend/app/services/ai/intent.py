"""意图分类器 — 可扩展的协议 + 规则实现。"""

from __future__ import annotations

import logging
from typing import Literal, Protocol

logger = logging.getLogger(__name__)

AssistantIntent = Literal[
    "my_tasks",
    "meeting_tasks",
    "meeting_summary",
    "knowledge_query",
    "execution_advice",
    "general_chat",
]


class IntentClassifier(Protocol):
    """意图分类器协议，未来可替换为 LLM 分类器。"""

    def classify(self, message: str, context: dict[str, object] | None = None) -> AssistantIntent:
        ...


class RuleBasedIntentClassifier:
    """基于关键词匹配的规则分类器（当前实现）。"""

    def classify(self, message: str, context: dict[str, object] | None = None) -> AssistantIntent:
        normalized = message.strip().lower()
        has_meeting_context = isinstance(context, dict) and isinstance(context.get("meeting_id"), int)
        asks_for_meeting_summary = any(
            keyword in normalized
            for keyword in ("纪要", "总结", "摘要", "讲了什么", "会议内容", "决议", "决定")
        )

        if any(keyword in normalized for keyword in ("快到期", "即将到期", "近期截止")) and "任务" in normalized:
            return "my_tasks"
        if ("会议" in normalized or "会" in normalized) and any(keyword in normalized for keyword in ("任务", "行动项", "todo", "待办")):
            return "meeting_tasks"
        if any(keyword in normalized for keyword in ("我的任务", "我有哪些任务", "任务有什么", "待办", "进行中", "已完成")):
            return "my_tasks"
        if has_meeting_context and any(keyword in normalized for keyword in ("任务", "行动项", "todo", "待办")):
            return "meeting_tasks"
        if has_meeting_context and asks_for_meeting_summary:
            return "meeting_summary"
        if any(keyword in normalized for keyword in ("怎么做", "如何推进", "下一步", "执行", "推进")):
            return "execution_advice"
        if asks_for_meeting_summary:
            return "meeting_summary"
        if any(
            keyword in normalized
            for keyword in (
                "knowledge",
                "history",
                "project",
                "risk",
                "decision",
                "customer",
                "meeting",
                "会议",
                "项目",
                "风险",
                "决策",
                "决定",
                "客户",
                "历史",
            )
        ):
            return "knowledge_query"
        return "general_chat"


# ── 模块级分类器实例 ──────────────────────────────────────────
_classifier: IntentClassifier = RuleBasedIntentClassifier()


def get_intent_classifier() -> IntentClassifier:
    """获取当前意图分类器。"""
    return _classifier


def set_intent_classifier(classifier: IntentClassifier) -> None:
    """替换意图分类器（用于测试或运行时切换）。"""
    global _classifier
    _classifier = classifier
    logger.info("Intent classifier replaced: %s", type(classifier).__name__)
