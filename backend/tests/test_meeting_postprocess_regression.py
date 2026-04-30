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
from app.services.ai.llm_service import LLMServiceError
from app.services.meeting_service import (
    build_meeting_summary,
    build_meeting_summary_with_llm,
    generate_tasks_from_transcripts,
    generate_tasks_from_transcripts_with_llm,
    normalize_summary_text,
)
from app.services import meeting_service

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


def seed_meeting(db: Session) -> tuple[User, User, User, Meeting]:
    organizer = User(
        username="owner",
        email="owner@example.com",
        password_hash="hashed_password_123",
        full_name="Owner",
        role="member",
    )
    zhangsan = User(
        username="zhangsan",
        email="zhangsan@example.com",
        password_hash="hashed_password_123",
        full_name="张三",
        role="member",
    )
    lisi = User(
        username="lisi",
        email="lisi@example.com",
        password_hash="hashed_password_123",
        full_name="李四",
        role="member",
    )
    db.add_all([organizer, zhangsan, lisi])
    db.commit()

    meeting = Meeting(title="周会", organizer_id=organizer.id)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return organizer, zhangsan, lisi, meeting


def test_build_meeting_summary_skips_blank_lines() -> None:
    transcripts = [MeetingTranscript(content=""), MeetingTranscript(content="  第一行  "), MeetingTranscript(content="第二行")]

    assert build_meeting_summary(transcripts) == "第一行\n第二行"


def test_build_meeting_summary_handles_empty_input() -> None:
    assert build_meeting_summary([]) == ""


def test_build_meeting_summary_with_llm_falls_back_to_rules() -> None:
    meeting = Meeting(title="周会", organizer_id=1)
    transcripts = [MeetingTranscript(content="第一段内容"), MeetingTranscript(content="第二段内容")]

    async def run() -> tuple[str, str]:
        with patch(
            "app.services.meeting_service.llm_generate_meeting_summary",
            new_callable=AsyncMock,
            side_effect=LLMServiceError("boom"),
        ):
            return await build_meeting_summary_with_llm(meeting, transcripts)

    summary, version = asyncio.run(run())

    assert summary == "第一段内容\n第二段内容"
    assert version == "rule-v1"


def test_build_meeting_summary_with_llm_empty_input_returns_empty_version() -> None:
    async def run() -> tuple[str, str]:
        return await build_meeting_summary_with_llm(Meeting(title="周会", organizer_id=1), [])

    summary, version = asyncio.run(run())

    assert summary == ""
    assert version == "empty-v1"


def test_build_meeting_summary_with_llm_returns_llm_summary_on_success() -> None:
    meeting = Meeting(title="周会", organizer_id=1)
    transcripts = [MeetingTranscript(content="第一段内容"), MeetingTranscript(content="第二段内容")]

    async def run() -> tuple[str, str]:
        with patch(
            "app.services.meeting_service.llm_generate_meeting_summary",
            new_callable=AsyncMock,
            return_value="LLM 生成的摘要",
        ):
            return await build_meeting_summary_with_llm(meeting, transcripts)

    summary, version = asyncio.run(run())

    assert summary == "LLM 生成的摘要"
    assert version == "llm-summary-v1"


def test_normalize_summary_text_strips_markdown_noise() -> None:
    raw = "# 会议纪要\n\n**会议主题**：产品评审\n- *第一项*\n***\n"
    normalized = normalize_summary_text(raw)

    assert normalized == "会议纪要\n\n会议主题：产品评审\n• 第一项"


def test_generate_tasks_from_transcripts_extracts_multiple_actions() -> None:
    db = make_session()
    try:
        organizer, zhangsan, lisi, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=organizer.id,
            speaker_name="Owner",
            segment_index=1,
            content="请张三提交接口文档，今天完成；请李四负责整理测试报告，今天完成。",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        tasks = generate_tasks_from_transcripts(db, meeting.id, [transcript])

        assert len(tasks) == 2
        assert tasks[0].title == "请张三提交接口文档，今天完成"
        assert tasks[0].assignee_id == zhangsan.id
        assert tasks[0].priority == "high"
        assert tasks[1].title == "请李四负责整理测试报告，今天完成"
        assert tasks[1].assignee_id == lisi.id
        assert tasks[1].priority == "high"
    finally:
        db.close()


def test_generate_tasks_from_transcripts_returns_empty_for_blank_content() -> None:
    db = make_session()
    try:
        _, _, _, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=None,
            speaker_name=None,
            segment_index=1,
            content="   ",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        assert generate_tasks_from_transcripts(db, meeting.id, [transcript]) == []
    finally:
        db.close()


def test_generate_tasks_from_transcripts_returns_empty_for_no_action_keywords() -> None:
    db = make_session()
    try:
        _, _, _, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=None,
            speaker_name=None,
            segment_index=1,
            content="今天我们同步了进度和风险，没有明确任务。",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        assert generate_tasks_from_transcripts(db, meeting.id, [transcript]) == []
    finally:
        db.close()


def test_generate_tasks_from_transcripts_reuses_existing_tasks() -> None:
    db = make_session()
    try:
        organizer, _, _, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=organizer.id,
            speaker_name="Owner",
            segment_index=1,
            content="请张三完成接口联调。",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        first_tasks = generate_tasks_from_transcripts(db, meeting.id, [transcript])
        second_tasks = generate_tasks_from_transcripts(db, meeting.id, [transcript])

        assert len(first_tasks) == 1
        assert len(second_tasks) == 1
        assert first_tasks[0].id == second_tasks[0].id
    finally:
        db.close()


def test_generate_tasks_from_transcripts_with_llm_falls_back_to_rules() -> None:
    db = make_session()
    try:
        organizer, zhangsan, _, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=organizer.id,
            speaker_name="Owner",
            segment_index=1,
            content="请张三完成接口联调。",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        async def run() -> tuple[list[Task], str]:
            with patch(
                "app.services.meeting_service.llm_extract_action_items",
                new_callable=AsyncMock,
                side_effect=LLMServiceError("boom"),
            ):
                return await generate_tasks_from_transcripts_with_llm(db, meeting.id, [transcript])

        tasks, version = asyncio.run(run())

        assert len(tasks) == 1
        assert tasks[0].title == "请张三完成接口联调"
        assert tasks[0].assignee_id == zhangsan.id
        assert version == "rule-v1"
    finally:
        db.close()


def test_generate_tasks_from_transcripts_with_llm_uses_llm_result() -> None:
    db = make_session()
    try:
        organizer, zhangsan, _, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=organizer.id,
            speaker_name="Owner",
            segment_index=1,
            content="请张三完成接口联调。",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        async def run() -> tuple[list[Task], str]:
            with patch(
                "app.services.meeting_service.llm_extract_action_items",
                new_callable=AsyncMock,
                return_value=[
                    {
                        "title": "完成接口联调",
                        "description": "请张三完成接口联调。",
                        "assignee_name": "张三",
                        "priority": "high",
                        "due_hint": None,
                    }
                ],
            ):
                return await generate_tasks_from_transcripts_with_llm(db, meeting.id, [transcript])

        tasks, version = asyncio.run(run())

        assert len(tasks) == 1
        assert tasks[0].title == "完成接口联调"
        assert tasks[0].description == "请张三完成接口联调。"
        assert tasks[0].assignee_id == zhangsan.id
        assert tasks[0].priority == "high"
        assert version == "llm-task-v1"
    finally:
        db.close()


def test_generate_tasks_from_transcripts_with_llm_filters_colloquial_titles() -> None:
    db = make_session()
    try:
        organizer, _, _, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=organizer.id,
            speaker_name="Owner",
            segment_index=1,
            content="那会变成这个事明天完成也可以，后天完成也可以。",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        async def run() -> tuple[list[Task], str]:
            with patch(
                "app.services.meeting_service.llm_extract_action_items",
                new_callable=AsyncMock,
                return_value=[
                    {
                        "title": "后天完成也可以",
                        "description": "那会变成这个事明天完成也可以，后天完成也可以。",
                        "assignee_name": None,
                        "priority": "medium",
                        "due_hint": "后天",
                    }
                ],
            ):
                return await generate_tasks_from_transcripts_with_llm(db, meeting.id, [transcript])

        tasks, version = asyncio.run(run())

        assert tasks == []
        assert version == "llm-task-v1"
    finally:
        db.close()


def test_generate_tasks_from_transcripts_with_llm_falls_back_when_llm_returns_empty() -> None:
    db = make_session()
    try:
        organizer, zhangsan, _, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=organizer.id,
            speaker_name="Owner",
            segment_index=1,
            content="请张三完成接口联调。",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        async def run() -> tuple[list[Task], str]:
            with patch(
                "app.services.meeting_service.llm_extract_action_items",
                new_callable=AsyncMock,
                return_value=[],
            ):
                return await generate_tasks_from_transcripts_with_llm(db, meeting.id, [transcript])

        tasks, version = asyncio.run(run())

        assert len(tasks) == 1
        assert tasks[0].title == "请张三完成接口联调"
        assert tasks[0].assignee_id == zhangsan.id
        assert version == "rule-v1"
    finally:
        db.close()


def test_generate_tasks_from_transcripts_with_llm_reuses_existing_tasks() -> None:
    db = make_session()
    try:
        organizer, _, _, meeting = seed_meeting(db)
        transcript = MeetingTranscript(
            meeting_id=meeting.id,
            speaker_user_id=organizer.id,
            speaker_name="Owner",
            segment_index=1,
            content="请张三完成接口联调。",
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        async def seed() -> tuple[list[Task], str]:
            with patch(
                "app.services.meeting_service.llm_extract_action_items",
                new_callable=AsyncMock,
                return_value=[
                    {
                        "title": "完成接口联调",
                        "description": "请张三完成接口联调。",
                        "assignee_name": "张三",
                        "priority": "high",
                        "due_hint": None,
                    }
                ],
            ):
                return await generate_tasks_from_transcripts_with_llm(db, meeting.id, [transcript])

        seeded_tasks, seeded_version = asyncio.run(seed())

        async def rerun() -> tuple[list[Task], str]:
            return await generate_tasks_from_transcripts_with_llm(db, meeting.id, [transcript])

        reused_tasks, reused_version = asyncio.run(rerun())

        assert len(seeded_tasks) == 1
        assert seeded_version == "llm-task-v1"
        assert len(reused_tasks) == 1
        assert reused_tasks[0].id == seeded_tasks[0].id
        assert reused_version == "existing-v1"
    finally:
        db.close()


def test_generate_tasks_from_transcripts_with_llm_uses_batched_extraction() -> None:
    db = make_session()
    try:
        organizer, zhangsan, lisi, meeting = seed_meeting(db)
        transcripts = [
            MeetingTranscript(
                meeting_id=meeting.id,
                speaker_user_id=organizer.id,
                speaker_name="Owner",
                segment_index=1,
                content="请张三完成接口联调。",
            ),
            MeetingTranscript(
                meeting_id=meeting.id,
                speaker_user_id=organizer.id,
                speaker_name="Owner",
                segment_index=2,
                content="请李四提交测试报告。",
            ),
        ]
        db.add_all(transcripts)
        db.commit()
        for transcript in transcripts:
            db.refresh(transcript)

        async def run() -> tuple[list[Task], str]:
            with patch(
                "app.services.meeting_service.llm_extract_action_items_for_batch",
                new_callable=AsyncMock,
                return_value=[
                    {
                        "segment_index": 0,
                        "title": "完成接口联调",
                        "description": "请张三完成接口联调。",
                        "assignee_name": "张三",
                        "priority": "high",
                        "due_hint": None,
                    },
                    {
                        "segment_index": 1,
                        "title": "提交测试报告",
                        "description": "请李四提交测试报告。",
                        "assignee_name": "李四",
                        "priority": "medium",
                        "due_hint": None,
                    },
                ],
            ) as batched_mock, patch(
                "app.services.meeting_service.llm_extract_action_items",
                new_callable=AsyncMock,
                return_value=[],
            ) as single_mock:
                tasks, version = await generate_tasks_from_transcripts_with_llm(db, meeting.id, transcripts)
                assert batched_mock.await_count == 1
                assert single_mock.await_count == 0
                return tasks, version

        tasks, version = asyncio.run(run())

        assert len(tasks) == 2
        assert tasks[0].transcript_id == transcripts[0].id
        assert tasks[0].title == "完成接口联调"
        assert tasks[0].assignee_id == zhangsan.id
        assert tasks[1].transcript_id == transcripts[1].id
        assert tasks[1].title == "提交测试报告"
        assert tasks[1].assignee_id == lisi.id
        assert version == "llm-task-v1"
    finally:
        db.close()


def test_resolve_assignee_id_by_name_matches_fullname_username_and_email_prefix() -> None:
    db = make_session()
    try:
        db.add_all(
            [
                User(
                    username="wanglei",
                    email="wang.lei@example.com",
                    password_hash="hashed_password_123",
                    full_name="王磊",
                    role="member",
                ),
                User(
                    username="li_na",
                    email="li.na@example.com",
                    password_hash="hashed_password_123",
                    full_name="Li Na",
                    role="member",
                ),
            ]
        )
        db.commit()

        wang = db.query(User).filter(User.username == "wanglei").first()
        lina = db.query(User).filter(User.username == "li_na").first()
        assert wang is not None
        assert lina is not None

        assert meeting_service.resolve_assignee_id_by_name(db, "王磊") == wang.id
        assert meeting_service.resolve_assignee_id_by_name(db, "wang lei") == wang.id
        assert meeting_service.resolve_assignee_id_by_name(db, "wang.lei") == wang.id
        assert meeting_service.resolve_assignee_id_by_name(db, "LiNa") == lina.id
        assert meeting_service.resolve_assignee_id_by_name(db, "li.na") == lina.id
    finally:
        db.close()


def test_resolve_assignee_id_from_text_matches_embedded_aliases() -> None:
    db = make_session()
    try:
        db.add_all(
            [
                User(
                    username="wanglei",
                    email="wang.lei@example.com",
                    password_hash="hashed_password_123",
                    full_name="王磊",
                    role="member",
                ),
                User(
                    username="lina",
                    email="li.na@example.com",
                    password_hash="hashed_password_123",
                    full_name="Li Na",
                    role="member",
                ),
            ]
        )
        db.commit()

        wang = db.query(User).filter(User.username == "wanglei").first()
        lina = db.query(User).filter(User.username == "lina").first()
        assert wang is not None
        assert lina is not None

        assert meeting_service.resolve_assignee_id_from_text(db, "Wang Lei needs to deliver v1") == wang.id
        assert meeting_service.resolve_assignee_id_from_text(db, "please ask wang.lei to send doc") == wang.id
        assert meeting_service.resolve_assignee_id_from_text(db, "li.na should add test cases") == lina.id
    finally:
        db.close()
