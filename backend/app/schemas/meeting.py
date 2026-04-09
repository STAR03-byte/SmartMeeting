"""会议 Schema 定义。"""

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from app.schemas.meeting_transcript import MeetingTranscriptOut
from app.schemas.structured_summary import StructuredSummary
from app.schemas.task import TaskOut
from app.schemas.user import UserOut

MeetingStatus = Literal["planned", "ongoing", "done", "cancelled"]


class MeetingCreate(BaseModel):
    """创建会议请求。"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    organizer_id: int
    team_id: int | None = None
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
    status: MeetingStatus | None = None


class MeetingClearContentRequest(BaseModel):
    clear_transcripts: bool = True
    clear_tasks: bool = True
    clear_summary: bool = True
    clear_audios: bool = True
    reset_status: bool = True


class MeetingOut(BaseModel):
    """会议响应。"""

    id: int
    title: str
    description: str | None
    organizer_id: int
    team_id: int | None = None
    scheduled_start_at: datetime | None
    scheduled_end_at: datetime | None
    actual_start_at: datetime | None
    actual_end_at: datetime | None
    location: str | None
    status: str
    summary: str | None
    postprocessed_at: datetime | None
    postprocess_version: str | None
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class MeetingListOut(BaseModel):
    items: list[MeetingOut]
    total: int


class MeetingDetailOut(MeetingOut):
    organizer: UserOut


class MeetingShareOut(BaseModel):
    meeting_id: int
    share_token: str
    share_path: str
    created_now: bool
    shared_at: datetime


class SharedMeetingOut(BaseModel):
    meeting: MeetingDetailOut
    transcripts: list[MeetingTranscriptOut]
    tasks: list[TaskOut]
    my_role: str = Field(..., description="当前用户在该会议中的角色（guest/organizer/participant）")


class MeetingPostprocessOut(BaseModel):
    """会议后处理响应。"""

    meeting_id: int
    summary: str
    tasks: list[TaskOut]




class MeetingStructuredSummaryOut(BaseModel):
    meeting_id: int
    structured_summary: StructuredSummary
    has_structured_data: bool = Field(..., description='是否有有效的结构化数据')


class MeetingExportRequest(BaseModel):
    """会议导出请求。"""

    format: str = Field(default="txt", pattern="^txt$")


class MeetingExportOut(BaseModel):
    """会议导出响应。"""

    meeting_id: int
    format: str
    filename: str
    content: str
