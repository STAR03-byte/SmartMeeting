"""团队 API 测试。"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_create_team_success(auth_client: TestClient) -> None:
    """成功创建团队。"""
    resp = auth_client.post(
        "/api/v1/teams",
        json={
            "name": "Test Team",
            "description": "A test team",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Team"
    assert data["description"] == "A test team"
    assert "id" in data
    assert "owner_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_team_without_auth(client: TestClient) -> None:
    """未认证用户无法创建团队。"""
    resp = client.post(
        "/api/v1/teams",
        json={
            "name": "Test Team",
            "description": "A test team",
        },
    )
    assert resp.status_code == 401


def test_create_team_max_limit(auth_client: TestClient) -> None:
    """用户创建团队数量达到上限。"""
    for i in range(5):
        resp = auth_client.post(
            "/api/v1/teams",
            json={
                "name": f"Team {i}",
                "description": f"Team {i} description",
            },
        )
        assert resp.status_code == 201

    resp = auth_client.post(
        "/api/v1/teams",
        json={
            "name": "Team 6",
            "description": "Team 6 description",
        },
    )
    assert resp.status_code == 400
    assert "已达到团队创建上限" in resp.json()["detail"]