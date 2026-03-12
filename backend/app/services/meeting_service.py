"""会议服务层。"""

from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.schemas.meeting import MeetingCreate, MeetingUpdate


def create_meeting(db: Session, payload: MeetingCreate) -> Meeting:
    """创建会议。"""

    meeting = Meeting(**payload.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def list_meetings(db: Session) -> list[Meeting]:
    """查询会议列表。"""

    return db.query(Meeting).order_by(Meeting.id.desc()).all()


def get_meeting(db: Session, meeting_id: int) -> Meeting | None:
    """按 ID 查询会议。"""

    return db.query(Meeting).filter(Meeting.id == meeting_id).first()


def update_meeting(db: Session, meeting: Meeting, payload: MeetingUpdate) -> Meeting:
    """更新会议。"""

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(meeting, key, value)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def delete_meeting(db: Session, meeting: Meeting) -> None:
    """删除会议。"""

    db.delete(meeting)
    db.commit()
