"""决策 API 端点测试。"""

import pytest


@pytest.fixture()
def meeting_id(auth_client):
    """创建测试用户和会议并返回会议 ID。"""
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "decision_test_user",
            "email": "decision_test@example.com",
            "password": "hashed_password_123",
            "password_hash": "hashed_password_123",
            "full_name": "决策测试用户",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "决策测试会议",
            "description": "决策测试用",
            "organizer_id": user_id,
            "status": "done",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestDecisionsCRUD:
    """决策 CRUD 测试。"""

    def test_create_decision(self, auth_client, meeting_id):
        resp = auth_client.post(
            "/api/v1/decisions",
            json={
                "meeting_id": meeting_id,
                "content": "使用 PostgreSQL 作为主数据库",
                "proposer_name": "张三",
                "confidence": 0.9,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "使用 PostgreSQL 作为主数据库"
        assert data["status"] == "confirmed"
        assert data["confidence"] == 0.9

    def test_list_decisions(self, auth_client, meeting_id):
        auth_client.post(
            "/api/v1/decisions",
            json={"meeting_id": meeting_id, "content": "决策一"},
        )
        auth_client.post(
            "/api/v1/decisions",
            json={"meeting_id": meeting_id, "content": "决策二"},
        )
        resp = auth_client.get("/api/v1/decisions", params={"meeting_id": meeting_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_decision(self, auth_client, meeting_id):
        create_resp = auth_client.post(
            "/api/v1/decisions",
            json={"meeting_id": meeting_id, "content": "获取单个决策"},
        )
        decision_id = create_resp.json()["id"]
        resp = auth_client.get(f"/api/v1/decisions/{decision_id}")
        assert resp.status_code == 200
        assert resp.json()["content"] == "获取单个决策"

    def test_update_decision(self, auth_client, meeting_id):
        create_resp = auth_client.post(
            "/api/v1/decisions",
            json={"meeting_id": meeting_id, "content": "原始内容"},
        )
        decision_id = create_resp.json()["id"]
        resp = auth_client.patch(
            f"/api/v1/decisions/{decision_id}",
            json={"content": "更新后的内容", "status": "confirmed"},
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "更新后的内容"

    def test_delete_decision(self, auth_client, meeting_id):
        create_resp = auth_client.post(
            "/api/v1/decisions",
            json={"meeting_id": meeting_id, "content": "待删除"},
        )
        decision_id = create_resp.json()["id"]
        resp = auth_client.delete(f"/api/v1/decisions/{decision_id}")
        assert resp.status_code == 204

        resp = auth_client.get(f"/api/v1/decisions/{decision_id}")
        assert resp.status_code == 404

    def test_create_decision_nonexistent_meeting(self, auth_client):
        resp = auth_client.post(
            "/api/v1/decisions",
            json={"meeting_id": 99999, "content": "不存在的会议"},
        )
        assert resp.status_code == 404

    def test_get_nonexistent_decision(self, auth_client):
        resp = auth_client.get("/api/v1/decisions/99999")
        assert resp.status_code == 404


class TestDecisionsFilter:
    """决策筛选测试。"""

    def test_filter_by_status(self, auth_client, meeting_id):
        auth_client.post(
            "/api/v1/decisions",
            json={"meeting_id": meeting_id, "content": "候选决策", "confidence": 0.5},
        )
        resp = auth_client.get("/api/v1/decisions", params={"meeting_id": meeting_id, "status": "confirmed"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_pagination(self, auth_client, meeting_id):
        for i in range(5):
            auth_client.post(
                "/api/v1/decisions",
                json={"meeting_id": meeting_id, "content": f"决策{i}"},
            )
        resp = auth_client.get(
            "/api/v1/decisions",
            params={"meeting_id": meeting_id, "limit": 2, "offset": 0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
