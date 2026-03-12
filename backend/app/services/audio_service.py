"""音频上传与占位识别服务。"""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.meeting_audio import MeetingAudio
from app.models.meeting_transcript import MeetingTranscript


def save_meeting_audio(db: Session, meeting_id: int, upload: UploadFile) -> MeetingAudio:
    """保存会议音频并记录元数据。"""

    suffix = Path(upload.filename or "audio.bin").suffix or ".bin"
    safe_name = f"{uuid4().hex}{suffix}"
    storage_dir = Path("backend/storage/audio") / str(meeting_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / safe_name

    content = upload.file.read()
    storage_path.write_bytes(content)

    audio = MeetingAudio(
        meeting_id=meeting_id,
        filename=upload.filename or safe_name,
        storage_path=str(storage_path),
        content_type=upload.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


def transcribe_latest_audio(db: Session, meeting_id: int) -> MeetingTranscript | None:
    """对最新音频执行占位识别并写入转写。"""

    latest_audio = (
        db.query(MeetingAudio)
        .filter(MeetingAudio.meeting_id == meeting_id)
        .order_by(MeetingAudio.id.desc())
        .first()
    )
    if not latest_audio:
        return None

    latest_segment = (
        db.query(MeetingTranscript)
        .filter(MeetingTranscript.meeting_id == meeting_id)
        .order_by(MeetingTranscript.segment_index.desc())
        .first()
    )
    next_segment = 1 if not latest_segment else latest_segment.segment_index + 1

    transcript = MeetingTranscript(
        meeting_id=meeting_id,
        speaker_user_id=None,
        speaker_name="ASR",
        segment_index=next_segment,
        language_code="zh-CN",
        source="mock-asr",
        content=f"[mock-asr] 已识别音频文件：{latest_audio.filename}",
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript
