from datetime import datetime, timezone
from typing import Any, cast

from fastapi.testclient import TestClient


def test_non_admin_cannot_create_user(auth_client: TestClient) -> None:
    from app.api.v1.endpoints.auth import get_current_user
    from app.schemas.auth import CurrentUserOut

    def member_user() -> CurrentUserOut:
        now = datetime.now(timezone.utc)
        return CurrentUserOut(
            id=2001,
            username="member_user",
            email="member_user@example.com",
            full_name="Member User",
            role="member",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    app = cast(Any, auth_client.app)
    app.dependency_overrides[get_current_user] = member_user

    resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "blocked_create_user",
            "email": "blocked_create_user@example.com",
            "password_hash": "password123",
            "full_name": "Blocked Create User",
            "role": "member",
        },
    )
    assert resp.status_code == 403


def test_non_admin_get_users_returns_only_self(auth_client: TestClient) -> None:
    create_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "scope_member_1",
            "email": "scope_member_1@example.com",
            "password_hash": "password123",
            "full_name": "Scope Member 1",
            "role": "member",
        },
    )
    assert create_resp.status_code == 201
    user = create_resp.json()

    from app.api.v1.endpoints.auth import get_current_user
    from app.schemas.auth import CurrentUserOut

    def current_member() -> CurrentUserOut:
        now = datetime.now(timezone.utc)
        return CurrentUserOut(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            role="member",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    app = cast(Any, auth_client.app)
    app.dependency_overrides[get_current_user] = current_member

    list_resp = auth_client.get("/api/v1/users")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["id"] == user["id"]


def test_non_admin_scope_all_forbidden(auth_client: TestClient) -> None:
    from app.api.v1.endpoints.auth import get_current_user
    from app.schemas.auth import CurrentUserOut

    def member_user() -> CurrentUserOut:
        now = datetime.now(timezone.utc)
        return CurrentUserOut(
            id=3001,
            username="scope_member_2",
            email="scope_member_2@example.com",
            full_name="Scope Member 2",
            role="member",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    app = cast(Any, auth_client.app)
    app.dependency_overrides[get_current_user] = member_user

    resp = auth_client.get("/api/v1/users?scope=all")
    assert resp.status_code == 403


def test_non_admin_get_users_by_meeting_returns_all_meeting_users(auth_client: TestClient) -> None:
    owner_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "meeting_owner",
            "email": "meeting_owner@example.com",
            "password_hash": "password123",
            "full_name": "Meeting Owner",
            "role": "member",
        },
    )
    assert owner_resp.status_code == 201
    owner = owner_resp.json()

    member_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "meeting_member",
            "email": "meeting_member@example.com",
            "password_hash": "password123",
            "full_name": "Meeting Member",
            "role": "member",
        },
    )
    assert member_resp.status_code == 201
    member = member_resp.json()

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "meeting for user scope",
            "description": "scope test",
            "organizer_id": owner["id"],
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    add_participant_resp = auth_client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": member["id"],
            "participant_role": "required",
        },
    )
    assert add_participant_resp.status_code == 201

    from app.api.v1.endpoints.auth import get_current_user
    from app.schemas.auth import CurrentUserOut

    def current_member() -> CurrentUserOut:
        now = datetime.now(timezone.utc)
        return CurrentUserOut(
            id=member["id"],
            username=member["username"],
            email=member["email"],
            full_name=member["full_name"],
            role="member",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    app = cast(Any, auth_client.app)
    app.dependency_overrides[get_current_user] = current_member

    resp = auth_client.get(f"/api/v1/users?scope=selectable&meeting_id={meeting_id}")
    assert resp.status_code == 200
    data = resp.json()
    ids = {item["id"] for item in data}
    assert owner["id"] in ids
    assert member["id"] in ids


def test_team_meeting_organizer_get_users_by_meeting_can_see_team_users(auth_client: TestClient) -> None:
    owner_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "org_owner_a",
            "email": "org_owner_a@example.com",
            "password_hash": "password123",
            "full_name": "Org Owner A",
            "role": "member",
        },
    )
    assert owner_resp.status_code == 201
    owner = owner_resp.json()

    extra_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "org_extra_b",
            "email": "org_extra_b@example.com",
            "password_hash": "password123",
            "full_name": "Org Extra B",
            "role": "member",
        },
    )
    assert extra_resp.status_code == 201
    extra = extra_resp.json()

    team_resp = auth_client.post(
        "/api/v1/teams",
        json={"name": "owner selectable team", "description": "for selectable", "is_public": False},
    )
    assert team_resp.status_code == 201
    team_id = team_resp.json()["id"]

    add_member_resp = auth_client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": extra["id"], "role": "member"},
    )
    assert add_member_resp.status_code == 201

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "organizer broad selectable",
            "description": "scope",
            "organizer_id": owner["id"],
            "team_id": team_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    from app.api.v1.endpoints.auth import get_current_user
    from app.schemas.auth import CurrentUserOut

    def current_owner() -> CurrentUserOut:
        now = datetime.now(timezone.utc)
        return CurrentUserOut(
            id=owner["id"],
            username=owner["username"],
            email=owner["email"],
            full_name=owner["full_name"],
            role="member",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    app = cast(Any, auth_client.app)
    app.dependency_overrides[get_current_user] = current_owner

    resp = auth_client.get(f"/api/v1/users?scope=selectable&meeting_id={meeting_id}")
    assert resp.status_code == 200
    ids = {item["id"] for item in resp.json()}
    assert owner["id"] in ids
    assert extra["id"] in ids
