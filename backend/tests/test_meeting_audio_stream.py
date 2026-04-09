from __future__ import annotations

from pathlib import Path

from app.models.meeting_audio import MeetingAudio


def test_stream_audio_handles_unicode_filename(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "stream_owner",
            "email": "stream_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Stream Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "音频流测试会议",
            "description": "测试中文文件名流式播放",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    upload_resp = auth_client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("录音-中文名.wav", b"RIFF....WAVEfmt", "audio/wav")},
    )
    assert upload_resp.status_code == 201
    audio_id = upload_resp.json()["id"]

    stream_resp = auth_client.get(f"/api/v1/meetings/{meeting_id}/audios/{audio_id}/stream")
    assert stream_resp.status_code == 200

    content_disposition = stream_resp.headers.get("content-disposition")
    assert content_disposition is not None
    assert content_disposition.startswith("inline; filename*=UTF-8''")
    assert "%E5%BD%95%E9%9F%B3-%E4%B8%AD%E6%96%87%E5%90%8D.wav" in content_disposition
