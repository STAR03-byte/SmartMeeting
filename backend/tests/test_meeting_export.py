def test_meeting_export_requires_existing_meeting(auth_client) -> None:
    response = auth_client.post("/api/v1/meetings/9999/export", json={"format": "txt"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_meeting_export_requires_summary(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "export_owner",
            "email": "export_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Export Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "待导出会议",
            "description": "无摘要",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    response = auth_client.post(f"/api/v1/meetings/{meeting_id}/export", json={"format": "txt"})

    assert response.status_code == 400
    assert response.json()["detail"] == "No summary available for export"


def test_meeting_export_returns_text_payload(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "export_manager",
            "email": "export_manager@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Export Manager",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "周例会",
            "description": "讨论本周任务",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM",
            "segment_index": 1,
            "content": "今天确认需求范围，张三负责接口联调，周五前完成。",
        },
    )

    postprocess_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert postprocess_resp.status_code == 200

    response = auth_client.post(f"/api/v1/meetings/{meeting_id}/export", json={"format": "txt"})

    assert response.status_code == 200
    body = response.json()
    assert body["meeting_id"] == meeting_id
    assert body["format"] == "txt"
    assert body["filename"].endswith(".txt")
    assert body["content"].startswith("title=")
    assert "summary=" in body["content"]
