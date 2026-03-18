import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash


@pytest.mark.usefixtures("client")
def test_login_and_me_flow(client: TestClient) -> None:
    user_resp = client.post(
        "/api/v1/users",
        json={
            "username": "login_user",
            "email": "login_user@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Login User",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "login_user", "password": "plain-password"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert token_data["access_token"]
    assert token_data["token_type"] == "bearer"

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "login_user"


@pytest.mark.usefixtures("client")
def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "missing", "password": "bad"},
    )

    assert resp.status_code == 401
