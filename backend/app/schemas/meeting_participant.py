"""会议参与人 Schema 定义。"""

from datetime import datetime

from pydantic import BaseModel, Field


class MeetingParticipantCreate(BaseModel):
    """创建参与人请求。"""

    meeting_id: int
    user_id: int
    participant_role: str = Field(default="required")
    attendance_status: str = Field(default="invited")
    joined_at: datetime | None = None
    left_at: datetime | None = None


class MeetingParticipantUpdate(BaseModel):
    """更新参与人请求。"""

    participant_role: str | None = None
    attendance_status: str | None = None
    joined_at: datetime | None = None
    left_at: datetime | None = None


class MeetingParticipantOut(BaseModel):
    """参与人响应。"""

    id: int
    meeting_id: int
    user_id: int
    email: str | None = None
    participant_role: str
    attendance_status: str
    joined_at: datetime | None
    left_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
