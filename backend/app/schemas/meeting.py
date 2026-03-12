"""会议 Schema 定义。"""

from datetime import datetime

from pydantic import BaseModel, Field


class MeetingCreate(BaseModel):
    """创建会议请求。"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    organizer_id: int
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    location: str | None = Field(default=None, max_length=255)


class MeetingUpdate(BaseModel):
    """更新会议请求。"""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    location: str | None = Field(default=None, max_length=255)
    status: str | None = None


class MeetingOut(BaseModel):
    """会议响应。"""

    id: int
    title: str
    description: str | None
    organizer_id: int
    scheduled_start_at: datetime | None
    scheduled_end_at: datetime | None
    actual_start_at: datetime | None
    actual_end_at: datetime | None
    location: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
