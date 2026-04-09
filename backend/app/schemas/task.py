"""任务 Schema 定义。"""

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

TaskPriority = Literal["high", "medium", "low"]
TaskStatus = Literal["todo", "in_progress", "done"]


class TaskCreate(BaseModel):
    """创建任务请求。"""

    meeting_id: int
    transcript_id: int | None = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    assignee_id: int | None = None
    reporter_id: int | None = None
    priority: TaskPriority = Field(default="medium")
    status: TaskStatus = Field(default="todo")
    progress_note: str | None = None
    due_at: datetime | None = None
    reminder_at: datetime | None = None


class TaskUpdate(BaseModel):
    """更新任务请求。"""

    transcript_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    assignee_id: int | None = None
    reporter_id: int | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    progress_note: str | None = None
    due_at: datetime | None = None
    reminder_at: datetime | None = None
    completed_at: datetime | None = None


class TaskOut(BaseModel):
    """任务响应。"""

    id: int
    meeting_id: int
    meeting_title: str | None = None
    transcript_id: int | None
    title: str
    description: str | None
    assignee_id: int | None
    reporter_id: int | None
    priority: str
    status: str
    progress_note: str | None
    due_at: datetime | None
    reminder_at: datetime | None
    completed_at: datetime | None
    is_overdue: bool = False
    is_due_soon: bool = False
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class TaskListOut(BaseModel):
    items: list[TaskOut]
    total: int
