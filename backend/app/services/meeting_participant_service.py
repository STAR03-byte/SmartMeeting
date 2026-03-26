"""会议参与人服务层。"""

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
        participant_role=participant.participant_role,
        attendance_status=participant.attendance_status,
        joined_at=participant.joined_at,
        left_at=participant.left_at,
        created_at=participant.created_at,
        updated_at=participant.updated_at,
    )


def create_participant(db: Session, payload: MeetingParticipantCreate) -> MeetingParticipant:
    """创建会议参与人。"""

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
    query = db.query(MeetingParticipant, User.email).join(User, MeetingParticipant.user_id == User.id)
    if meeting_id is not None:
        query = query.filter(MeetingParticipant.meeting_id == meeting_id)
    rows = query.order_by(MeetingParticipant.id.desc()).all()
    return [_build_participant_out(participant, email) for participant, email in rows]


def get_participant(db: Session, participant_id: int) -> MeetingParticipant | None:
    """按 ID 查询参与人。"""

    return db.query(MeetingParticipant).filter(MeetingParticipant.id == participant_id).first()


def get_participant_out(db: Session, participant_id: int) -> MeetingParticipantOut | None:
    row = db.query(MeetingParticipant, User.email).join(User, MeetingParticipant.user_id == User.id).filter(MeetingParticipant.id == participant_id).first()
    if not row:
        return None
    participant, email = row
    return _build_participant_out(participant, email)


def update_participant(
    db: Session,
    participant: MeetingParticipant,
    payload: MeetingParticipantUpdate,
) -> MeetingParticipant:
    """更新参与人。"""

    data = payload.model_dump(exclude_unset=True)
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
