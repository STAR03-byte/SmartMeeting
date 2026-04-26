"""测试会议团队功能。"""

import pytest
from fastapi.testclient import TestClient


def test_create_personal_meeting_without_team_id(auth_client: TestClient) -> None:
    """测试创建个人会议（不提供 team_id）。"""
    # 创建组织者
    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_personal",
            "email": "organizer_personal@example.com",
            "password_hash": "hashed_password",
            "full_name": "Organizer Personal",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    # 创建会议（不提供 team_id）
    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "个人会议",
            "description": "这是一个个人会议",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_data = meeting_resp.json()
    assert meeting_data["title"] == "个人会议"
    assert meeting_data["organizer_id"] == organizer_id
    assert meeting_data.get("team_id") is None

    # 验证组织者自动成为参与者
    participants_resp = auth_client.get(f"/api/v1/participants?meeting_id={meeting_data['id']}")
    assert participants_resp.status_code == 200
    participants = participants_resp.json()
    assert len(participants) == 1
    assert participants[0]["user_id"] == organizer_id
    assert participants[0]["role"] == "organizer"


def test_create_team_meeting_with_valid_team_member(auth_client: TestClient) -> None:
    """测试团队成员创建团队会议。"""
    # 创建团队所有者
    owner_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "team_owner",
            "email": "team_owner@example.com",
            "password_hash": "hashed_password",
            "full_name": "Team Owner",
            "role": "member",
        },
    )
    assert owner_resp.status_code == 201
    owner_id = owner_resp.json()["id"]

    # 创建团队
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

    # 创建团队成员（作为组织者）
    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "team_organizer",
            "email": "team_organizer@example.com",
            "password_hash": "hashed_password",
            "full_name": "Team Organizer",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    # 添加组织者到团队
    member_resp = auth_client.post(
        f"/api/v1/teams/{team_id}/members",
        json={
            "user_id": organizer_id,
            "role": "member",
        },
    )
    assert member_resp.status_code == 201

    # 创建团队会议
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
    meeting_data = meeting_resp.json()
    assert meeting_data["title"] == "团队会议"
    assert meeting_data["organizer_id"] == organizer_id
    assert meeting_data["team_id"] == team_id

    # 验证组织者自动成为参与者
    participants_resp = auth_client.get(f"/api/v1/participants?meeting_id={meeting_data['id']}")
    assert participants_resp.status_code == 200
    participants = participants_resp.json()
    assert len(participants) == 1
    assert participants[0]["user_id"] == organizer_id
    assert participants[0]["role"] == "organizer"

    list_resp = auth_client.get(f"/api/v1/meetings?team_id={team_id}")
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["total"] == 1
    assert list_body["items"][0]["id"] == meeting_data["id"]
    assert list_body["items"][0]["team_id"] == team_id


def test_create_team_meeting_rejects_non_team_member(auth_client: TestClient) -> None:
    """测试非团队成员无法创建团队会议。"""
    # 创建团队所有者
    owner_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "team_owner_reject",
            "email": "team_owner_reject@example.com",
            "password_hash": "hashed_password",
            "full_name": "Team Owner Reject",
            "role": "member",
        },
    )
    assert owner_resp.status_code == 201
    owner_id = owner_resp.json()["id"]

    # 创建团队
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

    # 创建非团队成员（作为组织者）
    non_member_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "non_member",
            "email": "non_member@example.com",
            "password_hash": "hashed_password",
            "full_name": "Non Member",
            "role": "member",
        },
    )
    assert non_member_resp.status_code == 201
    non_member_id = non_member_resp.json()["id"]

    # 尝试创建团队会议（应该失败）
    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "团队会议2",
            "description": "这是一个团队会议",
            "organizer_id": non_member_id,
            "team_id": team_id,
        },
    )
    assert meeting_resp.status_code == 403
    assert meeting_resp.json()["detail"] == "无权在此团队创建会议"
