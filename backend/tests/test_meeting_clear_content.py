from __future__ import annotations

from collections.abc import Generator
from importlib import import_module
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.meeting import Meeting
from app.models.meeting_audio import MeetingAudio
from app.models.meeting_participant import MeetingParticipant
from app.models.meeting_transcript import MeetingTranscript
from app.models.task import Task
from app.services.business.meeting_service import clear_meeting_content


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    import_module("app.models")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


def test_clear_meeting_content_keeps_meeting_and_participants(db: Session) -> None:
    meeting = Meeting(
        title="Keep Meeting",
        organizer_id=1,
        status="done",
        summary="已有纪要",
        postprocessed_at=datetime(2026, 1, 1, 0, 0, 0),
        postprocess_version="llm-v1",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    db.add_all(
        [
            MeetingAudio(
                meeting_id=meeting.id,
                filename="a.wav",
                storage_path="backend/storage/audio/a.wav",
                content_type="audio/wav",
                size_bytes=123,
            ),
            MeetingParticipant(
                meeting_id=meeting.id,
                user_id=1,
                participant_role="required",
                attendance_status="invited",
            ),
            MeetingTranscript(
                meeting_id=meeting.id,
                speaker_user_id=None,
                speaker_name="A",
                segment_index=1,
                content="hello",
            ),
            Task(
                meeting_id=meeting.id,
                transcript_id=None,
                title="todo",
                description=None,
                assignee_id=None,
                reporter_id=None,
                priority="medium",
                status="todo",
            ),
        ]
    )
    db.commit()

    updated = clear_meeting_content(db, meeting)

    assert db.query(Meeting).filter(Meeting.id == meeting.id).first() is not None
    assert db.query(MeetingAudio).filter(MeetingAudio.meeting_id == meeting.id).count() == 0
    assert db.query(MeetingTranscript).filter(MeetingTranscript.meeting_id == meeting.id).count() == 0
    assert db.query(Task).filter(Task.meeting_id == meeting.id).count() == 0
    assert db.query(MeetingParticipant).filter(MeetingParticipant.meeting_id == meeting.id).count() == 1
    assert updated.status == "planned"
    assert updated.summary is None
    assert updated.postprocessed_at is None
    assert updated.postprocess_version is None


def test_clear_meeting_content_removes_audio_file_from_storage(db: Session, tmp_path: Path) -> None:
    meeting = Meeting(title="Clear File", organizer_id=1)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    audio_path = tmp_path / "meeting-audio.wav"
    audio_path.write_bytes(b"fake-audio-content")

    db.add(
        MeetingAudio(
            meeting_id=meeting.id,
            filename="meeting-audio.wav",
            storage_path=str(audio_path),
            content_type="audio/wav",
            size_bytes=18,
        )
    )
    db.commit()

    _ = clear_meeting_content(db, meeting)

    assert not audio_path.exists()


def test_clear_meeting_content_selective_only_summary(db: Session) -> None:
    meeting = Meeting(
        title="Selective",
        organizer_id=1,
        status="done",
        summary="已有纪要",
        postprocessed_at=datetime(2026, 1, 1, 0, 0, 0),
        postprocess_version="llm-v1",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    db.add_all(
        [
            MeetingParticipant(
                meeting_id=meeting.id,
                user_id=1,
                participant_role="required",
                attendance_status="invited",
            ),
            MeetingTranscript(
                meeting_id=meeting.id,
                speaker_user_id=None,
                speaker_name="A",
                segment_index=1,
                content="hello",
            ),
            Task(
                meeting_id=meeting.id,
                transcript_id=None,
                title="todo",
                description=None,
                assignee_id=None,
                reporter_id=None,
                priority="medium",
                status="todo",
            ),
        ]
    )
    db.commit()

    updated = clear_meeting_content(
        db,
        meeting,
        clear_transcripts=False,
        clear_tasks=False,
        clear_summary=True,
        clear_audios=False,
        reset_status=False,
    )

    assert db.query(MeetingTranscript).filter(MeetingTranscript.meeting_id == meeting.id).count() == 1
    assert db.query(Task).filter(Task.meeting_id == meeting.id).count() == 1
    assert updated.summary is None
    assert updated.postprocessed_at is None
    assert updated.postprocess_version is None
    assert updated.status == "done"
