from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.team_member import TeamMember
from app.schemas.auth import CurrentUserOut
from app.schemas.meeting import SharedMeetingOut
from app.services.meeting_service import build_shared_meeting_out

router = APIRouter(prefix="/shared/meetings", tags=["shared-meetings"])


def _can_access_meeting(meeting: Meeting, user_id: int, db: Session) -> bool:
    """检查用户是否有权访问会议。

    用户有权访问会议的条件：
    1. 是会议组织者
    2. 是会议参与者
    3. 是团队成员（如果会议属于某个团队）
    """
    if meeting.organizer_id == user_id:
        return True

    participant = (
        db.query(MeetingParticipant)
        .filter(MeetingParticipant.meeting_id == meeting.id, MeetingParticipant.user_id == user_id)
        .first()
    )
    if participant:
        return True

    if meeting.team_id:
        team_member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == meeting.team_id, TeamMember.user_id == user_id)
            .first()
        )
        if team_member:
            return True

    return False


@router.get("/{share_token}", response_model=SharedMeetingOut)
def get_shared_meeting_api(
    share_token: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> SharedMeetingOut:
    """通过分享链接访问会议（需要登录）。

    访客通过分享链接查看会议，但只能查看，不能编辑。
    """
    meeting = db.query(Meeting).filter(Meeting.share_token == share_token).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Shared meeting not found")

    if not _can_access_meeting(meeting, current_user.id, db):
        raise HTTPException(status_code=403, detail="You do not have permission to access this meeting")

    return build_shared_meeting_out(db, meeting, my_role="guest")
