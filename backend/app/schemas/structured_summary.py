"""结构化摘要 Schema 定义。"""

from datetime import date
from typing import ClassVar, Literal

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class AgendaItem(BaseModel):
    """议程项。"""

    topic: str = Field(..., min_length=1, max_length=500, description="讨论主题")
    speaker: str | None = Field(default=None, max_length=100, description="发言人")
    key_points: list[str] = Field(default_factory=list, description="关键要点")


class Resolution(BaseModel):
    """决议项。"""

    decision: str = Field(..., min_length=1, max_length=500, description="决议内容")
    proposer: str | None = Field(default=None, max_length=100, description="提议人")
    context: str | None = Field(default=None, max_length=1000, description="决议背景")


class TodoItem(BaseModel):
    """待办事项。"""

    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: str | None = Field(default=None, max_length=1000, description="任务描述")
    assignee: str | None = Field(default=None, max_length=100, description="负责人")
    due_date: str | None = Field(default=None, max_length=100, description="截止时间提示")
    priority: Literal["high", "medium", "low"] = Field(default="medium", description="优先级")


class StructuredSummary(BaseModel):
    """结构化会议摘要。"""

    agenda: list[AgendaItem] = Field(default_factory=list, description="议程列表")
    resolutions: list[Resolution] = Field(default_factory=list, description="决议列表")
    todos: list[TodoItem] = Field(default_factory=list, description="待办事项列表")
    raw_summary: str | None = Field(default=None, description="原始摘要文本（用于回退显示）")

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class StructuredSummaryOut(BaseModel):
    """结构化摘要响应。"""

    meeting_id: int
    structured_summary: StructuredSummary
    has_structured_data: bool = Field(
        ..., description="是否有有效的结构化数据"
    )