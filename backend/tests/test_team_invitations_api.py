from typing import Any, cast

from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import CurrentUserOut

from fastapi.testclient import TestClient
from datetime import datetime


def _create_team(auth_client: TestClient, name: str = "Invites Team") -> int:
    resp = auth_client.post(
        "/api/v1/teams",
        json={"name": name, "description": "team"},
    )
    assert resp.status_code == 201
    data = cast(dict[str, Any], resp.json())
    return cast(int, data["id"])


def _create_owner_user(auth_client: TestClient) -> int:
    return _create_user(auth_client, "owner_user", "owner@example.com")


def _create_user(client: TestClient, username: str, email: str) -> int:
    resp = client.post(
        "/api/v1/users",
        json={
            "username": username,
            "email": email,
            "password_hash": "password123",
            "full_name": "Invite User",
            "role": "member",
        },
    )
    assert resp.status_code == 201
    data = cast(dict[str, Any], resp.json())
    return cast(int, data["id"])


def _set_current_user(client: TestClient, user_id: int, username: str) -> None:
    def override() -> CurrentUserOut:
        return CurrentUserOut(
            id=user_id,
            username=username,
            email=f"{username}@example.com",
            full_name="Invite User",
            role="member",
            is_active=True,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )

    app = cast(Any, client.app)
    app.dependency_overrides[get_current_user] = override


def test_send_team_invitation_success(auth_client: TestClient) -> None:
    _create_owner_user(auth_client)
    team_id = _create_team(auth_client)
    invitee_id = _create_user(auth_client, "invitee1", "invitee1@example.com")

    resp = auth_client.post(f"/api/v1/teams/{team_id}/invitations", json={"invitee_id": invitee_id})
    assert resp.status_code == 201
    data = cast(dict[str, Any], resp.json())
    assert data["team_id"] == team_id
    assert data["invitee_id"] == invitee_id
    assert data["status"] == "pending"


def test_pending_invitations_only_for_me(auth_client: TestClient) -> None:
    _create_owner_user(auth_client)
    team_id = _create_team(auth_client)
    invitee_id = _create_user(auth_client, "invitee2", "invitee2@example.com")

    _set_current_user(auth_client, 1, "test_user")

    send_resp = auth_client.post(f"/api/v1/teams/{team_id}/invitations", json={"invitee_id": invitee_id})
    assert send_resp.status_code == 201

    _set_current_user(auth_client, invitee_id, "invitee2")
    list_resp = auth_client.get("/api/v1/invitations")
    assert list_resp.status_code == 200
    items = cast(list[dict[str, Any]], list_resp.json())
    assert len(items) == 1
    assert items[0]["invitee_id"] == invitee_id
    assert items[0]["team_name"] == "Invites Team"
    assert items[0]["inviter_name"] == "Invite User"


def test_accept_and_reject_invitation(auth_client: TestClient) -> None:
    _create_owner_user(auth_client)
    team_id = _create_team(auth_client)
    invitee_id = _create_user(auth_client, "invitee3", "invitee3@example.com")

    _set_current_user(auth_client, 1, "test_user")

    send_resp = auth_client.post(f"/api/v1/teams/{team_id}/invitations", json={"invitee_id": invitee_id})
    invitation_data = cast(dict[str, Any], send_resp.json())
    invitation_id = cast(int, invitation_data["id"])

    _set_current_user(auth_client, invitee_id, "invitee3")
    accept_resp = auth_client.post(f"/api/v1/invitations/{invitation_id}/accept")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"


def test_invitation_permission_checks(auth_client: TestClient) -> None:
    _create_owner_user(auth_client)
    team_id = _create_team(auth_client)
    invitee_id = _create_user(auth_client, "invitee4", "invitee4@example.com")

    _set_current_user(auth_client, 999, "member_user")
    forbidden_resp = auth_client.post(f"/api/v1/teams/{team_id}/invitations", json={"invitee_id": invitee_id})
    assert forbidden_resp.status_code in (403, 404)

    _set_current_user(auth_client, 1, "test_user")

    send_resp = auth_client.post(f"/api/v1/teams/{team_id}/invitations", json={"invitee_id": invitee_id})
    invitation_data = cast(dict[str, Any], send_resp.json())
    invitation_id = cast(int, invitation_data["id"])

    other_resp = auth_client.post(f"/api/v1/invitations/{invitation_id}/accept")
    assert other_resp.status_code == 403

    _set_current_user(auth_client, invitee_id, "invitee4")
    reject_resp = auth_client.post(f"/api/v1/invitations/{invitation_id}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"


def test_generate_invite_link_and_accept_by_token(auth_client: TestClient) -> None:
    _create_owner_user(auth_client)
    team_id = _create_team(auth_client)

    link_resp = auth_client.post(f"/api/v1/teams/{team_id}/invite-link", json={"expires_in_hours": 24})
    assert link_resp.status_code == 201
    token = link_resp.json()["invite_token"]
    assert token

    invitee_id = _create_user(auth_client, "invitee_by_token", "invitee_by_token@example.com")
    _set_current_user(auth_client, invitee_id, "invitee_by_token")

    accept_resp = auth_client.post(f"/api/v1/invitations/accept-by-token/{token}")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"
    assert accept_resp.json()["invitee_id"] == invitee_id


def test_accept_reject_are_idempotent_for_processed_invitation(auth_client: TestClient) -> None:
    _create_owner_user(auth_client)
    team_id = _create_team(auth_client)
    invitee_id = _create_user(auth_client, "invitee_idempotent", "invitee_idempotent@example.com")

    _set_current_user(auth_client, 1, "test_user")
    send_resp = auth_client.post(f"/api/v1/teams/{team_id}/invitations", json={"invitee_id": invitee_id})
    assert send_resp.status_code == 201
    invitation_id = send_resp.json()["id"]

    _set_current_user(auth_client, invitee_id, "invitee_idempotent")
    accept_resp_1 = auth_client.post(f"/api/v1/invitations/{invitation_id}/accept")
    assert accept_resp_1.status_code == 200
    assert accept_resp_1.json()["status"] == "accepted"

    accept_resp_2 = auth_client.post(f"/api/v1/invitations/{invitation_id}/accept")
    assert accept_resp_2.status_code == 200
    assert accept_resp_2.json()["status"] == "accepted"

    reject_resp = auth_client.post(f"/api/v1/invitations/{invitation_id}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "accepted"
