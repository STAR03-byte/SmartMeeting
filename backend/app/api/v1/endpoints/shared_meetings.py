from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting import Meeting
from app.schemas.meeting import SharedMeetingOut
from app.services.meeting_service import build_shared_meeting_out

router = APIRouter(prefix="/shared/meetings", tags=["shared-meetings"])


@router.get("/{share_token}", response_model=SharedMeetingOut)
def get_shared_meeting_api(share_token: str, db: Session = Depends(get_db)) -> SharedMeetingOut:
    meeting = db.query(Meeting).filter(Meeting.share_token == share_token).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Shared meeting not found")

    return build_shared_meeting_out(db, meeting)
