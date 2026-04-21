from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.team import Team
from app.models.team_invite_link import TeamInviteLink
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


def _get_invite_link_by_token(db: Session, invite_token: str) -> TeamInviteLink | None:
    return db.query(TeamInviteLink).filter(TeamInviteLink.invite_token == invite_token).first()


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


def _now_naive_utc() -> datetime:
    return datetime.now().astimezone(UTC).replace(tzinfo=None)


def create_invite_link(db: Session, team_id: int, inviter_id: int, expires_in_hours: int = 72) -> TeamInviteLink:
    team = _get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="团队不存在")

    require_team_admin(db, team_id, inviter_id)

    normalized_hours = max(1, min(expires_in_hours, 24 * 30))
    expires_at = _now_naive_utc() + timedelta(hours=normalized_hours)

    token = token_urlsafe(32)
    invite_link = TeamInviteLink(
        team_id=team_id,
        inviter_id=inviter_id,
        invite_token=token,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(invite_link)
    db.commit()
    db.refresh(invite_link)
    return invite_link


def get_user_invitations(db: Session, user_id: int) -> list[TeamInvitation]:
    return (
        db.query(TeamInvitation)
        .options(joinedload(TeamInvitation.team), joinedload(TeamInvitation.inviter))
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
        return invitation

    if _get_membership(db, invitation.team_id, user_id):
        invitation.status = "accepted"
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    team = _get_team(db, invitation.team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="团队不存在")

    member = TeamMember(team_id=invitation.team_id, user_id=user_id, role="member")
    invitation.status = "accepted"
    db.add(member)
    db.add(invitation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已在团队中或邀请已处理")
    db.refresh(invitation)
    return invitation


def reject_invitation(db: Session, invitation_id: int, user_id: int) -> TeamInvitation:
    invitation = _get_invitation(db, invitation_id)
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请不存在")

    if invitation.invitee_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能处理自己的邀请")

    if invitation.status != "pending":
        return invitation

    invitation.status = "rejected"
    db.add(invitation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请状态更新失败，请刷新后重试")
    db.refresh(invitation)
    return invitation


def accept_invite_link(db: Session, invite_token: str, user_id: int) -> TeamInvitation:
    invite_link = _get_invite_link_by_token(db, invite_token)
    if invite_link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请链接不存在")

    if invite_link.revoked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请链接已失效")

    if invite_link.expires_at < _now_naive_utc():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请链接已过期")

    team = _get_team(db, invite_link.team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="团队不存在")

    if _get_membership(db, invite_link.team_id, user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已在团队中")

    existing = (
        db.query(TeamInvitation)
        .filter(
            TeamInvitation.team_id == invite_link.team_id,
            TeamInvitation.invitee_id == user_id,
            TeamInvitation.status == "pending",
        )
        .first()
    )
    if existing:
        invitation = existing
    else:
        invitation = TeamInvitation(
            team_id=invite_link.team_id,
            inviter_id=invite_link.inviter_id,
            invitee_id=user_id,
            status="pending",
        )
        db.add(invitation)
        db.flush()

    member = TeamMember(team_id=invite_link.team_id, user_id=user_id, role="member")
    invitation.status = "accepted"
    db.add(member)
    db.add(invitation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已在团队中或邀请已处理")
    db.refresh(invitation)
    return invitation
