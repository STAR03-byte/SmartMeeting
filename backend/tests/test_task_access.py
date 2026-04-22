import time

from fastapi.testclient import TestClient

from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import CurrentUserOut


def _unique_suffix() -> str:
    return str(int(time.time() * 1000000))


def _create_user(auth_client: TestClient, prefix: str) -> dict[str, object]:
    suffix = _unique_suffix()
    resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": f"{prefix}_{suffix}",
            "email": f"{prefix}_{suffix}@example.com",
            "password_hash": "hashed_password",
            "full_name": f"{prefix}_{suffix}",
            "role": "member",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _as_user(client: TestClient, user: dict[str, object]) -> None:
    def _mock_user() -> CurrentUserOut:
        return CurrentUserOut(
            id=int(user["id"]),
            username=str(user["username"]),
            email=str(user["email"]),
            full_name=str(user["full_name"]),
            role="member",
            is_active=True,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )

    client.app.dependency_overrides[get_current_user] = _mock_user  # type: ignore[attr-defined]


def test_non_visible_user_cannot_list_other_users_tasks(auth_client: TestClient) -> None:
    owner = _create_user(auth_client, "task_owner")
    owner_id = int(owner["id"])

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "owner meeting",
            "description": "owner-only",
            "organizer_id": owner_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = int(meeting_resp.json()["id"])

    task_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "owner secret task",
            "description": "should be hidden",
            "assignee_id": owner_id,
            "reporter_id": owner_id,
            "priority": "medium",
            "status": "todo",
        },
    )
    assert task_resp.status_code == 201

    outsider = _create_user(auth_client, "task_outsider")
    _as_user(auth_client, outsider)

    list_resp = auth_client.get("/api/v1/tasks")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_assignee_can_list_assigned_task_even_if_not_organizer(auth_client: TestClient) -> None:
    owner = _create_user(auth_client, "task_owner_assign")
    assignee = _create_user(auth_client, "task_assignee")

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "shared task meeting",
            "description": "for assignee visibility",
            "organizer_id": int(owner["id"]),
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = int(meeting_resp.json()["id"])

    task_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "assigned task",
            "description": "assigned visibility",
            "assignee_id": int(assignee["id"]),
            "reporter_id": int(owner["id"]),
            "priority": "high",
            "status": "todo",
        },
    )
    assert task_resp.status_code == 201
    task_id = int(task_resp.json()["id"])

    _as_user(auth_client, assignee)

    list_resp = auth_client.get("/api/v1/tasks")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert int(data["items"][0]["id"]) == task_id
    assert data["items"][0]["can_manage"] is True


def test_reporter_without_assignment_cannot_list_task(auth_client: TestClient) -> None:
    owner = _create_user(auth_client, "task_owner_reporter")
    assignee = _create_user(auth_client, "task_assignee_reporter")
    reporter = _create_user(auth_client, "task_reporter_only")

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "reporter hidden meeting",
            "description": "reporter should not see task",
            "organizer_id": int(owner["id"]),
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = int(meeting_resp.json()["id"])

    task_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "reporter hidden task",
            "description": "reporter hidden task",
            "assignee_id": int(assignee["id"]),
            "reporter_id": int(reporter["id"]),
            "priority": "medium",
            "status": "todo",
        },
    )
    assert task_resp.status_code == 201

    _as_user(auth_client, reporter)
    list_resp = auth_client.get("/api/v1/tasks")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0
    assert list_resp.json()["items"] == []


def test_assignee_can_update_assigned_task(auth_client: TestClient) -> None:
    owner = _create_user(auth_client, "task_owner_update")
    assignee = _create_user(auth_client, "task_assignee_update")

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "assignee update meeting",
            "description": "assignee can manage own task",
            "organizer_id": int(owner["id"]),
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = int(meeting_resp.json()["id"])

    task_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "assigned update task",
            "description": "before update",
            "assignee_id": int(assignee["id"]),
            "reporter_id": int(owner["id"]),
            "priority": "medium",
            "status": "todo",
        },
    )
    assert task_resp.status_code == 201
    task_id = int(task_resp.json()["id"])

    _as_user(auth_client, assignee)
    patch_resp = auth_client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "in_progress", "description": "after update"},
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["status"] == "in_progress"
    assert body["description"] == "after update"
    assert body["can_manage"] is True


def test_organizer_created_task_response_marks_can_manage_true(auth_client: TestClient) -> None:
    owner = _create_user(auth_client, "task_owner_create_resp")

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "create response meeting",
            "description": "organizer create response",
            "organizer_id": int(owner["id"]),
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = int(meeting_resp.json()["id"])

    task_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "create response task",
            "description": "create response task",
            "reporter_id": int(owner["id"]),
            "priority": "medium",
            "status": "todo",
        },
    )
    assert task_resp.status_code == 201
    assert task_resp.json()["can_manage"] is True
