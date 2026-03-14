"""会议参与人 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.meeting_participant import (
    MeetingParticipantCreate,
    MeetingParticipantOut,
    MeetingParticipantUpdate,
)
from app.services.meeting_participant_service import (
    create_participant,
    delete_participant,
    get_participant,
    list_participants,
    update_participant,
)
from app.services.meeting_service import get_meeting
from app.services.user_service import get_user

router = APIRouter(prefix="/participants", tags=["participants"])


@router.post("", response_model=MeetingParticipantOut, status_code=status.HTTP_201_CREATED)
def create_participant_api(
    payload: MeetingParticipantCreate,
    db: Session = Depends(get_db),
) -> MeetingParticipantOut:
    """创建会议参与人。"""

    meeting = get_meeting(db, payload.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    user = get_user(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return create_participant(db, payload)


@router.get("", response_model=list[MeetingParticipantOut])
def list_participants_api(
    meeting_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[MeetingParticipantOut]:
    """查询会议参与人列表。"""

    return list_participants(db, meeting_id=meeting_id)


@router.get("/{participant_id}", response_model=MeetingParticipantOut)
def get_participant_api(participant_id: int, db: Session = Depends(get_db)) -> MeetingParticipantOut:
    """查询会议参与人详情。"""

    participant = get_participant(db, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@router.patch("/{participant_id}", response_model=MeetingParticipantOut)
def update_participant_api(
    participant_id: int,
    payload: MeetingParticipantUpdate,
    db: Session = Depends(get_db),
) -> MeetingParticipantOut:
    """更新会议参与人。"""

    participant = get_participant(db, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return update_participant(db, participant, payload)


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant_api(participant_id: int, db: Session = Depends(get_db)) -> None:
    """删除会议参与人。"""

    participant = get_participant(db, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    delete_participant(db, participant)
