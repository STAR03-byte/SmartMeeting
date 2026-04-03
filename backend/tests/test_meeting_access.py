"""测试会议详情权限检查。"""

import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.team_member import TeamMember
from app.models.meeting_participant import MeetingParticipant


def get_unique_suffix():
    """生成唯一后缀，避免用户名冲突。"""
    return str(int(time.time() * 1000000))


def test_admin_can_view_any_meeting(auth_client: TestClient) -> None:
    """测试管理员可以查看任何会议。"""
    admin_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "admin_user",
            "email": "admin@example.com",
            "password_hash": "hashed_password",
            "full_name": "Admin User",
            "role": "admin",
        },
    )
    assert admin_resp.status_code == 201
    admin_id = admin_resp.json()["id"]

    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_user",
            "email": "organizer@example.com",
            "password_hash": "hashed_password",
            "full_name": "Organizer User",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

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


def test_team_member_can_view_team_meeting(auth_client: TestClient, member_client: TestClient) -> None:
    """测试团队成员可以查看团队会议。"""
    owner_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "team_owner_view",
            "email": "team_owner_view@example.com",
            "password_hash": "hashed_password",
            "full_name": "Team Owner View",
            "role": "member",
        },
    )
    assert owner_resp.status_code == 201
    owner_id = owner_resp.json()["id"]

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

    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "team_organizer_view",
            "email": "team_organizer_view@example.com",
            "password_hash": "hashed_password",
            "full_name": "Team Organizer View",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

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
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        team_member = TeamMember(
            team_id=team_id,
            user_id=999,
            role="member",
        )
        db.add(team_member)
        db.commit()
    finally:
        db.close()

    detail_resp = member_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == meeting_id


def test_non_team_member_cannot_view_team_meeting(auth_client: TestClient, member_client: TestClient) -> None:
    """测试非团队成员不能查看团队会议。"""
    owner_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "team_owner_reject_view",
            "email": "team_owner_reject_view@example.com",
            "password_hash": "hashed_password",
            "full_name": "Team Owner Reject View",
            "role": "member",
        },
    )
    assert owner_resp.status_code == 201
    owner_id = owner_resp.json()["id"]

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

    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "team_organizer_reject_view",
            "email": "team_organizer_reject_view@example.com",
            "password_hash": "hashed_password",
            "full_name": "Team Organizer Reject View",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

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
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    detail_resp = member_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 403
    assert detail_resp.json()["detail"] == "无权查看此会议"


def test_organizer_can_view_personal_meeting(auth_client: TestClient) -> None:
    """测试组织者可以查看个人会议。"""
    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_personal_view",
            "email": "organizer_personal_view@example.com",
            "password_hash": "hashed_password",
            "full_name": "Organizer Personal View",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

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


def test_participant_can_view_personal_meeting(auth_client: TestClient, member_client: TestClient) -> None:
    """测试参与者可以查看个人会议。"""
    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_participant_view",
            "email": "organizer_participant_view@example.com",
            "password_hash": "hashed_password",
            "full_name": "Organizer Participant View",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

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

    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        participant = MeetingParticipant(
            meeting_id=meeting_id,
            user_id=999,
            role="participant",
            participant_role="required",
            attendance_status="invited",
        )
        db.add(participant)
        db.commit()
    finally:
        db.close()

    detail_resp = member_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == meeting_id


def test_non_participant_cannot_view_personal_meeting(auth_client: TestClient, member_client: TestClient) -> None:
    """测试非参与者不能查看个人会议。"""
    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_non_participant_view",
            "email": "organizer_non_participant_view@example.com",
            "password_hash": "hashed_password",
            "full_name": "Organizer Non Participant View",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

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

    detail_resp = member_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 403
    assert detail_resp.json()["detail"] == "无权查看此会议"