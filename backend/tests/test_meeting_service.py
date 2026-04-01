from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module
from typing import Protocol, cast

import pytest
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.meeting import Meeting
from app.models.meeting_transcript import MeetingTranscript
from app.models.task import Task
from app.models.user import User
from app.schemas.meeting import MeetingCreate
from app.services.meeting_service import (
    build_shared_meeting_out,
    count_meetings,
    create_meeting,
    create_or_get_meeting_share,
    list_meetings,
)


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


def seed_user(db: Session, username: str = "owner", full_name: str = "Owner") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash="hashed_password_123",
        full_name=full_name,
        role="member",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_meeting_persists_payload() -> None:
    db = make_session()
    try:
        owner = seed_user(db)
        payload = MeetingCreate(
            title="架构评审",
            description="确认发布窗口",
            organizer_id=owner.id,
        )

        meeting = create_meeting(db, payload)

        assert meeting.id is not None
        assert meeting.title == "架构评审"
        assert meeting.description == "确认发布窗口"
        assert meeting.organizer_id == owner.id
    finally:
        db.close()


def test_list_and_count_meetings_with_filters() -> None:
    db = make_session()
    try:
        owner = seed_user(db)
        db.add_all(
            [
                Meeting(title="发布评审", description="发布计划", organizer_id=owner.id, status="planned"),
                Meeting(title="风险复盘", description="风险清单", organizer_id=owner.id, status="done"),
                Meeting(title="例行同步", description="研发同步", organizer_id=owner.id, status="planned"),
            ]
        )
        db.commit()

        meetings = list_meetings(db, status="planned", keyword="发布", limit=10, offset=0)
        total = count_meetings(db, status="planned", keyword="发布")

        assert len(meetings) == 1
        assert meetings[0].title == "发布评审"
        assert total == 1
    finally:
        db.close()


def test_create_or_get_meeting_share_is_idempotent() -> None:
    db = make_session()
    try:
        owner = seed_user(db)
        meeting = Meeting(title="分享会议", organizer_id=owner.id, summary="会议摘要")
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        first, first_created = create_or_get_meeting_share(db, meeting)
        second, second_created = create_or_get_meeting_share(db, meeting)

        assert first_created is True
        assert second_created is False
        assert first.share_token == second.share_token
        assert first.shared_at is not None
    finally:
        db.close()


def test_create_or_get_meeting_share_requires_summary() -> None:
    db = make_session()
    try:
        owner = seed_user(db)
        meeting = Meeting(title="无摘要会议", organizer_id=owner.id, summary=None)
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        with pytest.raises(ValueError, match="Meeting summary is required for sharing"):
            create_or_get_meeting_share(db, meeting)
    finally:
        db.close()


def test_build_shared_meeting_out_returns_read_only_payload() -> None:
    db = make_session()
    try:
        owner = seed_user(db, username="shared-owner", full_name="Shared Owner")
        meeting = Meeting(
            title="共享会议",
            description="共享详情",
            organizer_id=owner.id,
            summary="共享摘要",
            share_token="token-1",
            shared_at=datetime.now(UTC),
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=owner.id,
            speaker_name="Shared Owner",
            segment_index=1,
            content="共享纪要",
        )
        task = Task(
            meeting_id=meeting.id,
            title="共享任务",
            description="共享任务描述",
            assignee_id=owner.id,
            reporter_id=owner.id,
            status="todo",
            priority="medium",
        )
        db.add_all([transcript, task])
        db.commit()

        shared = build_shared_meeting_out(db, meeting)

        assert shared.meeting.id == meeting.id
        assert shared.meeting.organizer.id == owner.id
        assert len(shared.transcripts) == 1
        assert shared.transcripts[0].content == "共享纪要"
        assert len(shared.tasks) == 1
        assert shared.tasks[0].title == "共享任务"
    finally:
        db.close()


def test_build_shared_meeting_out_raises_when_organizer_not_found() -> None:
    db = make_session()
    try:
        # Create meeting with non-existent organizer_id
        meeting = Meeting(
            title="孤立会议",
            description="组织者已被删除",
            organizer_id=9999,
            summary="会议摘要",
            share_token="token-orphan",
            shared_at=datetime.now(UTC),
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        with pytest.raises(ValueError, match="Organizer not found"):
            build_shared_meeting_out(db, meeting)
    finally:
        db.close()
