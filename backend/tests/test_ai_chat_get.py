"""AI 聊天 GET SSE 兼容性测试。"""

from app.models.meeting import Meeting
from app.models.meeting_transcript import MeetingTranscript
from app.models.user import User


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


def _make_db(auth_client):
    override_get_db = auth_client.app.dependency_overrides[next(iter(auth_client.app.dependency_overrides.keys()))]
    db_gen = override_get_db()
    db = next(db_gen)
    return db, db_gen


def test_ai_chat_get_returns_meeting_minutes_directly(auth_client) -> None:
    db, db_gen = _make_db(auth_client)
    try:
        user = User(
            username="chat_minutes_owner",
            email="chat_minutes_owner@example.com",
            password_hash="hashed",
            full_name="Chat Minutes Owner",
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        meeting = Meeting(
            title="GET纪要会议",
            organizer_id=user.id,
            summary="会议纪要：本周五完成接口联调，并由运维跟进环境扩容。",
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        response = auth_client.get(
            "/api/v1/ai/chat",
            params={
                "message": "GET纪要会议的会议纪要是什么",
            },
        )

        assert response.status_code == 200
        assert "会议纪要" in response.text
        assert "接口联调" in response.text
    finally:
        db.close()
        db_gen.close()


def test_ai_chat_get_returns_meeting_resolutions_directly(auth_client) -> None:
    db, db_gen = _make_db(auth_client)
    try:
        user = User(
            username="chat_resolution_owner",
            email="chat_resolution_owner@example.com",
            password_hash="hashed",
            full_name="Chat Resolution Owner",
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        meeting = Meeting(title="GET决议会议", organizer_id=user.id)
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        db.add_all(
            [
                MeetingTranscript(
                    meeting_id=meeting.id,
                    speaker_user_id=user.id,
                    speaker_name="Chat Resolution Owner",
                    segment_index=1,
                    content="今天会议决定本周五完成接口联调。",
                ),
                MeetingTranscript(
                    meeting_id=meeting.id,
                    speaker_user_id=user.id,
                    speaker_name="Chat Resolution Owner",
                    segment_index=2,
                    content="最终决定由运维支持扩容。",
                ),
            ]
        )
        db.commit()

        response = auth_client.get(
            "/api/v1/ai/chat",
            params={
                "message": "GET决议会议有哪些决议",
            },
        )

        assert response.status_code == 200
        assert "决议" in response.text or "决定" in response.text
        assert "接口联调" in response.text
    finally:
        db.close()
        db_gen.close()
