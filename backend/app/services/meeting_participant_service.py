"""会议参与人服务层。"""

from sqlalchemy.orm import Session

from app.models.meeting_participant import MeetingParticipant
from app.schemas.meeting_participant import MeetingParticipantCreate, MeetingParticipantUpdate


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


def get_participant(db: Session, participant_id: int) -> MeetingParticipant | None:
    """按 ID 查询参与人。"""

    return db.query(MeetingParticipant).filter(MeetingParticipant.id == participant_id).first()


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
