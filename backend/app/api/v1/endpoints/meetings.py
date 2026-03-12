"""会议 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.meeting import MeetingCreate, MeetingOut, MeetingUpdate
from app.services.meeting_service import (
    create_meeting,
    delete_meeting,
    get_meeting,
    list_meetings,
    update_meeting,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting_api(payload: MeetingCreate, db: Session = Depends(get_db)) -> MeetingOut:
    """创建会议。"""

    return create_meeting(db, payload)


@router.get("", response_model=list[MeetingOut])
def list_meetings_api(db: Session = Depends(get_db)) -> list[MeetingOut]:
    """查询会议列表。"""

    return list_meetings(db)


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting_api(meeting_id: int, db: Session = Depends(get_db)) -> MeetingOut:
    """查询会议详情。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingOut)
def update_meeting_api(
    meeting_id: int,
    payload: MeetingUpdate,
    db: Session = Depends(get_db),
) -> MeetingOut:
    """更新会议。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return update_meeting(db, meeting, payload)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting_api(meeting_id: int, db: Session = Depends(get_db)) -> None:
    """删除会议。"""

    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    delete_meeting(db, meeting)
