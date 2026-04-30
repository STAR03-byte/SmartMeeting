"""用户服务层。"""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, payload: UserCreate) -> User:
    """创建用户。"""

    data = payload.model_dump()
    raw_password = data["password_hash"]
    if not raw_password.startswith("$pbkdf2-sha256$"):
        data["password_hash"] = get_password_hash(raw_password)

    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    """查询用户列表。"""

    return db.query(User).order_by(User.id.desc()).all()


def list_selectable_users(
    db: Session,
    current_user_id: int,
    is_admin: bool,
    team_id: int | None = None,
    meeting_id: int | None = None,
) -> list[User]:
    if is_admin:
        return list_users(db)

    if meeting_id is not None:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting is None:
            return []

        participant = (
            db.query(MeetingParticipant)
            .filter(MeetingParticipant.meeting_id == meeting_id, MeetingParticipant.user_id == current_user_id)
            .first()
        )

        team_member = None
        if meeting.team_id is not None:
            team_member = (
                db.query(TeamMember)
                .filter(TeamMember.team_id == meeting.team_id, TeamMember.user_id == current_user_id)
                .first()
            )

        has_access = meeting.organizer_id == current_user_id or participant is not None or team_member is not None
        if not has_access:
            return []

        if meeting.team_id is not None:
            team_user_ids = db.query(TeamMember.user_id).filter(TeamMember.team_id == meeting.team_id)
            users = db.query(User).filter(User.id.in_(team_user_ids)).order_by(User.id.desc()).all()
            if not any(u.id == meeting.organizer_id for u in users):
                organizer = get_user(db, meeting.organizer_id)
                if organizer is not None:
                    users.append(organizer)
            return users

        participant_user_ids = db.query(MeetingParticipant.user_id).filter(MeetingParticipant.meeting_id == meeting_id)
        users = db.query(User).filter(User.id.in_(participant_user_ids)).order_by(User.id.desc()).all()
        if not any(u.id == meeting.organizer_id for u in users):
            organizer = get_user(db, meeting.organizer_id)
            if organizer is not None:
                users.append(organizer)
        return users

    if team_id is None:
        user = get_user(db, current_user_id)
        return [user] if user else []

    membership = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user_id)
        .first()
    )
    if not membership:
        return []

    team_user_ids = db.query(TeamMember.user_id).filter(TeamMember.team_id == team_id)
    return db.query(User).filter(User.id.in_(team_user_ids)).order_by(User.id.desc()).all()


def search_invitable_users(
    db: Session,
    team_id: int,
    current_user_id: int,
    keyword: str,
    is_admin: bool,
    limit: int = 20,
) -> list[User]:
    from app.services.business.team_permission_service import check_team_permission

    normalized = keyword.strip()
    if len(normalized) < 2:
        return []

    if not is_admin and not check_team_permission(db, team_id, current_user_id, "admin"):
        return []

    existing_member_ids = db.query(TeamMember.user_id).filter(TeamMember.team_id == team_id)
    return (
        db.query(User)
        .filter(User.id.not_in(existing_member_ids))
        .filter(
            (User.username.ilike(f"%{normalized}%"))
            | (User.full_name.ilike(f"%{normalized}%"))
            | (User.email.ilike(f"%{normalized}%"))
        )
        .order_by(User.id.desc())
        .limit(limit)
        .all()
    )


def get_user(db: Session, user_id: int) -> User | None:
    """按 ID 查询用户。"""

    return db.query(User).filter(User.id == user_id).first()


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    """更新用户。"""

    data: dict[str, object] = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """删除用户。"""

    db.delete(user)
    db.commit()
