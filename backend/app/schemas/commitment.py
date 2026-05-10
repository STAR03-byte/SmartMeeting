"""承诺相关 Schema。"""

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class CommitmentCreate(BaseModel):
    """创建承诺请求。"""

    meeting_id: int
    content: str = Field(..., min_length=1, max_length=5000)
    assignee_name: str | None = None
    assignee_user_id: int | None = None
    due_hint: str | None = None
    linked_task_id: int | None = None


class CommitmentUpdate(BaseModel):
    """更新承诺请求。"""

    content: str | None = Field(default=None, min_length=1, max_length=5000)
    assignee_name: str | None = None
    assignee_user_id: int | None = None
    due_hint: str | None = None
    status: str | None = None
    linked_task_id: int | None = None


class CommitmentOut(BaseModel):
    """承诺响应。"""

    id: int
    meeting_id: int
    content: str
    assignee_name: str | None
    assignee_user_id: int | None
    due_hint: str | None
    status: str
    linked_task_id: int | None
    created_at: datetime
    updated_at: datetime
    confirmed_at: datetime | None

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class CommitmentListOut(BaseModel):
    """承诺列表响应。"""

    items: list[CommitmentOut]
    total: int
