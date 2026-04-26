from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Protocol, cast
from unittest.mock import AsyncMock, patch

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.meeting import Meeting
from app.models.meeting_transcript import MeetingTranscript
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskUpdate
from app.services.meeting_service import generate_tasks_from_transcripts_with_llm
from app.services.task_service import update_task


class _MetadataOwner(Protocol):
    metadata: MetaData


class _DatabaseModule(Protocol):
    Base: type[_MetadataOwner]


DATABASE_MODULE = cast(_DatabaseModule, cast(object, import_module("app.core.database")))
METADATA = DATABASE_MODULE.Base.metadata


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    METADATA.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def seed_meeting(db: Session) -> tuple[User, User, Meeting, MeetingTranscript]:
    organizer = User(
        username="draft_owner",
        email="draft_owner@example.com",
        password_hash="hashed_password_123",
        full_name="Draft Owner",
        role="member",
    )
    assignee = User(
        username="draft_assignee",
        email="draft_assignee@example.com",
        password_hash="hashed_password_123",
        full_name="Draft Assignee",
        role="member",
    )
    db.add_all([organizer, assignee])
    db.commit()

    meeting = Meeting(title="Draft workflow meeting", organizer_id=organizer.id)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    transcript = MeetingTranscript(
        meeting_id=meeting.id,
        speaker_user_id=organizer.id,
        speaker_name="Owner",
        segment_index=1,
        content="Draft Assignee should send the rollout checklist by Friday.",
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return organizer, assignee, meeting, transcript


def test_postprocess_extracted_tasks_start_as_drafts_and_can_be_confirmed() -> None:
    db = make_session()
    try:
        organizer, assignee, meeting, transcript = seed_meeting(db)

        async def run() -> tuple[list[Task], str]:
            with patch(
                "app.services.meeting_service.llm_extract_action_items_for_batch",
                new_callable=AsyncMock,
                return_value=[],
            ), patch(
                "app.services.meeting_service.llm_extract_action_items",
                new_callable=AsyncMock,
                return_value=[
                    {
                        "title": "Send rollout checklist",
                        "description": "Draft Assignee should send the rollout checklist by Friday.",
                        "assignee_name": "Draft Assignee",
                        "priority": "high",
                        "due_hint": "Friday",
                    }
                ],
            ), patch("app.services.meeting_service.is_actionable_task_text", return_value=True):
                return await generate_tasks_from_transcripts_with_llm(
                    db,
                    meeting.id,
                    [transcript],
                    reporter_id=organizer.id,
                )

        tasks, version = asyncio.run(run())

        assert version == "llm-task-v1"
        assert len(tasks) == 1
        assert tasks[0].status == "draft"
        assert tasks[0].reporter_id == organizer.id
        assert tasks[0].assignee_id == assignee.id
        assert tasks[0].transcript_id == transcript.id

        confirmed = update_task(db, tasks[0], TaskUpdate(status="todo"))

        assert confirmed.status == "todo"
        assert confirmed.completed_at is None
    finally:
        db.close()
