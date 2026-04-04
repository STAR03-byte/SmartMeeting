from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.team_invitation import TeamInvitation
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team_invitation import TeamInvitationCreate
from app.services.team_permission_service import require_team_admin


def _get_team(db: Session, team_id: int) -> Team | None:
    return db.query(Team).filter(Team.id == team_id).first()


def _get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def _get_membership(db: Session, team_id: int, user_id: int) -> TeamMember | None:
    return (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )


def _get_invitation(db: Session, invitation_id: int) -> TeamInvitation | None:
    return db.query(TeamInvitation).filter(TeamInvitation.id == invitation_id).first()


def create_invitation(
    db: Session,
    team_id: int,
    inviter_id: int,
    payload: TeamInvitationCreate,
) -> TeamInvitation:
    team = _get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="团队不存在")

    require_team_admin(db, team_id, inviter_id)

    invitee = _get_user(db, payload.invitee_id)
    if invitee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if team.owner_id == payload.invitee_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="团队所有者已在团队中")

    if _get_membership(db, team_id, payload.invitee_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该用户已在团队中")

    existing = (
        db.query(TeamInvitation)
        .filter(
            TeamInvitation.team_id == team_id,
            TeamInvitation.invitee_id == payload.invitee_id,
            TeamInvitation.status == "pending",
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请已存在")

    invitation = TeamInvitation(
        team_id=team_id,
        inviter_id=inviter_id,
        invitee_id=payload.invitee_id,
        status="pending",
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def get_user_invitations(db: Session, user_id: int) -> list[TeamInvitation]:
    return (
        db.query(TeamInvitation)
        .filter(TeamInvitation.invitee_id == user_id, TeamInvitation.status == "pending")
        .order_by(TeamInvitation.created_at.desc())
        .all()
    )


def accept_invitation(db: Session, invitation_id: int, user_id: int) -> TeamInvitation:
    invitation = _get_invitation(db, invitation_id)
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请不存在")

    if invitation.invitee_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能处理自己的邀请")

    if invitation.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请已处理")

    if _get_membership(db, invitation.team_id, user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已在团队中")

    team = _get_team(db, invitation.team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="团队不存在")

    member = TeamMember(team_id=invitation.team_id, user_id=user_id, role="member")
    invitation.status = "accepted"
    db.add(member)
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def reject_invitation(db: Session, invitation_id: int, user_id: int) -> TeamInvitation:
    invitation = _get_invitation(db, invitation_id)
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请不存在")

    if invitation.invitee_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能处理自己的邀请")

    if invitation.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请已处理")

    invitation.status = "rejected"
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation
