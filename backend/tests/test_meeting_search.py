from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.core.database import Base
from app.models.meeting import Meeting
from app.services.business.meeting_service import list_meetings, match_meeting_keyword


def test_match_meeting_keyword_matches_title_or_description() -> None:
    meeting1 = Meeting(title="项目推进会议", description="讨论接口联调", organizer_id=1)
    meeting2 = Meeting(title="周会", description="讨论预算与排期", organizer_id=1)

    assert match_meeting_keyword(meeting1, "接口") is True
    assert match_meeting_keyword(meeting2, "接口") is False


def test_list_meetings_returns_newest_first() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        db.add_all(
            [
                Meeting(title="旧会议", description="old", organizer_id=1),
                Meeting(title="新会议", description="new", organizer_id=1),
            ]
        )
        db.commit()

        meetings = list_meetings(db)

        assert [meeting.title for meeting in meetings] == ["新会议", "旧会议"]
    finally:
        db.close()


def test_list_meetings_can_sort_by_scheduled_start_time() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        db.add_all(
            [
                Meeting(
                    title="后开始",
                    description="later",
                    organizer_id=1,
                    scheduled_start_at=datetime(2026, 1, 2, 10, 0, 0),
                ),
                Meeting(
                    title="先开始",
                    description="earlier",
                    organizer_id=1,
                    scheduled_start_at=datetime(2026, 1, 1, 10, 0, 0),
                ),
            ]
        )
        db.commit()

        meetings = list_meetings(db, sort_by="scheduled_start_at")

        assert [meeting.title for meeting in meetings] == ["先开始", "后开始"]
    finally:
        db.close()
