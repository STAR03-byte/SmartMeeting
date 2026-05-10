"""会议主题相关 Schema。"""

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class MeetingTopicCreate(BaseModel):
    """创建会议主题请求。"""

    meeting_id: int
    topic: str = Field(..., min_length=1, max_length=200)
    relevance_score: float = Field(default=1.0, ge=0, le=1)


class MeetingTopicOut(BaseModel):
    """会议主题响应。"""

    id: int
    meeting_id: int
    topic: str
    relevance_score: float | None
    created_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class MeetingTopicListOut(BaseModel):
    """会议主题列表响应。"""

    items: list[MeetingTopicOut]
    total: int
