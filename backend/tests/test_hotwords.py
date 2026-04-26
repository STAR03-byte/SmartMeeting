from __future__ import annotations

from unittest.mock import MagicMock
from typing import cast

from fastapi.testclient import TestClient
from app.core.security import get_password_hash
from app.services.hotword_service import clear_hotword_cache, get_hotword_terms
from sqlalchemy.orm import Session
from pytest import MonkeyPatch


def _login_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    login_resp = client.post("/api/v1/auth/login", data={"username": username, "password": password})
    assert login_resp.status_code == 200
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}


def test_hotwords_crud_flow(client: TestClient) -> None:
    user_resp = client.post(
        "/api/v1/register",
        json={
            "username": "hotword_user",
            "email": "hotword_user@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Hotword User",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201

    headers = _login_headers(client, "hotword_user", "plain-password")

    create_resp = client.post("/api/v1/hotwords", json={"word": "WhisperX"}, headers=headers)
    assert create_resp.status_code == 201
    assert create_resp.json()["word"] == "WhisperX"

    list_resp = client.get("/api/v1/hotwords", headers=headers)
    assert list_resp.status_code == 200
    list_body = cast(list[dict[str, object]], list_resp.json())
    assert len(list_body) == 1

    hotword_id = int(cast(int, list_body[0]["id"]))
    delete_resp = client.delete(f"/api/v1/hotwords/{hotword_id}", headers=headers)
    assert delete_resp.status_code == 204

    empty_resp = client.get("/api/v1/hotwords", headers=headers)
    assert empty_resp.status_code == 200
    assert empty_resp.json() == []


def test_hotword_terms_cache_hits_once(monkeypatch: MonkeyPatch) -> None:
    clear_hotword_cache()
    calls: list[int] = []

    def fake_list_hotwords(_db: Session, user_id: int):
        calls.append(user_id)
        item = MagicMock()
        item.word = "SmartMeeting"
        return [item]

    from app.services import hotword_service

    monkeypatch.setattr(hotword_service, "list_hotwords", fake_list_hotwords)

    db = cast(Session, object())
    first = get_hotword_terms(db, 7)
    second = get_hotword_terms(db, 7)

    assert first == second
    assert first[0] == "SmartMeeting"
    assert "Whisper" in first
    assert calls == [7]
