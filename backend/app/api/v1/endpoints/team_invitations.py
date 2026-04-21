from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.team_invitation import TeamInvitationCreate, TeamInvitationOut, TeamInviteLinkCreate, TeamInviteLinkOut
from app.models.team_invitation import TeamInvitation
from app.services.team_invitation_service import (
    accept_invite_link,
    accept_invitation,
    create_invite_link,
    create_invitation,
    get_user_invitations,
    reject_invitation,
)
from .auth import get_current_user

router = APIRouter(tags=["team_invitations"], dependencies=[Depends(get_current_user)])


def _build_team_invitation_out(item: TeamInvitation) -> TeamInvitationOut:
    return TeamInvitationOut.model_validate(
        {
            **item.__dict__,
            "team_name": getattr(getattr(item, "team", None), "name", None),
            "inviter_name": getattr(getattr(item, "inviter", None), "full_name", None),
        }
    )


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
    return _build_team_invitation_out(create_invitation(db, team_id, current_user.id, payload))


@router.post(
    "/teams/{team_id}/invite-link",
    response_model=TeamInviteLinkOut,
    status_code=status.HTTP_201_CREATED,
)
def create_team_invite_link_api(
    team_id: int,
    payload: TeamInviteLinkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamInviteLinkOut:
    invite_link = create_invite_link(db, team_id, current_user.id, payload.expires_in_hours)
    return TeamInviteLinkOut(
        team_id=invite_link.team_id,
        invite_token=invite_link.invite_token,
        invite_path=f"/invite/{invite_link.invite_token}",
        expires_at=invite_link.expires_at,
    )


@router.get("/invitations", response_model=list[TeamInvitationOut])
def list_my_invitations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> list[TeamInvitationOut]:
    return [_build_team_invitation_out(item) for item in get_user_invitations(db, current_user.id)]


@router.post("/invitations/{invitation_id}/accept", response_model=TeamInvitationOut)
def accept_team_invitation(
    invitation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamInvitationOut:
    return _build_team_invitation_out(accept_invitation(db, invitation_id, current_user.id))


@router.post("/invitations/{invitation_id}/reject", response_model=TeamInvitationOut)
def reject_team_invitation(
    invitation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamInvitationOut:
    return _build_team_invitation_out(reject_invitation(db, invitation_id, current_user.id))


@router.post("/invitations/accept-by-token/{invite_token}", response_model=TeamInvitationOut)
def accept_team_invitation_by_token(
    invite_token: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamInvitationOut:
    return _build_team_invitation_out(accept_invite_link(db, invite_token, current_user.id))
