"""团队 REST API。"""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.team import Team
from app.models.team_invitation import TeamInvitation
from app.models.team_invite_link import TeamInviteLink
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.auth import CurrentUserOut
from app.schemas.team import AddTeamMember, TeamCreate, TeamMemberOut, TeamOut, UpdateMemberRole
from .auth import get_current_user

router = APIRouter(prefix="/teams", tags=["teams"], dependencies=[Depends(get_current_user)])

MAX_TEAMS_PER_USER = 5


def _team_out(team: Team, my_role: str) -> TeamOut:
    return TeamOut(
        id=team.id,
        name=team.name,
        description=team.description,
        is_public=team.is_public,
        owner_id=team.owner_id,
        my_role=my_role,
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamOut:
    """创建团队（当前用户自动成为 owner）。"""

    team_count = cast(
        int,
        db.query(func.count())
        .select_from(Team)
        .filter(Team.owner_id == current_user.id)
        .scalar()
    )

    if team_count >= MAX_TEAMS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"已达到团队创建上限（{MAX_TEAMS_PER_USER} 个团队）",
        )

    team = Team(
        name=payload.name,
        description=payload.description,
        is_public=payload.is_public,
        owner_id=current_user.id,
    )
    db.add(team)
    db.flush()

    team_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role="owner",
    )
    _ = db.add(team_member)
    db.commit()
    db.refresh(team)

    return _team_out(team, "owner")


@router.get("", response_model=list[TeamOut])
def list_teams(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> list[TeamOut]:
    """获取当前用户所属的团队列表。"""
    memberships = (
        db.query(TeamMember)
        .filter(TeamMember.user_id == current_user.id)
        .all()
    )

    team_ids = [m.team_id for m in memberships]
    if not team_ids:
        return []

    teams = db.query(Team).filter(Team.id.in_(team_ids)).all()

    role_map = {m.team_id: m.role for m in memberships}

    return [_team_out(team, role_map.get(team.id, "member")) for team in teams]


@router.get("/public", response_model=list[TeamOut])
def list_public_teams_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> list[TeamOut]:
    public_teams = db.query(Team).filter(Team.is_public.is_(True)).all()
    user_team_ids = {
        tm.team_id
        for tm in db.query(TeamMember)
        .filter(TeamMember.user_id == current_user.id)
        .all()
    }

    return [_team_out(team, "guest") for team in public_teams if team.id not in user_team_ids]


@router.get("/{team_id}", response_model=TeamOut)
def get_team(
    team_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamOut:
    """获取团队详情（仅限团队成员）。"""
    membership = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在或您无权访问",
        )

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    return _team_out(team, membership.role)


@router.post("/{team_id}/join", response_model=TeamOut)
def join_public_team_endpoint(
    team_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamOut:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or not team.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="公开团队不存在",
        )

    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经是该团队成员",
        )

    member = TeamMember(team_id=team_id, user_id=current_user.id, role="member")
    db.add(member)
    db.commit()

    return _team_out(team, "member")


def _require_team_role(
    db: Session, team_id: int, user_id: int, allowed_roles: list[str]
) -> TeamMember:
    """检查用户是否具有指定角色，否则抛出 403。"""
    membership = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在或您无权访问",
        )
    if membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )
    return membership


@router.get("/{team_id}/members", response_model=list[TeamMemberOut])
def list_team_members(
    team_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> list[TeamMemberOut]:
    """获取团队成员列表（团队成员均可查看）。"""
    # 验证当前用户是团队成员
    membership = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在或您无权访问",
        )

    members = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id)
        .join(User)
        .all()
    )

    return [
        TeamMemberOut(
            user_id=m.user_id,
            user_name=m.user.username,
            full_name=m.user.full_name,
            email=m.user.email,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in members
    ]


@router.post("/{team_id}/members", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def add_team_member(
    team_id: int,
    payload: AddTeamMember,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamMemberOut:
    """添加团队成员（owner/admin 权限）。"""
    _ = _require_team_role(db, team_id, current_user.id, ["owner", "admin"])

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    member_count = cast(
        int,
        db.query(func.count())
        .select_from(TeamMember)
        .filter(TeamMember.team_id == team_id)
        .scalar()
    )

    if member_count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="团队成员已达上限（20 人）",
        )

    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == payload.user_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户已在团队中",
        )

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    new_member = TeamMember(
        team_id=team_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    _ = db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return TeamMemberOut(
        user_id=new_member.user_id,
        user_name=user.username,
        full_name=user.full_name,
        email=user.email,
        role=new_member.role,
        joined_at=new_member.joined_at,
    )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> None:
    """移除团队成员（owner/admin 权限）。"""
    _ = _require_team_role(db, team_id, current_user.id, ["owner", "admin"])

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    if team.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除团队所有者",
        )

    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    _ = db.delete(member)
    db.commit()


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberOut)
def update_member_role(
    team_id: int,
    user_id: int,
    payload: UpdateMemberRole,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> TeamMemberOut:
    """修改成员角色（仅 owner 权限）。"""
    _ = _require_team_role(db, team_id, current_user.id, ["owner"])

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    if team.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改团队所有者的角色",
        )

    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    member.role = payload.role
    db.commit()
    db.refresh(member)

    return TeamMemberOut(
        user_id=member.user_id,
        user_name=member.user.username,
        full_name=member.user.full_name,
        email=member.user.email,
        role=member.role,
        joined_at=member.joined_at,
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> None:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有团队所有者可以删除团队",
        )

    db.query(Meeting).filter(Meeting.team_id == team_id).update({Meeting.team_id: None}, synchronize_session=False)
    db.query(TeamInvitation).filter(TeamInvitation.team_id == team_id).delete(synchronize_session=False)
    db.query(TeamInviteLink).filter(TeamInviteLink.team_id == team_id).delete(synchronize_session=False)
    db.query(TeamMember).filter(TeamMember.team_id == team_id).delete(synchronize_session=False)
    db.delete(team)
    db.commit()
