"""决策相关 API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.decision import Decision
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.schemas.decision import DecisionCreate, DecisionListOut, DecisionOut, DecisionUpdate

router = APIRouter(prefix="/decisions", tags=["decisions"])


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


@router.post("", response_model=DecisionOut, status_code=201)
def create_decision(
    payload: DecisionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Decision:
    """创建决策。"""
    meeting = db.query(Meeting).filter(Meeting.id == payload.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    if not _check_access(meeting, current_user["id"], db):
        raise HTTPException(status_code=403, detail="无权访问此会议")

    decision = Decision(
        meeting_id=payload.meeting_id,
        content=payload.content,
        proposer_name=payload.proposer_name,
        proposer_user_id=payload.proposer_user_id or current_user["id"],
        context=payload.context,
        confidence=payload.confidence,
        status="confirmed",
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@router.get("", response_model=DecisionListOut)
def list_decisions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    meeting_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """获取决策列表。"""
    query = db.query(Decision)

    if meeting_id:
        query = query.filter(Decision.meeting_id == meeting_id)
    if status:
        query = query.filter(Decision.status == status)

    total = query.count()
    items = query.order_by(Decision.created_at.desc()).offset(offset).limit(limit).all()

    return {"items": items, "total": total}


@router.get("/{decision_id}", response_model=DecisionOut)
def get_decision(
    decision_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Decision:
    """获取单个决策。"""
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="决策不存在")
    return decision


@router.patch("/{decision_id}", response_model=DecisionOut)
def update_decision(
    decision_id: int,
    payload: DecisionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Decision:
    """更新决策（包括确认/拒绝）。"""
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="决策不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(decision, field, value)

    if payload.status == "confirmed" and not decision.confirmed_at:
        from datetime import datetime
        decision.confirmed_at = datetime.now()

    db.commit()
    db.refresh(decision)
    return decision


@router.delete("/{decision_id}", status_code=204)
def delete_decision(
    decision_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """删除决策。"""
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="决策不存在")
    db.delete(decision)
    db.commit()
