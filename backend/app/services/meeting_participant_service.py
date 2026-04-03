"""会议参与人服务层。"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.meeting_participant import MeetingParticipant
from app.models.user import User
from app.schemas.meeting_participant import MeetingParticipantCreate, MeetingParticipantUpdate
from app.schemas.meeting_participant import MeetingParticipantOut


def _build_participant_out(participant: MeetingParticipant, email: str | None) -> MeetingParticipantOut:
    return MeetingParticipantOut(
        id=participant.id,
        meeting_id=participant.meeting_id,
        user_id=participant.user_id,
        email=email,
        role=participant.role,
        participant_role=participant.participant_role,
        attendance_status=participant.attendance_status,
        joined_at=participant.joined_at,
        left_at=participant.left_at,
        created_at=participant.created_at,
        updated_at=participant.updated_at,
    )


def create_participant(db: Session, payload: MeetingParticipantCreate) -> MeetingParticipant:
    """创建会议参与人。"""

    existing = (
        db.query(MeetingParticipant)
        .filter(
            MeetingParticipant.meeting_id == payload.meeting_id,
            MeetingParticipant.user_id == payload.user_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Participant already exists in meeting")

    participant = MeetingParticipant(**payload.model_dump())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def list_participants(db: Session, meeting_id: int | None = None) -> list[MeetingParticipant]:
    """查询参与人列表，可按会议筛选。"""

    query = db.query(MeetingParticipant)
    if meeting_id is not None:
        query = query.filter(MeetingParticipant.meeting_id == meeting_id)
    return query.order_by(MeetingParticipant.id.desc()).all()


def list_participants_out(db: Session, meeting_id: int | None = None) -> list[MeetingParticipantOut]:
    query = db.query(MeetingParticipant)
    if meeting_id is not None:
        query = query.filter(MeetingParticipant.meeting_id == meeting_id)
    participants = query.order_by(MeetingParticipant.id.desc()).all()
    user_ids = [participant.user_id for participant in participants]
    user_email_map: dict[int, str] = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_email_map = {user.id: user.email for user in users}
    return [_build_participant_out(participant, user_email_map.get(participant.user_id)) for participant in participants]




def list_participants_out_paginated(
    db: Session,
    meeting_id: int | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[MeetingParticipantOut]:
    query = db.query(MeetingParticipant)
    if meeting_id is not None:
        query = query.filter(MeetingParticipant.meeting_id == meeting_id)
    query = query.order_by(MeetingParticipant.id.desc()).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    participants = query.all()
    user_ids = [participant.user_id for participant in participants]
    user_email_map: dict[int, str] = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_email_map = {user.id: user.email for user in users}
    return [_build_participant_out(participant, user_email_map.get(participant.user_id)) for participant in participants]


def count_participants(db: Session, meeting_id: int | None = None) -> int:
    query = db.query(MeetingParticipant)
    if meeting_id is not None:
        query = query.filter(MeetingParticipant.meeting_id == meeting_id)
    return query.count()


def get_participant(db: Session, participant_id: int) -> MeetingParticipant | None:
    """按 ID 查询参与人。"""

    return db.query(MeetingParticipant).filter(MeetingParticipant.id == participant_id).first()


def get_participant_out(db: Session, participant_id: int) -> MeetingParticipantOut | None:
    participant = get_participant(db, participant_id)
    if not participant:
        return None
    user = db.query(User).filter(User.id == participant.user_id).first()
    email = user.email if user is not None else None
    return _build_participant_out(participant, email)


def update_participant(
    db: Session,
    participant: MeetingParticipant,
    payload: MeetingParticipantUpdate,
) -> MeetingParticipant:
    """更新参与人。"""

    data: dict[str, object] = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(participant, key, value)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def delete_participant(db: Session, participant: MeetingParticipant) -> None:
    """删除参与人。"""

    db.delete(participant)
    db.commit()


def get_participant_role(db: Session, meeting_id: int, user_id: int) -> str | None:
    """获取用户在会议中的角色。返回 'organizer', 'participant', 或 None。"""
    participant = (
        db.query(MeetingParticipant)
        .filter(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == user_id,
        )
        .first()
    )
    return participant.role if participant else None


def is_organizer(db: Session, meeting_id: int, user_id: int) -> bool:
    """检查用户是否是会议组织者。"""
    role = get_participant_role(db, meeting_id, user_id)
    return role == "organizer"


def is_participant(db: Session, meeting_id: int, user_id: int) -> bool:
    """检查用户是否是会议参与者（包括 organizer）。"""
    role = get_participant_role(db, meeting_id, user_id)
    return role in ["organizer", "participant"]
