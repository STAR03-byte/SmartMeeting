import time
from datetime import UTC, datetime
from typing import Any, TypedDict, cast

from fastapi.testclient import TestClient

from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import CurrentUserOut


class UserData(TypedDict):
    id: int
    username: str
    email: str
    full_name: str


class MeetingData(TypedDict):
    id: int


class TeamData(TypedDict):
    id: int


class TaskData(TypedDict):
    assignee_id: int | None


def _unique_suffix() -> str:
    return str(int(time.time() * 1000000))


def _create_user(auth_client: TestClient, prefix: str, role: str = "member") -> UserData:
    suffix = _unique_suffix()
    resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": f"{prefix}_{suffix}",
            "email": f"{prefix}_{suffix}@example.com",
            "password_hash": "hashed_password",
            "full_name": f"{prefix}_{suffix}",
            "role": role,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _set_current_user(auth_client: TestClient, user: UserData, role: str = "member") -> None:
    def _mock_user() -> CurrentUserOut:
        return CurrentUserOut(
            id=int(user["id"]),
            username=str(user["username"]),
            email=str(user["email"]),
            full_name=str(user["full_name"]),
            role=role,
            is_active=True,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    cast(Any, auth_client.app).dependency_overrides[get_current_user] = _mock_user


def _create_meeting(
    auth_client: TestClient,
    organizer: UserData,
    title: str,
    team_id: int | None = None,
) -> MeetingData:
    payload: dict[str, object] = {
        "title": title,
        "description": title,
        "organizer_id": int(organizer["id"]),
    }
    if team_id is not None:
        payload["team_id"] = team_id

    resp = auth_client.post(
        "/api/v1/meetings",
        json=payload,
    )
    assert resp.status_code == 201
    return resp.json()


def _create_team(auth_client: TestClient, owner: UserData, name: str) -> TeamData:
    _set_current_user(auth_client, owner)
    resp = auth_client.post(
        "/api/v1/teams",
        json={"name": name, "description": name, "is_public": False},
    )
    assert resp.status_code == 201
    return resp.json()


def _add_team_member(auth_client: TestClient, team_id: int, user: UserData, role: str = "member") -> dict[str, object]:
    resp = auth_client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": int(user["id"]), "role": role},
    )
    assert resp.status_code == 201
    return resp.json()


def _add_meeting_participant(auth_client: TestClient, meeting_id: int, user: UserData) -> dict[str, object]:
    resp = auth_client.post(
        "/api/v1/participants",
        json={"meeting_id": meeting_id, "user_id": int(user["id"]), "participant_role": "required", "attendance_status": "invited"},
    )
    assert resp.status_code == 201
    return resp.json()


def _create_task(auth_client: TestClient, meeting_id: int, title: str, reporter_id: int, assignee_id: int | None = None) -> TaskData:
    payload: dict[str, int | str | None] = {
        "meeting_id": meeting_id,
        "title": title,
        "description": title,
        "reporter_id": reporter_id,
        "priority": "medium",
        "status": "todo",
    }
    if assignee_id is not None:
        payload["assignee_id"] = assignee_id

    resp = auth_client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 201
    return cast(TaskData, resp.json())


def test_create_task_without_assignee_succeeds(auth_client: TestClient) -> None:
    organizer = _create_user(auth_client, "task_org_1")
    _set_current_user(auth_client, organizer)
    meeting = _create_meeting(auth_client, organizer, "meeting_without_assignee")

    task = _create_task(auth_client, int(meeting["id"]), "task_without_assignee", int(organizer["id"]))

    assert task["assignee_id"] is None


def test_create_task_with_meeting_participant_assignee_succeeds(auth_client: TestClient) -> None:
    organizer = _create_user(auth_client, "task_org_2")
    assignee = _create_user(auth_client, "task_participant")
    _set_current_user(auth_client, organizer)
    meeting = _create_meeting(auth_client, organizer, "meeting_with_participant")
    _add_meeting_participant(auth_client, int(meeting["id"]), assignee)

    task = _create_task(
        auth_client,
        int(meeting["id"]),
        "task_participant_assignee",
        int(organizer["id"]),
        assignee_id=int(assignee["id"]),
    )

    assert task["assignee_id"] == assignee["id"]


def test_create_team_meeting_task_with_team_member_assignee_succeeds(auth_client: TestClient) -> None:
    organizer = _create_user(auth_client, "task_org_3")
    team_member = _create_user(auth_client, "task_team_member")
    team = _create_team(auth_client, organizer, "task_team")
    _set_current_user(auth_client, organizer)
    _add_team_member(auth_client, int(team["id"]), team_member)
    team_meeting = _create_meeting(auth_client, organizer, "team_meeting", team_id=int(team["id"]))

    task = _create_task(
        auth_client,
        int(team_meeting["id"]),
        "task_team_member_assignee",
        int(organizer["id"]),
        assignee_id=int(team_member["id"]),
    )

    assert task["assignee_id"] == team_member["id"]


def test_create_task_with_organizer_assignee_succeeds(auth_client: TestClient) -> None:
    organizer = _create_user(auth_client, "task_org_4")
    _set_current_user(auth_client, organizer)
    meeting = _create_meeting(auth_client, organizer, "meeting_with_organizer_assignee")

    task = _create_task(
        auth_client,
        int(meeting["id"]),
        "task_organizer_assignee",
        int(organizer["id"]),
        assignee_id=int(organizer["id"]),
    )

    assert task["assignee_id"] == organizer["id"]


def test_create_task_with_unauthorized_assignee_returns_400(auth_client: TestClient) -> None:
    organizer = _create_user(auth_client, "task_org_5")
    unauthorized = _create_user(auth_client, "task_unauthorized")
    _set_current_user(auth_client, organizer)
    meeting = _create_meeting(auth_client, organizer, "meeting_with_unauthorized_assignee")

    resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": int(meeting["id"]),
            "title": "task_unauthorized_assignee",
            "description": "task_unauthorized_assignee",
            "assignee_id": int(unauthorized["id"]),
            "reporter_id": int(organizer["id"]),
            "priority": "medium",
            "status": "todo",
        },
    )
    assert resp.status_code == 400


def test_admin_can_create_task_with_any_assignee(auth_client: TestClient) -> None:
    organizer = _create_user(auth_client, "task_org_6")
    assignee = _create_user(auth_client, "task_any_user")
    _set_current_user(auth_client, organizer, role="admin")
    meeting = _create_meeting(auth_client, organizer, "meeting_for_admin_assignee")

    task = _create_task(
        auth_client,
        int(meeting["id"]),
        "task_admin_assignee",
        int(organizer["id"]),
        assignee_id=int(assignee["id"]),
    )

    assert task["assignee_id"] == assignee["id"]
