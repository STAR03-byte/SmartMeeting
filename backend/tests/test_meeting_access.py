"""测试会议详情权限检查。"""

import time

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import CurrentUserOut
from app.core.database import get_db
from app.models.team_member import TeamMember
from app.models.meeting_participant import MeetingParticipant


def get_unique_suffix():
    """生成唯一后缀，避免用户名冲突。"""
    return str(int(time.time() * 1000000))


def _create_unique_user(auth_client: TestClient, prefix: str) -> dict[str, object]:
    suffix = get_unique_suffix()
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


def _override_current_user(client: TestClient, user: dict[str, object]) -> None:
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


def test_admin_can_view_any_meeting(auth_client: TestClient) -> None:
    """测试管理员可以查看任何会议。"""
    organizer = _create_unique_user(auth_client, "organizer_user")
    organizer_id = int(organizer["id"])

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "个人会议",
            "description": "这是一个个人会议",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    detail_resp = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == meeting_id


def test_team_member_can_view_team_meeting(auth_client: TestClient) -> None:
    """测试团队成员可以查看团队会议。"""
    owner = _create_unique_user(auth_client, "team_owner_view")
    owner_id = int(owner["id"])

    team_resp = auth_client.post(
        "/api/v1/teams",
        json={
            "name": "测试团队",
            "description": "这是一个测试团队",
            "owner_id": owner_id,
        },
    )
    assert team_resp.status_code == 201
    team_id = team_resp.json()["id"]

    organizer = _create_unique_user(auth_client, "team_organizer_view")
    organizer_id = int(organizer["id"])

    member_resp = auth_client.post(
        f"/api/v1/teams/{team_id}/members",
        json={
            "user_id": organizer_id,
            "role": "member",
        },
    )
    assert member_resp.status_code == 201

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "团队会议",
            "description": "这是一个团队会议",
            "organizer_id": organizer_id,
            "team_id": team_id,
        },
    )
    assert meeting_resp.status_code == 201, meeting_resp.text
    meeting_id = meeting_resp.json()["id"]

    viewer = _create_unique_user(auth_client, "team_viewer")
    add_viewer_resp = auth_client.post(
        f"/api/v1/teams/{team_id}/members",
        json={
            "user_id": int(viewer["id"]),
            "role": "member",
        },
    )
    assert add_viewer_resp.status_code == 201

    _override_current_user(auth_client, viewer)

    detail_resp = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == meeting_id


def test_non_team_member_cannot_view_team_meeting(auth_client: TestClient) -> None:
    """测试非团队成员不能查看团队会议。"""
    owner = _create_unique_user(auth_client, "team_owner_reject_view")
    owner_id = int(owner["id"])

    team_resp = auth_client.post(
        "/api/v1/teams",
        json={
            "name": "测试团队2",
            "description": "这是另一个测试团队",
            "owner_id": owner_id,
        },
    )
    assert team_resp.status_code == 201
    team_id = team_resp.json()["id"]

    organizer = _create_unique_user(auth_client, "team_organizer_reject_view")
    organizer_id = int(organizer["id"])

    member_resp = auth_client.post(
        f"/api/v1/teams/{team_id}/members",
        json={
            "user_id": organizer_id,
            "role": "member",
        },
    )
    assert member_resp.status_code == 201

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "团队会议2",
            "description": "这是一个团队会议",
            "organizer_id": organizer_id,
            "team_id": team_id,
        },
    )
    assert meeting_resp.status_code == 201, meeting_resp.text
    meeting_id = meeting_resp.json()["id"]

    outsider = _create_unique_user(auth_client, "team_outsider")
    _override_current_user(auth_client, outsider)

    detail_resp = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 403
    assert detail_resp.json()["detail"] == "无权查看此会议"


def test_organizer_can_view_personal_meeting(auth_client: TestClient) -> None:
    """测试组织者可以查看个人会议。"""
    organizer = _create_unique_user(auth_client, "organizer_personal_view")
    organizer_id = int(organizer["id"])

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "个人会议",
            "description": "这是一个个人会议",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201, meeting_resp.text
    meeting_id = meeting_resp.json()["id"]

    detail_resp = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == meeting_id


def test_participant_can_view_personal_meeting(auth_client: TestClient) -> None:
    """测试参与者可以查看个人会议。"""
    organizer = _create_unique_user(auth_client, "organizer_participant_view")
    organizer_id = int(organizer["id"])

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "个人会议",
            "description": "这是一个个人会议",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201, meeting_resp.text
    meeting_id = meeting_resp.json()["id"]

    participant_user = _create_unique_user(auth_client, "participant_view")
    add_participant_resp = auth_client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": int(participant_user["id"]),
            "participant_role": "required",
        },
    )
    assert add_participant_resp.status_code == 201

    _override_current_user(auth_client, participant_user)

    detail_resp = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == meeting_id


def test_non_participant_cannot_view_personal_meeting(auth_client: TestClient) -> None:
    """测试非参与者不能查看个人会议。"""
    organizer = _create_unique_user(auth_client, "organizer_non_participant_view")
    organizer_id = int(organizer["id"])

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "个人会议",
            "description": "这是一个个人会议",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    outsider = _create_unique_user(auth_client, "non_participant_outsider")
    _override_current_user(auth_client, outsider)

    detail_resp = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 403
    assert detail_resp.json()["detail"] == "无权查看此会议"
