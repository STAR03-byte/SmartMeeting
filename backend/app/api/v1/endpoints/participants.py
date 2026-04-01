"""会议参与人 REST API。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.meeting_participant import (
    MeetingParticipantCreate,
    MeetingParticipantOut,
    MeetingParticipantUpdate,
)
from app.services.meeting_service import get_meeting
from app.services.meeting_participant_service import (
    create_participant,
    delete_participant,
    get_participant,
    get_participant_out,
    list_participants,
    list_participants_out,
    update_participant,
)
from app.services.user_service import get_user
from .auth import get_current_user

router = APIRouter(prefix="/participants", tags=["participants"], dependencies=[Depends(get_current_user)])


def _assert_participant_management_permission(meeting, current_user: CurrentUserOut) -> None:
    if current_user.role == "admin":
        return
    if meeting.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage participants for this meeting")


@router.post("", response_model=MeetingParticipantOut, status_code=status.HTTP_201_CREATED)
def create_participant_api(
    payload: MeetingParticipantCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> MeetingParticipantOut:
    """创建会议参与人。"""

    meeting = get_meeting(db, payload.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_participant_management_permission(meeting, current_user)

    user = get_user(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return create_participant(db, payload)


@router.get("", response_model=list[MeetingParticipantOut])
def list_participants_api(
    meeting_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> list[MeetingParticipantOut]:
    """查询会议参与人列表。"""

    if meeting_id is not None:
        meeting = get_meeting(db, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        _assert_participant_management_permission(meeting, current_user)

    return list_participants_out(db, meeting_id=meeting_id)


@router.get("/{participant_id}", response_model=MeetingParticipantOut)
def get_participant_api(
    participant_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> MeetingParticipantOut:
    """查询会议参与人详情。"""

    participant = get_participant_out(db, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    meeting = get_meeting(db, participant.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_participant_management_permission(meeting, current_user)
    return participant


@router.patch("/{participant_id}", response_model=MeetingParticipantOut)
def update_participant_api(
    participant_id: int,
    payload: MeetingParticipantUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> MeetingParticipantOut:
    """更新会议参与人。"""

    participant = get_participant(db, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    meeting = get_meeting(db, participant.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_participant_management_permission(meeting, current_user)
    return update_participant(db, participant, payload)


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant_api(
    participant_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> None:
    """删除会议参与人。"""

    participant = get_participant(db, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    meeting = get_meeting(db, participant.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    _assert_participant_management_permission(meeting, current_user)
    delete_participant(db, participant)
