from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.team_invitation import TeamInvitationCreate, TeamInvitationOut
from app.services.team_invitation_service import (
    accept_invitation,
    create_invitation,
    get_user_invitations,
    reject_invitation,
)
from .auth import get_current_user

router = APIRouter(tags=["team_invitations"], dependencies=[Depends(get_current_user)])


@router.post(
    "/teams/{team_id}/invitations",
    response_model=TeamInvitationOut,
    status_code=status.HTTP_201_CREATED,
)
def send_invitation(
    team_id: int,
    payload: TeamInvitationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamInvitationOut:
    return TeamInvitationOut.model_validate(create_invitation(db, team_id, current_user.id, payload))


@router.get("/invitations", response_model=list[TeamInvitationOut])
def list_my_invitations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> list[TeamInvitationOut]:
    return [TeamInvitationOut.model_validate(item) for item in get_user_invitations(db, current_user.id)]


@router.post("/invitations/{invitation_id}/accept", response_model=TeamInvitationOut)
def accept_team_invitation(
    invitation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamInvitationOut:
    return TeamInvitationOut.model_validate(accept_invitation(db, invitation_id, current_user.id))


@router.post("/invitations/{invitation_id}/reject", response_model=TeamInvitationOut)
def reject_team_invitation(
    invitation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamInvitationOut:
    return TeamInvitationOut.model_validate(reject_invitation(db, invitation_id, current_user.id))
