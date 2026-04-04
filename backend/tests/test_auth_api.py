import pytest
from fastapi.testclient import TestClient
from app.core.database import get_db
from typing import Any, cast

from app.core.security import get_password_hash
from app.models.audit_log import AuditLog


@pytest.mark.usefixtures("client")
def test_login_and_me_flow(client: TestClient) -> None:
    user_resp = client.post(
        "/api/v1/register",
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


@pytest.mark.usefixtures("client")
def test_login_writes_audit_logs_for_success_and_failure(client: TestClient) -> None:
    user_resp = client.post(
        "/api/v1/register",
        json={
            "username": "audit_login_user",
            "email": "audit_login_user@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Audit Login User",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    bad_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "audit_login_user", "password": "wrong-password"},
    )
    assert bad_login_resp.status_code == 401

    ok_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "audit_login_user", "password": "plain-password"},
    )
    assert ok_login_resp.status_code == 200

    app = cast(Any, client.app)
    override_get_db = app.dependency_overrides[get_db]
    db_gen = override_get_db()
    db = next(db_gen)
    try:
        login_success = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "users",
                AuditLog.entity_id == user_id,
                AuditLog.action == "LOGIN_SUCCESS",
            )
            .first()
        )
        assert login_success is not None
        assert login_success.actor_user_id == user_id

        login_failed = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "users",
                AuditLog.action == "LOGIN_FAILED",
            )
            .first()
        )
        assert login_failed is not None
    finally:
        db_gen.close()


@pytest.mark.usefixtures("client")
def test_register_forces_member_role_even_if_admin_requested(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/register",
        json={
            "username": "register_force_member",
            "email": "register_force_member@example.com",
            "password_hash": "plain-password",
            "full_name": "Register Force Member",
            "role": "admin",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "member"
