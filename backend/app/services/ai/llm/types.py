"""LLM 类型定义。"""

from typing import TypedDict


class ExtractedTask(TypedDict):
    title: str
    description: str
    assignee_name: str | None
    priority: str
    due_hint: str | None


class BatchedExtractedTask(ExtractedTask):
    segment_index: int


class SuggestedRelatedTask(TypedDict):
    id: int
    title: str


class TaskSuggestions(TypedDict):
    steps: list[str]
    risks: list[str]
    suggested_roles: list[str]
    related_tasks: list[SuggestedRelatedTask]
