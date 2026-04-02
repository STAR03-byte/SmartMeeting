"""会议转写 Schema 定义。"""

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class MeetingTranscriptCreate(BaseModel):
    """创建转写请求。"""

    meeting_id: int
    speaker_user_id: int | None = None
    speaker_id: int | None = None
    speaker_name: str | None = Field(default=None, max_length=100)
    segment_index: int = Field(..., ge=1)
    start_time_sec: float | None = None
    end_time_sec: float | None = None
    language_code: str = Field(default="zh-CN", max_length=10)
    source: str = Field(default="whisper")
    content: str = Field(..., min_length=1)


class MeetingTranscriptUpdate(BaseModel):
    """更新转写请求。"""

    speaker_user_id: int | None = None
    speaker_id: int | None = None
    speaker_name: str | None = Field(default=None, max_length=100)
    start_time_sec: float | None = None
    end_time_sec: float | None = None
    language_code: str | None = Field(default=None, max_length=10)
    source: str | None = None
    content: str | None = Field(default=None, min_length=1)


class MeetingTranscriptOut(BaseModel):
    """转写响应。"""

    id: int
    meeting_id: int
    speaker_user_id: int | None
    speaker_id: int | None
    speaker_name: str | None
    segment_index: int
    start_time_sec: float | None
    end_time_sec: float | None
    language_code: str
    source: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class MeetingTranscriptListOut(BaseModel):
    items: list[MeetingTranscriptOut]
    total: int
