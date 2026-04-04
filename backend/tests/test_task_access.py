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
