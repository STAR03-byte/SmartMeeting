from __future__ import annotations

from collections.abc import Generator
from importlib import import_module

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
from app.services.meeting_service import delete_meeting


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


def test_delete_meeting_removes_related_rows(db: Session) -> None:
    meeting = Meeting(title="Delete Me", organizer_id=1)
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

    delete_meeting(db, meeting)

    assert db.query(Meeting).filter(Meeting.id == meeting.id).first() is None
    assert db.query(MeetingAudio).filter(MeetingAudio.meeting_id == meeting.id).count() == 0
    assert db.query(MeetingParticipant).filter(MeetingParticipant.meeting_id == meeting.id).count() == 0
    assert db.query(MeetingTranscript).filter(MeetingTranscript.meeting_id == meeting.id).count() == 0
    assert db.query(Task).filter(Task.meeting_id == meeting.id).count() == 0
