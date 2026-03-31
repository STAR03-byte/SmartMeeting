"""会议转写服务层。"""

from sqlalchemy.orm import Session

from app.models.meeting_transcript import MeetingTranscript
from app.schemas.meeting_transcript import MeetingTranscriptCreate, MeetingTranscriptUpdate


def create_transcript(db: Session, payload: MeetingTranscriptCreate) -> MeetingTranscript:
    """创建转写片段。"""

    transcript = MeetingTranscript(**payload.model_dump())
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def list_transcripts(db: Session, meeting_id: int | None = None) -> list[MeetingTranscript]:
    """查询转写列表，可按会议筛选。"""

    query = db.query(MeetingTranscript)
    if meeting_id is not None:
        query = query.filter(MeetingTranscript.meeting_id == meeting_id)
    return query.order_by(MeetingTranscript.id.desc()).all()


def get_transcript(db: Session, transcript_id: int) -> MeetingTranscript | None:
    """按 ID 查询转写。"""

    return db.query(MeetingTranscript).filter(MeetingTranscript.id == transcript_id).first()


def update_transcript(
    db: Session,
    transcript: MeetingTranscript,
    payload: MeetingTranscriptUpdate,
) -> MeetingTranscript:
    """更新转写。"""

    data: dict[str, object] = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(transcript, key, value)
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def delete_transcript(db: Session, transcript: MeetingTranscript) -> None:
    """删除转写。"""

    db.delete(transcript)
    db.commit()
