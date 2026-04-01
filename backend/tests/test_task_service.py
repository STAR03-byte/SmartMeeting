from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import (
    count_tasks,
    create_task,
    extract_action_items,
    infer_assignee_name,
    infer_task_priority,
    list_tasks,
    update_task,
)


def _db_from_client(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db_gen = override_get_db()
    db = next(db_gen)
    return db, db_gen


def _seed_meeting_context(db):
    organizer = User(
        username="svc_owner",
        email="svc_owner@example.com",
        password_hash="hashed",
        full_name="Svc Owner",
        role="admin",
    )
    assignee = User(
        username="svc_assignee",
        email="svc_assignee@example.com",
        password_hash="hashed",
        full_name="Svc Assignee",
        role="member",
    )
    reporter = User(
        username="svc_reporter",
        email="svc_reporter@example.com",
        password_hash="hashed",
        full_name="Svc Reporter",
        role="member",
    )
    db.add_all([organizer, assignee, reporter])
    db.commit()
    db.refresh(organizer)
    db.refresh(assignee)
    db.refresh(reporter)

    meeting = Meeting(title="Service Test", organizer_id=organizer.id)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting, assignee, reporter


def test_list_tasks_filters_sorts_and_paginates(client) -> None:
    db, db_gen = _db_from_client(client)
    try:
        meeting, assignee, reporter = _seed_meeting_context(db)
        now = datetime.now(UTC)

        t1 = Task(
            meeting_id=meeting.id,
            title="整理周报",
            assignee_id=assignee.id,
            reporter_id=reporter.id,
            priority="medium",
            status="todo",
            due_at=now + timedelta(days=2),
        )
        t2 = Task(
            meeting_id=meeting.id,
            title="发布复盘",
            assignee_id=assignee.id,
            reporter_id=reporter.id,
            priority="high",
            status="in_progress",
            due_at=now + timedelta(days=1),
        )
        t3 = Task(
            meeting_id=meeting.id,
            title="完成验收",
            assignee_id=None,
            reporter_id=reporter.id,
            priority="low",
            status="todo",
            due_at=None,
        )
        db.add_all([t1, t2, t3])
        db.commit()

        filtered = list_tasks(
            db,
            meeting_id=meeting.id,
            assignee_id=assignee.id,
            status="in_progress",
            priority="high",
            keyword="发布",
            sort_by="due_at_asc",
            limit=10,
            offset=0,
        )

        assert len(filtered) == 1
        assert filtered[0].title == "发布复盘"

        paged = list_tasks(
            db,
            meeting_id=meeting.id,
            sort_by="due_at_asc",
            limit=1,
            offset=0,
        )
        assert len(paged) == 1
        assert paged[0].title == "发布复盘"
    finally:
        db_gen.close()


def test_count_tasks_with_filters(client) -> None:
    db, db_gen = _db_from_client(client)
    try:
        meeting, assignee, reporter = _seed_meeting_context(db)
        db.add_all(
            [
                Task(meeting_id=meeting.id, title="任务一", assignee_id=assignee.id, reporter_id=reporter.id),
                Task(meeting_id=meeting.id, title="任务二", assignee_id=assignee.id, reporter_id=reporter.id),
                Task(meeting_id=meeting.id, title="其他", assignee_id=None, reporter_id=reporter.id),
            ]
        )
        db.commit()

        total = count_tasks(db, meeting_id=meeting.id, assignee_id=assignee.id, keyword="任务")
        assert total == 2
    finally:
        db_gen.close()


def test_create_and_update_task_status_transition(client) -> None:
    db, db_gen = _db_from_client(client)
    try:
        meeting, assignee, reporter = _seed_meeting_context(db)
        created = create_task(
            db,
            TaskCreate(
                meeting_id=meeting.id,
                title="推进发布",
                assignee_id=assignee.id,
                reporter_id=reporter.id,
                status="todo",
            ),
        )

        assert created.status == "todo"

        in_progress = update_task(db, created, TaskUpdate(status="in_progress"))
        assert in_progress.status == "in_progress"
        assert in_progress.completed_at is None

        done = update_task(db, in_progress, TaskUpdate(status="done"))
        assert done.status == "done"
        assert done.completed_at is not None

        reopened = update_task(db, done, TaskUpdate(status="todo"))
        assert reopened.status == "todo"
        assert reopened.completed_at is None
    finally:
        db_gen.close()


def test_update_task_rejects_invalid_status_transition(client) -> None:
    db, db_gen = _db_from_client(client)
    try:
        meeting, assignee, reporter = _seed_meeting_context(db)
        task = create_task(
            db,
            TaskCreate(
                meeting_id=meeting.id,
                title="非法流转",
                assignee_id=assignee.id,
                reporter_id=reporter.id,
                status="todo",
            ),
        )

        with pytest.raises(Exception, match="Invalid task status transition"):
            update_task(db, task, TaskUpdate(status="done"))
    finally:
        db_gen.close()


def test_task_rule_helpers_extract_priority_and_assignee() -> None:
    content = "请王伟今天完成发布，并跟进验收。"

    items = extract_action_items(content)
    assert items
    assert infer_task_priority(content) == "high"
    assert infer_assignee_name(content) in {"王伟", "王伟今天"}
