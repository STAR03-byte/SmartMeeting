"""流式转写 API 端点 — 接收桌面端实时转写数据。"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.meeting_transcript import MeetingTranscript
from app.schemas.auth import CurrentUserOut
from .auth import get_current_user

router = APIRouter(
    prefix="/meetings/{meeting_id}/transcripts",
    tags=["streaming-transcript"],
    dependencies=[Depends(get_current_user)],
)


class StreamingTranscriptPayload(BaseModel):
    """流式转写数据。"""

    text: str = Field(..., min_length=1, description="转写文本")
    speaker: str | None = Field(default=None, max_length=100, description="说话人名称")
    start_time: float | None = Field(default=None, description="开始时间（秒）")
    end_time: float | None = Field(default=None, description="结束时间（秒）")
    segment_index: int | None = Field(default=None, description="段落索引")
    language_code: str = Field(default="zh-CN", max_length=10, description="语言代码")
    source: str = Field(default="desktop", max_length=20, description="来源：desktop|whisper")


class StreamingTranscriptResponse(BaseModel):
    """流式转写响应。"""

    id: int
    meeting_id: int
    speaker_name: str | None
    content: str
    segment_index: int
    start_time_sec: float | None
    end_time_sec: float | None
    created_at: datetime


def _check_meeting_access(meeting: Meeting, user_id: int, db: Session) -> bool:
    """检查用户是否有权访问会议。"""
    if meeting.organizer_id == user_id:
        return True
    participant = (
        db.query(MeetingParticipant)
        .filter(
            MeetingParticipant.meeting_id == meeting.id,
            MeetingParticipant.user_id == user_id,
        )
        .first()
    )
    return participant is not None


def _get_next_segment_index(meeting_id: int, db: Session) -> int:
    """获取下一个段落索引。"""
    max_index = (
        db.query(MeetingTranscript.segment_index)
        .filter(MeetingTranscript.meeting_id == meeting_id)
        .order_by(MeetingTranscript.segment_index.desc())
        .first()
    )
    return (max_index[0] + 1) if max_index else 1


@router.post("", response_model=StreamingTranscriptResponse, status_code=201)
def create_streaming_transcript(
    meeting_id: int,
    payload: StreamingTranscriptPayload,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> StreamingTranscriptResponse:
    """接收桌面端实时转写数据。

    桌面端在录音过程中，每 30 秒或检测到说话停顿时，
    将转写文本通过此接口同步到服务器。
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    if not _check_meeting_access(meeting, current_user.id, db):
        raise HTTPException(status_code=403, detail="无权访问此会议")

    # 确定段落索引
    segment_index = payload.segment_index
    if segment_index is None:
        segment_index = _get_next_segment_index(meeting_id, db)

    # 创建转写记录
    transcript = MeetingTranscript(
        meeting_id=meeting_id,
        speaker_name=payload.speaker,
        segment_index=segment_index,
        start_time_sec=payload.start_time,
        end_time_sec=payload.end_time,
        language_code=payload.language_code,
        source=payload.source,
        content=payload.text,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    return StreamingTranscriptResponse(
        id=transcript.id,
        meeting_id=transcript.meeting_id,
        speaker_name=transcript.speaker_name,
        content=transcript.content,
        segment_index=transcript.segment_index,
        start_time_sec=transcript.start_time_sec,
        end_time_sec=transcript.end_time_sec,
        created_at=transcript.created_at,
    )


@router.get("", response_model=list[StreamingTranscriptResponse])
def list_streaming_transcripts(
    meeting_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
    since_segment: int = 0,
) -> list[StreamingTranscriptResponse]:
    """获取会议的转写列表（用于桌面端同步后获取最新数据）。

    Args:
        meeting_id: 会议 ID
        since_segment: 只返回此索引之后的段落（用于增量同步）
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    if not _check_meeting_access(meeting, current_user.id, db):
        raise HTTPException(status_code=403, detail="无权访问此会议")

    query = (
        db.query(MeetingTranscript)
        .filter(
            MeetingTranscript.meeting_id == meeting_id,
            MeetingTranscript.segment_index > since_segment,
        )
        .order_by(MeetingTranscript.segment_index.asc())
    )

    return [
        StreamingTranscriptResponse(
            id=t.id,
            meeting_id=t.meeting_id,
            speaker_name=t.speaker_name,
            content=t.content,
            segment_index=t.segment_index,
            start_time_sec=t.start_time_sec,
            end_time_sec=t.end_time_sec,
            created_at=t.created_at,
        )
        for t in query.all()
    ]
