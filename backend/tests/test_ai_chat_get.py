"""AI 聊天 GET SSE 兼容性测试。"""


def test_ai_chat_get_supports_eventsource_query_token(auth_client) -> None:
    """GET /api/v1/ai/chat 应命中 GET 路由且不再返回 405。"""

    response = auth_client.get(
        "/api/v1/ai/chat",
        params={
            "message": "你好",
            "conversation_id": 99999,
            "access_token": "fake-token",
        },
    )

    # 对话不存在应返回 404；关键是不能再出现 405。
    assert response.status_code == 404
    assert response.status_code != 405
