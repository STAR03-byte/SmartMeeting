"""搜索 API 端点测试。"""

import pytest


class TestSearchAPI:
    """搜索 API 测试。"""

    def test_search_empty_query(self, auth_client):
        resp = auth_client.get("/api/v1/search", params={"q": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_search_returns_ok(self, auth_client):
        """搜索不应报错（SQLite 环境下向量搜索不可用但 API 应正常返回）。"""
        resp = auth_client.get("/api/v1/search", params={"q": "数据库"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_search_with_source_type_filter(self, auth_client):
        resp = auth_client.get(
            "/api/v1/search",
            params={"q": "测试", "source_type": "decision"},
        )
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_search_requires_auth(self, client):
        resp = client.get("/api/v1/search", params={"q": "测试"})
        assert resp.status_code in (401, 403)
