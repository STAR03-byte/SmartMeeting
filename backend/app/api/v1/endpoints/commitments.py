"""承诺相关 API 端点。"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.commitment import Commitment
from app.models.meeting import Meeting
from app.schemas.commitment import CommitmentCreate, CommitmentListOut, CommitmentOut, CommitmentUpdate
from app.models.meeting_participant import MeetingParticipant

router = APIRouter(prefix="/commitments", tags=["commitments"])


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


@router.post("", response_model=CommitmentOut, status_code=201)
def create_commitment(
    payload: CommitmentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Commitment:
    """创建承诺。"""
    meeting = db.query(Meeting).filter(Meeting.id == payload.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    if not _check_access(meeting, current_user["id"], db):
        raise HTTPException(status_code=403, detail="无权访问此会议")

    commitment = Commitment(
        meeting_id=payload.meeting_id,
        content=payload.content,
        assignee_name=payload.assignee_name,
        assignee_user_id=payload.assignee_user_id,
        due_hint=payload.due_hint,
        linked_task_id=payload.linked_task_id,
        status="confirmed",
    )
    db.add(commitment)
    db.commit()
    db.refresh(commitment)
    return commitment


@router.get("", response_model=CommitmentListOut)
def list_commitments(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    meeting_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    assignee_user_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """获取承诺列表。"""
    query = db.query(Commitment)

    if meeting_id:
        query = query.filter(Commitment.meeting_id == meeting_id)
    if status:
        query = query.filter(Commitment.status == status)
    if assignee_user_id:
        query = query.filter(Commitment.assignee_user_id == assignee_user_id)

    total = query.count()
    items = query.order_by(Commitment.created_at.desc()).offset(offset).limit(limit).all()

    return {"items": items, "total": total}


@router.get("/{commitment_id}", response_model=CommitmentOut)
def get_commitment(
    commitment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Commitment:
    """获取单个承诺。"""
    commitment = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="承诺不存在")
    return commitment


@router.patch("/{commitment_id}", response_model=CommitmentOut)
def update_commitment(
    commitment_id: int,
    payload: CommitmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Commitment:
    """更新承诺（包括状态流转）。"""
    commitment = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="承诺不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(commitment, field, value)

    if payload.status == "confirmed" and not commitment.confirmed_at:
        commitment.confirmed_at = datetime.now()

    db.commit()
    db.refresh(commitment)
    return commitment


@router.delete("/{commitment_id}", status_code=204)
def delete_commitment(
    commitment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """删除承诺。"""
    commitment = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="承诺不存在")
    db.delete(commitment)
    db.commit()
