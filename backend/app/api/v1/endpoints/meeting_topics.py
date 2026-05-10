"""会议主题相关 API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.meeting_topic import MeetingTopic
from app.schemas.meeting_topic import MeetingTopicCreate, MeetingTopicListOut, MeetingTopicOut
from app.models.meeting_participant import MeetingParticipant

router = APIRouter(prefix="/meeting-topics", tags=["meeting-topics"])


def _check_access(meeting: Meeting, user_id: int, db: Session) -> bool:
    """检查用户是否有权访问会议。"""
    if meeting.organizer_id == user_id:
        return True
    participant = (
        db.query(MeetingParticipant)
        .filter(MeetingParticipant.meeting_id == meeting.id, MeetingParticipant.user_id == user_id)
        .first()
    )
    return participant is not None


@router.post("", response_model=MeetingTopicOut, status_code=201)
def create_meeting_topic(
    payload: MeetingTopicCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> MeetingTopic:
    """创建会议主题。"""
    meeting = db.query(Meeting).filter(Meeting.id == payload.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    if not _check_access(meeting, current_user["id"], db):
        raise HTTPException(status_code=403, detail="无权访问此会议")

    topic = MeetingTopic(
        meeting_id=payload.meeting_id,
        topic=payload.topic,
        relevance_score=payload.relevance_score,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.get("", response_model=MeetingTopicListOut)
def list_meeting_topics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    meeting_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """获取会议主题列表。"""
    query = db.query(MeetingTopic)

    if meeting_id:
        query = query.filter(MeetingTopic.meeting_id == meeting_id)

    total = query.count()
    items = query.order_by(MeetingTopic.relevance_score.desc()).offset(offset).limit(limit).all()

    return {"items": items, "total": total}


@router.get("/{topic_id}", response_model=MeetingTopicOut)
def get_meeting_topic(
    topic_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> MeetingTopic:
    """获取单个会议主题。"""
    topic = db.query(MeetingTopic).filter(MeetingTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="主题不存在")
    return topic


@router.delete("/{topic_id}", status_code=204)
def delete_meeting_topic(
    topic_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """删除会议主题。"""
    topic = db.query(MeetingTopic).filter(MeetingTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="主题不存在")
    db.delete(topic)
    db.commit()
