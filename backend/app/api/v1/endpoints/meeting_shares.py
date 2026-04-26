from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.meeting import MeetingShareCreateRequest, MeetingShareOut
from app.services.meeting_service import create_or_get_meeting_share, get_meeting, revoke_meeting_share
from .auth import get_current_user

router = APIRouter(prefix="/meetings", tags=["meetings"], dependencies=[Depends(get_current_user)])


@router.post("/{meeting_id}/share", response_model=MeetingShareOut, status_code=status.HTTP_200_OK)
def create_meeting_share_api(
    meeting_id: int,
    payload: MeetingShareCreateRequest | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> MeetingShareOut:
    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only meeting organizer can create share link")
    if not meeting.summary:
        raise HTTPException(status_code=400, detail="No summary available for share")

    share_out, _ = create_or_get_meeting_share(db, meeting, expires_at=payload.expires_at if payload else None)
    return share_out


@router.delete("/{meeting_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def revoke_meeting_share_api(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserOut = Depends(get_current_user),
) -> None:
    meeting = get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only meeting organizer can revoke share link")

    revoke_meeting_share(db, meeting)
