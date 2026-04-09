from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.task import TaskCreate, TaskOut, TaskUpdate


def test_task_schema_includes_progress_note() -> None:
    create_payload = TaskCreate(meeting_id=1, title="跟进项目进度", progress_note="已完成接口联调")
    update_payload = TaskUpdate(progress_note="继续跟进")

    assert create_payload.progress_note == "已完成接口联调"
    assert update_payload.progress_note == "继续跟进"


def test_task_schema_includes_reminder_at() -> None:
    create_payload = TaskCreate(
        meeting_id=1,
        title="提醒测试",
        due_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC),
        reminder_at=datetime(2026, 1, 2, 10, 0, 0, tzinfo=UTC),
    )
    update_payload = TaskUpdate(reminder_at=datetime(2026, 1, 3, 10, 0, 0, tzinfo=UTC))

    assert create_payload.reminder_at is not None
    assert update_payload.reminder_at is not None


def test_task_out_serializes_progress_note() -> None:
    task_out = TaskOut(
        id=1,
        meeting_id=1,
        transcript_id=None,
        title="跟进项目进度",
        description="",
        assignee_id=None,
        reporter_id=None,
        priority="medium",
        status="todo",
        progress_note="已完成接口联调",
        due_at=None,
        reminder_at=None,
        completed_at=None,
        is_overdue=False,
        is_due_soon=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert task_out.progress_note == "已完成接口联调"
