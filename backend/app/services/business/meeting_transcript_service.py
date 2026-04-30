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
    
    # If updating speaker_name and a speaker_id exists, update all segments with the same speaker_id
    if "speaker_name" in data and transcript.speaker_id is not None:
        db.query(MeetingTranscript).filter(
            MeetingTranscript.meeting_id == transcript.meeting_id,
            MeetingTranscript.speaker_id == transcript.speaker_id
        ).update({"speaker_name": data["speaker_name"]}, synchronize_session=False)
        db.commit()
        db.refresh(transcript)

    for key, value in data.items():
        if key != "speaker_name":
            setattr(transcript, key, value)
    
    if "speaker_name" in data and transcript.speaker_id is None:
        setattr(transcript, "speaker_name", data["speaker_name"])

    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def delete_transcript(db: Session, transcript: MeetingTranscript) -> None:
    """删除转写。"""

    db.delete(transcript)
    db.commit()
