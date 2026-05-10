"""承诺 API 端点测试。"""

import pytest


@pytest.fixture()
def meeting_id(auth_client):
    """创建测试用户和会议并返回会议 ID。"""
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "commitment_test_user",
            "email": "commitment_test@example.com",
            "password": "hashed_password_123",
            "password_hash": "hashed_password_123",
            "full_name": "承诺测试用户",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "承诺测试会议",
            "description": "承诺测试用",
            "organizer_id": user_id,
            "status": "done",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestCommitmentsCRUD:
    """承诺 CRUD 测试。"""

    def test_create_commitment(self, auth_client, meeting_id):
        resp = auth_client.post(
            "/api/v1/commitments",
            json={
                "meeting_id": meeting_id,
                "content": "负责前端搜索页面开发",
                "assignee_name": "李四",
                "due_hint": "下周五前",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "负责前端搜索页面开发"
        assert data["assignee_name"] == "李四"
        assert data["status"] == "confirmed"

    def test_list_commitments(self, auth_client, meeting_id):
        auth_client.post(
            "/api/v1/commitments",
            json={"meeting_id": meeting_id, "content": "承诺一"},
        )
        auth_client.post(
            "/api/v1/commitments",
            json={"meeting_id": meeting_id, "content": "承诺二"},
        )
        resp = auth_client.get("/api/v1/commitments", params={"meeting_id": meeting_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    def test_update_commitment_status(self, auth_client, meeting_id):
        create_resp = auth_client.post(
            "/api/v1/commitments",
            json={"meeting_id": meeting_id, "content": "状态流转测试"},
        )
        cid = create_resp.json()["id"]

        resp = auth_client.patch(f"/api/v1/commitments/{cid}", json={"status": "in_progress"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

        resp = auth_client.patch(f"/api/v1/commitments/{cid}", json={"status": "done"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

    def test_delete_commitment(self, auth_client, meeting_id):
        create_resp = auth_client.post(
            "/api/v1/commitments",
            json={"meeting_id": meeting_id, "content": "待删除"},
        )
        cid = create_resp.json()["id"]
        resp = auth_client.delete(f"/api/v1/commitments/{cid}")
        assert resp.status_code == 204

    def test_create_commitment_nonexistent_meeting(self, auth_client):
        resp = auth_client.post(
            "/api/v1/commitments",
            json={"meeting_id": 99999, "content": "不存在的会议"},
        )
        assert resp.status_code == 404


class TestCommitmentsFilter:
    """承诺筛选测试。"""

    def test_filter_by_status(self, auth_client, meeting_id):
        auth_client.post(
            "/api/v1/commitments",
            json={"meeting_id": meeting_id, "content": "已确认承诺"},
        )
        resp = auth_client.get(
            "/api/v1/commitments",
            params={"meeting_id": meeting_id, "status": "confirmed"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
