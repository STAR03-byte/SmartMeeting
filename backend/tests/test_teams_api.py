from datetime import datetime, timezone
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import CurrentUserOut


def _user(user_id: int, username: str, email: str, role: str) -> CurrentUserOut:
    return CurrentUserOut(
        id=user_id,
        username=username,
        email=email,
        full_name=username,
        role=role,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_create_team_success(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/teams",
        json={"name": "Test Team", "description": "A test team"},
    )
    assert resp.status_code == 201
    data = cast(dict[str, object], resp.json())
    assert data["name"] == "Test Team"
    assert data["description"] == "A test team"
    assert data["is_public"] is False


def test_create_team_without_auth(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/teams",
        json={"name": "Test Team", "description": "A test team"},
    )
    assert resp.status_code == 401


def test_create_team_max_limit(auth_client: TestClient) -> None:
    for i in range(5):
        resp = auth_client.post(
            "/api/v1/teams",
            json={"name": f"Team {i}", "description": f"Team {i} description"},
        )
        assert resp.status_code == 201

    resp = auth_client.post(
        "/api/v1/teams",
        json={"name": "Team 6", "description": "Team 6 description"},
    )
    assert resp.status_code == 400
    assert "已达到团队创建上限" in str(cast(dict[str, object], resp.json())["detail"])


def test_public_teams_discovery_and_join(client: TestClient) -> None:
    app = cast(FastAPI, client.app)

    app.dependency_overrides[get_current_user] = lambda: _user(
        2,
        "public_team_owner",
        "public_team_owner@example.com",
        "member",
    )
    public_resp = client.post(
        "/api/v1/teams",
        json={"name": "Public Team", "description": "公开团队", "is_public": True},
    )
    assert public_resp.status_code == 201
    public_team_id = cast(dict[str, object], public_resp.json())["id"]

    app.dependency_overrides[get_current_user] = lambda: _user(
        1,
        "discover_user",
        "discover@example.com",
        "admin",
    )
    discover_resp = client.get("/api/v1/teams/public")
    assert discover_resp.status_code == 200
    discover_data = cast(list[dict[str, object]], discover_resp.json())
    assert len(discover_data) == 1
    assert discover_data[0]["id"] == public_team_id
    assert discover_data[0]["is_public"] is True

    join_resp = client.post(f"/api/v1/teams/{public_team_id}/join")
    assert join_resp.status_code == 200
    assert join_resp.json()["my_role"] == "member"

    discover_resp = client.get("/api/v1/teams/public")
    assert discover_resp.status_code == 200
    assert cast(list[dict[str, object]], discover_resp.json()) == []

    _ = app.dependency_overrides.pop(get_current_user, None)


def test_join_private_team_rejected(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    app.dependency_overrides[get_current_user] = lambda: _user(
        1,
        "private_user",
        "private@example.com",
        "admin",
    )

    team_resp = client.post(
        "/api/v1/teams",
        json={"name": "Private Team", "description": "私有团队", "is_public": False},
    )
    assert team_resp.status_code == 201
    team_id = cast(dict[str, object], team_resp.json())["id"]

    join_resp = client.post(f"/api/v1/teams/{team_id}/join")
    assert join_resp.status_code == 403
    assert cast(dict[str, object], join_resp.json())["detail"] == "公开团队不存在"

    _ = app.dependency_overrides.pop(get_current_user, None)


def test_delete_team_success(auth_client: TestClient) -> None:
    team_resp = auth_client.post(
        "/api/v1/teams",
        json={"name": "Delete Team", "description": "to be removed", "is_public": False},
    )
    assert team_resp.status_code == 201
    team_id = cast(dict[str, object], team_resp.json())["id"]

    delete_resp = auth_client.delete(f"/api/v1/teams/{team_id}")
    assert delete_resp.status_code == 204

    list_resp = auth_client.get("/api/v1/teams")
    assert list_resp.status_code == 200
    teams = cast(list[dict[str, object]], list_resp.json())
    assert all(t["id"] != team_id for t in teams)


def test_delete_team_forbidden_for_non_owner(client: TestClient) -> None:
    app = cast(FastAPI, client.app)

    app.dependency_overrides[get_current_user] = lambda: _user(
        1,
        "team_owner",
        "team_owner@example.com",
        "member",
    )
    team_resp = client.post(
        "/api/v1/teams",
        json={"name": "Owner Team", "description": "owner only", "is_public": False},
    )
    assert team_resp.status_code == 201
    team_id = cast(dict[str, object], team_resp.json())["id"]

    app.dependency_overrides[get_current_user] = lambda: _user(
        2,
        "other_user",
        "other_user@example.com",
        "member",
    )
    forbidden_resp = client.delete(f"/api/v1/teams/{team_id}")
    assert forbidden_resp.status_code == 403

    _ = app.dependency_overrides.pop(get_current_user, None)
