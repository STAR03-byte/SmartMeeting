"""后端核心接口测试。"""

from app.core.security import get_password_hash
from app.services.llm_service import LLMServiceError


def test_health_check(auth_client) -> None:
    """健康检查接口可用。"""

    response = auth_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_meeting_id_path_param_returns_422_with_error_code(auth_client) -> None:
    response = auth_client.get("/api/v1/meetings/0")

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "REQUEST_VALIDATION_ERROR"


def test_invalid_task_id_path_param_returns_422_with_error_code(auth_client) -> None:
    response = auth_client.patch("/api/v1/tasks/0", json={"status": "todo"})

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "REQUEST_VALIDATION_ERROR"


def test_user_crud_flow(auth_client) -> None:
    """用户创建和查询流程可用。"""

    create_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Alice",
            "role": "admin",
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    get_resp = auth_client.get(f"/api/v1/users/{user_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["username"] == "alice"

    list_resp = auth_client.get("/api/v1/users")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_create_user_rejects_duplicate_username_or_email(auth_client) -> None:
    first_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "duplicate_user",
            "email": "duplicate_user@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Duplicate User",
            "role": "member",
        },
    )
    assert first_resp.status_code == 201

    duplicate_username_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "duplicate_user",
            "email": "another_email@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Duplicate Username",
            "role": "member",
        },
    )
    assert duplicate_username_resp.status_code == 409
    assert duplicate_username_resp.json()["detail"] == "Username or email already exists"
    assert duplicate_username_resp.json()["error_code"] == "CONFLICT"

    duplicate_email_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "another_user",
            "email": "duplicate_user@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Duplicate Email",
            "role": "member",
        },
    )
    assert duplicate_email_resp.status_code == 409
    assert duplicate_email_resp.json()["detail"] == "Username or email already exists"
    assert duplicate_email_resp.json()["error_code"] == "CONFLICT"


def test_user_management_requires_admin_role(client) -> None:
    member_resp = client.post(
        "/api/v1/users",
        json={
            "username": "user_auth_member",
            "email": "user_auth_member@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "User Auth Member",
            "role": "member",
        },
    )
    assert member_resp.status_code == 201

    admin_resp = client.post(
        "/api/v1/users",
        json={
            "username": "user_auth_admin",
            "email": "user_auth_admin@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "User Auth Admin",
            "role": "admin",
        },
    )
    assert admin_resp.status_code == 201
    admin_id = admin_resp.json()["id"]

    target_resp = client.post(
        "/api/v1/users",
        json={
            "username": "user_auth_target",
            "email": "user_auth_target@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "User Auth Target",
            "role": "member",
        },
    )
    assert target_resp.status_code == 201
    target_id = target_resp.json()["id"]

    def login_headers(username: str) -> dict[str, str]:
        login_resp = client.post("/api/v1/auth/login", data={"username": username, "password": "plain-password"})
        assert login_resp.status_code == 200
        return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    member_headers = login_headers("user_auth_member")
    admin_headers = login_headers("user_auth_admin")

    forbidden_list_resp = client.get("/api/v1/users", headers=member_headers)
    assert forbidden_list_resp.status_code == 403
    assert forbidden_list_resp.json()["detail"] == "Admin role required"

    admin_list_resp = client.get("/api/v1/users", headers=admin_headers)
    assert admin_list_resp.status_code == 200
    assert len(admin_list_resp.json()) >= 3

    forbidden_get_resp = client.get(f"/api/v1/users/{target_id}", headers=member_headers)
    assert forbidden_get_resp.status_code == 403
    assert forbidden_get_resp.json()["detail"] == "Admin role required"

    admin_get_resp = client.get(f"/api/v1/users/{target_id}", headers=admin_headers)
    assert admin_get_resp.status_code == 200
    assert admin_get_resp.json()["id"] == target_id

    forbidden_patch_resp = client.patch(
        f"/api/v1/users/{target_id}",
        json={"full_name": "Blocked"},
        headers=member_headers,
    )
    assert forbidden_patch_resp.status_code == 403
    assert forbidden_patch_resp.json()["detail"] == "Admin role required"

    admin_patch_resp = client.patch(
        f"/api/v1/users/{target_id}",
        json={"full_name": "Updated By Admin"},
        headers=admin_headers,
    )
    assert admin_patch_resp.status_code == 200
    assert admin_patch_resp.json()["full_name"] == "Updated By Admin"

    forbidden_delete_resp = client.delete(f"/api/v1/users/{target_id}", headers=member_headers)
    assert forbidden_delete_resp.status_code == 403
    assert forbidden_delete_resp.json()["detail"] == "Admin role required"

    admin_delete_resp = client.delete(f"/api/v1/users/{target_id}", headers=admin_headers)
    assert admin_delete_resp.status_code == 204

    admin_self_delete_resp = client.delete(f"/api/v1/users/{admin_id}", headers=admin_headers)
    assert admin_self_delete_resp.status_code == 400
    assert admin_self_delete_resp.json()["detail"] == "Admin cannot delete self"


def test_meeting_crud_flow(auth_client) -> None:
    """会议创建和更新流程可用。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer",
            "email": "organizer@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Organizer",
            "role": "member",
        },
    )
    organizer_id = user_resp.json()["id"]

    create_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "产品评审会",
            "description": "评审 MVP 范围",
            "organizer_id": organizer_id,
            "location": "Room A",
        },
    )
    assert create_resp.status_code == 201
    meeting_id = create_resp.json()["id"]

    patch_resp = auth_client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={"status": "ongoing"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "ongoing"

    list_resp = auth_client.get("/api/v1/meetings")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_participants_api_includes_user_email(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "participant1",
            "email": "participant1@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Participant One",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_participants",
            "email": "organizer_participants@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Organizer Participants",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "参与人列表会议",
            "description": "测试参与人邮箱返回",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    create_resp = auth_client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": user_id,
            "participant_role": "required",
            "attendance_status": "invited",
        },
    )
    assert create_resp.status_code == 201

    list_resp = auth_client.get(f"/api/v1/participants?meeting_id={meeting_id}")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert len(body) == 1
    assert body[0]["email"] == "participant1@example.com"


def test_create_participant_rejects_duplicate_in_same_meeting(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "participant_duplicate",
            "email": "participant_duplicate@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Participant Duplicate",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_participant_duplicate",
            "email": "organizer_participant_duplicate@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Organizer Participant Duplicate",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "参与人去重会议",
            "description": "同一会议不可重复添加同一用户",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    first_create_resp = auth_client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": user_id,
            "participant_role": "required",
            "attendance_status": "invited",
        },
    )
    assert first_create_resp.status_code == 201

    second_create_resp = auth_client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": user_id,
            "participant_role": "optional",
            "attendance_status": "invited",
        },
    )
    assert second_create_resp.status_code == 409
    assert second_create_resp.json()["detail"] == "Participant already exists in meeting"


def test_get_participant_by_id_returns_email_and_fields(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "participant_detail",
            "email": "participant_detail@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Participant Detail",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_participant_detail",
            "email": "organizer_participant_detail@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Organizer Participant Detail",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "参与人详情会议",
            "description": "测试参与人详情返回",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    create_resp = auth_client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": user_id,
            "participant_role": "required",
            "attendance_status": "invited",
        },
    )
    assert create_resp.status_code == 201
    participant_id = create_resp.json()["id"]

    get_resp = auth_client.get(f"/api/v1/participants/{participant_id}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["id"] == participant_id
    assert body["meeting_id"] == meeting_id
    assert body["user_id"] == user_id
    assert body["email"] == "participant_detail@example.com"
    assert body["participant_role"] == "required"
    assert body["attendance_status"] == "invited"


def test_update_participant_api_updates_fields(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "participant_update",
            "email": "participant_update@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Participant Update",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_participant_update",
            "email": "organizer_participant_update@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Organizer Participant Update",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "参与人更新会议",
            "description": "测试参与人更新",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    create_resp = auth_client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": user_id,
            "participant_role": "optional",
            "attendance_status": "invited",
        },
    )
    assert create_resp.status_code == 201
    participant_id = create_resp.json()["id"]

    update_resp = auth_client.patch(
        f"/api/v1/participants/{participant_id}",
        json={
            "participant_role": "required",
            "attendance_status": "accepted",
        },
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["id"] == participant_id
    assert body["participant_role"] == "required"
    assert body["attendance_status"] == "accepted"


def test_delete_participant_api_removes_and_handles_not_found(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "participant_delete",
            "email": "participant_delete@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Participant Delete",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    organizer_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "organizer_participant_delete",
            "email": "organizer_participant_delete@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Organizer Participant Delete",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "参与人删除会议",
            "description": "测试参与人删除",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    create_resp = auth_client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": user_id,
            "participant_role": "required",
            "attendance_status": "invited",
        },
    )
    assert create_resp.status_code == 201
    participant_id = create_resp.json()["id"]

    delete_resp = auth_client.delete(f"/api/v1/participants/{participant_id}")
    assert delete_resp.status_code == 204

    get_deleted_resp = auth_client.get(f"/api/v1/participants/{participant_id}")
    assert get_deleted_resp.status_code == 404
    assert get_deleted_resp.json()["detail"] == "Participant not found"

    delete_again_resp = auth_client.delete(f"/api/v1/participants/{participant_id}")
    assert delete_again_resp.status_code == 404
    assert delete_again_resp.json()["detail"] == "Participant not found"


def test_participant_management_requires_organizer_or_admin(client) -> None:
    organizer_resp = client.post(
        "/api/v1/users",
        json={
            "username": "participant_auth_owner",
            "email": "participant_auth_owner@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Participant Auth Owner",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    other_resp = client.post(
        "/api/v1/users",
        json={
            "username": "participant_auth_other",
            "email": "participant_auth_other@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Participant Auth Other",
            "role": "member",
        },
    )
    assert other_resp.status_code == 201
    other_user_id = other_resp.json()["id"]

    admin_resp = client.post(
        "/api/v1/users",
        json={
            "username": "participant_auth_admin",
            "email": "participant_auth_admin@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Participant Auth Admin",
            "role": "admin",
        },
    )
    assert admin_resp.status_code == 201
    admin_user_id = admin_resp.json()["id"]

    organizer_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "participant_auth_owner", "password": "plain-password"},
    )
    assert organizer_login_resp.status_code == 200
    organizer_headers = {"Authorization": f"Bearer {organizer_login_resp.json()['access_token']}"}

    other_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "participant_auth_other", "password": "plain-password"},
    )
    assert other_login_resp.status_code == 200
    other_headers = {"Authorization": f"Bearer {other_login_resp.json()['access_token']}"}

    admin_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "participant_auth_admin", "password": "plain-password"},
    )
    assert admin_login_resp.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login_resp.json()['access_token']}"}

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "参与者权限会议",
            "description": "仅组织者或管理员可管理参与者",
            "organizer_id": organizer_id,
        },
        headers=organizer_headers,
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    forbidden_create_resp = client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": other_user_id,
            "participant_role": "required",
            "attendance_status": "invited",
        },
        headers=other_headers,
    )
    assert forbidden_create_resp.status_code == 403
    assert forbidden_create_resp.json()["detail"] == "Not authorized to manage participants for this meeting"

    organizer_create_resp = client.post(
        "/api/v1/participants",
        json={
            "meeting_id": meeting_id,
            "user_id": other_user_id,
            "participant_role": "required",
            "attendance_status": "invited",
        },
        headers=organizer_headers,
    )
    assert organizer_create_resp.status_code == 201
    participant_id = organizer_create_resp.json()["id"]

    forbidden_list_resp = client.get(f"/api/v1/participants?meeting_id={meeting_id}", headers=other_headers)
    assert forbidden_list_resp.status_code == 403
    assert forbidden_list_resp.json()["detail"] == "Not authorized to manage participants for this meeting"

    admin_list_resp = client.get(f"/api/v1/participants?meeting_id={meeting_id}", headers=admin_headers)
    assert admin_list_resp.status_code == 200
    assert len(admin_list_resp.json()) == 1

    forbidden_update_resp = client.patch(
        f"/api/v1/participants/{participant_id}",
        json={"attendance_status": "accepted"},
        headers=other_headers,
    )
    assert forbidden_update_resp.status_code == 403
    assert forbidden_update_resp.json()["detail"] == "Not authorized to manage participants for this meeting"

    admin_update_resp = client.patch(
        f"/api/v1/participants/{participant_id}",
        json={"attendance_status": "accepted"},
        headers=admin_headers,
    )
    assert admin_update_resp.status_code == 200
    assert admin_update_resp.json()["attendance_status"] == "accepted"

    forbidden_delete_resp = client.delete(f"/api/v1/participants/{participant_id}", headers=other_headers)
    assert forbidden_delete_resp.status_code == 403
    assert forbidden_delete_resp.json()["detail"] == "Not authorized to manage participants for this meeting"

    admin_delete_resp = client.delete(f"/api/v1/participants/{participant_id}", headers=admin_headers)
    assert admin_delete_resp.status_code == 204


def test_task_management_requires_assignee_reporter_organizer_or_admin(client) -> None:
    organizer_resp = client.post(
        "/api/v1/users",
        json={
            "username": "task_auth_owner",
            "email": "task_auth_owner@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Task Auth Owner",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    assignee_resp = client.post(
        "/api/v1/users",
        json={
            "username": "task_auth_assignee",
            "email": "task_auth_assignee@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Task Auth Assignee",
            "role": "member",
        },
    )
    assert assignee_resp.status_code == 201
    assignee_id = assignee_resp.json()["id"]

    reporter_resp = client.post(
        "/api/v1/users",
        json={
            "username": "task_auth_reporter",
            "email": "task_auth_reporter@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Task Auth Reporter",
            "role": "member",
        },
    )
    assert reporter_resp.status_code == 201
    reporter_id = reporter_resp.json()["id"]

    outsider_resp = client.post(
        "/api/v1/users",
        json={
            "username": "task_auth_outsider",
            "email": "task_auth_outsider@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Task Auth Outsider",
            "role": "member",
        },
    )
    assert outsider_resp.status_code == 201
    outsider_id = outsider_resp.json()["id"]

    admin_resp = client.post(
        "/api/v1/users",
        json={
            "username": "task_auth_admin",
            "email": "task_auth_admin@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Task Auth Admin",
            "role": "admin",
        },
    )
    assert admin_resp.status_code == 201

    def login_headers(username: str) -> dict[str, str]:
        login_resp = client.post("/api/v1/auth/login", data={"username": username, "password": "plain-password"})
        assert login_resp.status_code == 200
        return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    organizer_headers = login_headers("task_auth_owner")
    assignee_headers = login_headers("task_auth_assignee")
    reporter_headers = login_headers("task_auth_reporter")
    outsider_headers = login_headers("task_auth_outsider")
    admin_headers = login_headers("task_auth_admin")

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "任务权限会议",
            "description": "测试任务权限",
            "organizer_id": organizer_id,
        },
        headers=organizer_headers,
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    forbidden_create_resp = client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "越权创建任务",
            "assignee_id": assignee_id,
            "reporter_id": reporter_id,
        },
        headers=outsider_headers,
    )
    assert forbidden_create_resp.status_code == 403
    assert forbidden_create_resp.json()["detail"] == "Not authorized to manage tasks for this meeting"

    organizer_task_resp = client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "组织者创建任务",
            "assignee_id": assignee_id,
            "reporter_id": reporter_id,
        },
        headers=organizer_headers,
    )
    assert organizer_task_resp.status_code == 201
    task_id = organizer_task_resp.json()["id"]

    forbidden_update_resp = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=outsider_headers,
    )
    assert forbidden_update_resp.status_code == 403
    assert forbidden_update_resp.json()["detail"] == "Not authorized to manage this task"

    assignee_update_resp = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=assignee_headers,
    )
    assert assignee_update_resp.status_code == 200

    reporter_update_resp = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "done"},
        headers=reporter_headers,
    )
    assert reporter_update_resp.status_code == 200

    outsider_delete_resp = client.delete(f"/api/v1/tasks/{task_id}", headers=outsider_headers)
    assert outsider_delete_resp.status_code == 403
    assert outsider_delete_resp.json()["detail"] == "Not authorized to manage this task"

    admin_delete_resp = client.delete(f"/api/v1/tasks/{task_id}", headers=admin_headers)
    assert admin_delete_resp.status_code == 204

    organizer_delete_resp = client.delete(f"/api/v1/tasks/{task_id}", headers=organizer_headers)
    assert organizer_delete_resp.status_code == 404


def test_meeting_management_requires_organizer_or_admin(client) -> None:
    organizer_resp = client.post(
        "/api/v1/users",
        json={
            "username": "meeting_auth_owner",
            "email": "meeting_auth_owner@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Meeting Auth Owner",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    outsider_resp = client.post(
        "/api/v1/users",
        json={
            "username": "meeting_auth_outsider",
            "email": "meeting_auth_outsider@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Meeting Auth Outsider",
            "role": "member",
        },
    )
    assert outsider_resp.status_code == 201

    admin_resp = client.post(
        "/api/v1/users",
        json={
            "username": "meeting_auth_admin",
            "email": "meeting_auth_admin@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Meeting Auth Admin",
            "role": "admin",
        },
    )
    assert admin_resp.status_code == 201

    def login_headers(username: str) -> dict[str, str]:
        login_resp = client.post("/api/v1/auth/login", data={"username": username, "password": "plain-password"})
        assert login_resp.status_code == 200
        return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    organizer_headers = login_headers("meeting_auth_owner")
    outsider_headers = login_headers("meeting_auth_outsider")
    admin_headers = login_headers("meeting_auth_admin")

    forbidden_create_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "越权创建会议",
            "description": "非组织者本人不可创建",
            "organizer_id": organizer_id,
        },
        headers=outsider_headers,
    )
    assert forbidden_create_resp.status_code == 403
    assert forbidden_create_resp.json()["detail"] == "Not authorized to manage this meeting"

    organizer_create_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "会议权限验证",
            "description": "仅组织者或管理员可管理",
            "organizer_id": organizer_id,
        },
        headers=organizer_headers,
    )
    assert organizer_create_resp.status_code == 201
    meeting_id = organizer_create_resp.json()["id"]

    forbidden_update_resp = client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={"status": "ongoing"},
        headers=outsider_headers,
    )
    assert forbidden_update_resp.status_code == 403
    assert forbidden_update_resp.json()["detail"] == "Not authorized to manage this meeting"

    organizer_update_resp = client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={"status": "ongoing"},
        headers=organizer_headers,
    )
    assert organizer_update_resp.status_code == 200

    transcript_resp = client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "Owner",
            "segment_index": 1,
            "content": "请大家确认会议管理权限。",
        },
        headers=organizer_headers,
    )
    assert transcript_resp.status_code == 201

    forbidden_postprocess_resp = client.post(
        f"/api/v1/meetings/{meeting_id}/postprocess",
        headers=outsider_headers,
    )
    assert forbidden_postprocess_resp.status_code == 403
    assert forbidden_postprocess_resp.json()["detail"] == "Not authorized to manage this meeting"

    organizer_postprocess_resp = client.post(
        f"/api/v1/meetings/{meeting_id}/postprocess",
        headers=organizer_headers,
    )
    assert organizer_postprocess_resp.status_code == 200

    forbidden_export_resp = client.post(
        f"/api/v1/meetings/{meeting_id}/export",
        json={"format": "txt"},
        headers=outsider_headers,
    )
    assert forbidden_export_resp.status_code == 403
    assert forbidden_export_resp.json()["detail"] == "Not authorized to manage this meeting"

    admin_export_resp = client.post(
        f"/api/v1/meetings/{meeting_id}/export",
        json={"format": "txt"},
        headers=admin_headers,
    )
    assert admin_export_resp.status_code == 200

    forbidden_audio_resp = client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("demo.wav", b"RIFF....WAVEfmt", "audio/wav")},
        headers=outsider_headers,
    )
    assert forbidden_audio_resp.status_code == 403
    assert forbidden_audio_resp.json()["detail"] == "Not authorized to manage this meeting"

    admin_audio_resp = client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("demo.wav", b"RIFF....WAVEfmt", "audio/wav")},
        headers=admin_headers,
    )
    assert admin_audio_resp.status_code == 201

    forbidden_delete_resp = client.delete(f"/api/v1/meetings/{meeting_id}", headers=outsider_headers)
    assert forbidden_delete_resp.status_code == 403
    assert forbidden_delete_resp.json()["detail"] == "Not authorized to manage this meeting"

    admin_delete_resp = client.delete(f"/api/v1/meetings/{meeting_id}", headers=admin_headers)
    assert admin_delete_resp.status_code == 204


def test_upload_meeting_audio_rejects_oversized_file(auth_client, monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "meeting_audio_max_size_bytes", 8, raising=False)

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "audio_limit_owner",
            "email": "audio_limit_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Audio Limit Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "音频限制会议",
            "description": "测试音频上传大小限制",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    oversized_resp = auth_client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("oversized.wav", b"123456789", "audio/wav")},
    )

    assert oversized_resp.status_code == 413
    assert oversized_resp.json()["detail"] == "Uploaded audio file exceeds size limit"
    assert oversized_resp.json()["error_code"] == "PAYLOAD_TOO_LARGE"


def test_transcript_management_requires_organizer_or_admin(client) -> None:
    organizer_resp = client.post(
        "/api/v1/users",
        json={
            "username": "transcript_auth_owner",
            "email": "transcript_auth_owner@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Transcript Auth Owner",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    outsider_resp = client.post(
        "/api/v1/users",
        json={
            "username": "transcript_auth_outsider",
            "email": "transcript_auth_outsider@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Transcript Auth Outsider",
            "role": "member",
        },
    )
    assert outsider_resp.status_code == 201

    admin_resp = client.post(
        "/api/v1/users",
        json={
            "username": "transcript_auth_admin",
            "email": "transcript_auth_admin@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Transcript Auth Admin",
            "role": "admin",
        },
    )
    assert admin_resp.status_code == 201

    def login_headers(username: str) -> dict[str, str]:
        login_resp = client.post("/api/v1/auth/login", data={"username": username, "password": "plain-password"})
        assert login_resp.status_code == 200
        return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    organizer_headers = login_headers("transcript_auth_owner")
    outsider_headers = login_headers("transcript_auth_outsider")
    admin_headers = login_headers("transcript_auth_admin")

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "转写权限会议",
            "description": "仅组织者或管理员可管理转写",
            "organizer_id": organizer_id,
        },
        headers=organizer_headers,
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    forbidden_create_resp = client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "Owner",
            "segment_index": 1,
            "content": "越权创建转写",
        },
        headers=outsider_headers,
    )
    assert forbidden_create_resp.status_code == 403
    assert forbidden_create_resp.json()["detail"] == "Not authorized to manage transcripts for this meeting"

    organizer_create_resp = client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "Owner",
            "segment_index": 1,
            "content": "组织者创建转写",
        },
        headers=organizer_headers,
    )
    assert organizer_create_resp.status_code == 201
    transcript_id = organizer_create_resp.json()["id"]

    forbidden_list_resp = client.get(f"/api/v1/transcripts?meeting_id={meeting_id}", headers=outsider_headers)
    assert forbidden_list_resp.status_code == 403
    assert forbidden_list_resp.json()["detail"] == "Not authorized to manage transcripts for this meeting"

    admin_list_resp = client.get(f"/api/v1/transcripts?meeting_id={meeting_id}", headers=admin_headers)
    assert admin_list_resp.status_code == 200
    assert len(admin_list_resp.json()) == 1

    forbidden_get_resp = client.get(f"/api/v1/transcripts/{transcript_id}", headers=outsider_headers)
    assert forbidden_get_resp.status_code == 403
    assert forbidden_get_resp.json()["detail"] == "Not authorized to manage transcripts for this meeting"

    forbidden_update_resp = client.patch(
        f"/api/v1/transcripts/{transcript_id}",
        json={"content": "越权修改转写"},
        headers=outsider_headers,
    )
    assert forbidden_update_resp.status_code == 403
    assert forbidden_update_resp.json()["detail"] == "Not authorized to manage transcripts for this meeting"

    admin_update_resp = client.patch(
        f"/api/v1/transcripts/{transcript_id}",
        json={"content": "管理员修改转写"},
        headers=admin_headers,
    )
    assert admin_update_resp.status_code == 200

    forbidden_delete_resp = client.delete(f"/api/v1/transcripts/{transcript_id}", headers=outsider_headers)
    assert forbidden_delete_resp.status_code == 403
    assert forbidden_delete_resp.json()["detail"] == "Not authorized to manage transcripts for this meeting"

    admin_delete_resp = client.delete(f"/api/v1/transcripts/{transcript_id}", headers=admin_headers)
    assert admin_delete_resp.status_code == 204


def test_create_meeting_rejects_nonexistent_organizer(auth_client) -> None:
    create_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "无效组织者会议",
            "description": "组织者不存在",
            "organizer_id": 9999,
        },
    )

    assert create_resp.status_code == 404
    assert create_resp.json()["detail"] == "Organizer not found"


def test_create_meeting_rejects_invalid_schedule_range(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "schedule_owner",
            "email": "schedule_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Schedule Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    create_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "时间非法会议",
            "organizer_id": organizer_id,
            "scheduled_start_at": "2026-03-14T10:00:00Z",
            "scheduled_end_at": "2026-03-14T09:00:00Z",
        },
    )

    assert create_resp.status_code == 400
    assert create_resp.json()["detail"] == "scheduled_end_at must be after or equal to scheduled_start_at"


def test_meeting_postprocess_generates_summary_and_tasks(auth_client) -> None:
    """会议转写后处理可生成摘要和任务。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "pm01",
            "email": "pm@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "PM",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    assignee_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "zhangsan",
            "email": "zhangsan@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "张三",
            "role": "member",
        },
    )
    assert assignee_resp.status_code == 201
    zhangsan_id = assignee_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "周会",
            "description": "项目推进周会",
            "organizer_id": organizer_id,
            "location": "A101",
        },
    )
    meeting_id = meeting_resp.json()["id"]

    auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM",
            "segment_index": 1,
            "content": "今天确认了两个行动项：请张三本周五前提交接口文档；李四负责下周一前完成前端联调。",
        },
    )
    auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM",
            "segment_index": 2,
            "content": "风险点是测试环境资源不足，需要运维支持扩容。",
        },
    )

    process_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert process_resp.status_code == 200

    body = process_resp.json()
    assert body["meeting_id"] == meeting_id
    assert body["summary"]
    assert len(body["tasks"]) >= 1
    assert body["tasks"][0]["meeting_id"] == meeting_id
    assert body["tasks"][0]["assignee_id"] == zhangsan_id
    assert body["tasks"][0]["priority"] in ("high", "medium", "low")

    meeting_detail = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert meeting_detail.status_code == 200
    assert meeting_detail.json()["summary"] == body["summary"]
    assert meeting_detail.json()["postprocessed_at"] is not None
    assert meeting_detail.json()["postprocess_version"] in ("rule-v1", "llm-summary-v1")


def test_meeting_postprocess_requires_transcripts(auth_client) -> None:
    """无转写数据时后处理应拒绝。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "owner",
            "email": "owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "空白会议",
            "description": "暂无转写",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    process_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert process_resp.status_code == 400
    assert process_resp.json()["detail"] == "No transcripts found for meeting"


def test_meeting_export_flow(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "exporter",
            "email": "exporter@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Exporter",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "导出会议",
            "description": "测试纪要导出",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    transcript_resp = auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM",
            "segment_index": 1,
            "content": "今天确认导出功能，张三负责实现。",
        },
    )
    assert transcript_resp.status_code == 201

    postprocess_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert postprocess_resp.status_code == 200

    export_resp = auth_client.post(
        f"/api/v1/meetings/{meeting_id}/export",
        json={"format": "txt"},
    )
    assert export_resp.status_code == 200
    body = export_resp.json()
    assert body["meeting_id"] == meeting_id
    assert body["format"] == "txt"
    assert body["filename"].endswith(".txt")
    assert "导出会议" in body["content"]


def test_meeting_share_is_idempotent(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "share_owner",
            "email": "share_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Share Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "分享会议",
            "description": "验证分享链接",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    transcript_resp = auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM",
            "segment_index": 1,
            "content": "请张三本周五前完成接口文档。",
        },
    )
    assert transcript_resp.status_code == 201

    postprocess_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert postprocess_resp.status_code == 200

    first_share_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/share")
    assert first_share_resp.status_code == 200
    first_share = first_share_resp.json()
    assert first_share["meeting_id"] == meeting_id
    assert first_share["created_now"] is True
    assert first_share["share_token"]
    assert first_share["share_path"] == f"/shared/meetings/{first_share['share_token']}"
    assert first_share["shared_at"] is not None

    second_share_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/share")
    assert second_share_resp.status_code == 200
    second_share = second_share_resp.json()
    assert second_share["meeting_id"] == meeting_id
    assert second_share["created_now"] is False
    assert second_share["share_token"] == first_share["share_token"]
    assert second_share["share_path"] == first_share["share_path"]
    assert second_share["shared_at"] == first_share["shared_at"]


def test_meeting_share_requires_summary(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "share_blocker",
            "email": "share_blocker@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Share Blocker",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "无摘要分享会",
            "description": "不应允许分享",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    share_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/share")
    assert share_resp.status_code == 400
    assert share_resp.json()["detail"] == "No summary available for share"


def test_get_shared_meeting_returns_read_only_payload(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "shared_reader",
            "email": "shared_reader@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Shared Reader",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "只读分享会议",
            "description": "验证分享页",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    transcript_resp = auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM",
            "segment_index": 1,
            "content": "请李四今天补齐测试报告。",
        },
    )
    assert transcript_resp.status_code == 201

    postprocess_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert postprocess_resp.status_code == 200

    share_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/share")
    assert share_resp.status_code == 200
    share_token = share_resp.json()["share_token"]

    shared_resp = auth_client.get(f"/api/v1/shared/meetings/{share_token}")
    assert shared_resp.status_code == 200
    body = shared_resp.json()
    assert body["meeting"]["id"] == meeting_id
    assert body["meeting"]["title"] == "只读分享会议"
    assert body["meeting"]["summary"]
    assert body["meeting"]["organizer"]["full_name"] == "Shared Reader"
    assert len(body["transcripts"]) == 1
    assert body["transcripts"][0]["meeting_id"] == meeting_id
    assert len(body["tasks"]) >= 1
    assert body["tasks"][0]["meeting_id"] == meeting_id


def test_get_shared_meeting_invalid_token_returns_404(client) -> None:
    response = client.get("/api/v1/shared/meetings/not-a-real-token")

    assert response.status_code == 404
    assert response.json()["detail"] == "Shared meeting not found"


def test_get_shared_meeting_public_access_without_auth(client) -> None:
    owner_resp = client.post(
        "/api/v1/users",
        json={
            "username": "public_share_owner",
            "email": "public_share_owner@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Public Share Owner",
            "role": "member",
        },
    )
    assert owner_resp.status_code == 201
    owner_id = owner_resp.json()["id"]

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "public_share_owner", "password": "plain-password"},
    )
    assert login_resp.status_code == 200
    owner_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "公开分享会议",
            "description": "验证分享链接匿名访问",
            "organizer_id": owner_id,
        },
        headers=owner_headers,
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    transcript_resp = client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": owner_id,
            "speaker_name": "Owner",
            "segment_index": 1,
            "content": "请确认公开分享可匿名访问。",
        },
        headers=owner_headers,
    )
    assert transcript_resp.status_code == 201

    postprocess_resp = client.post(f"/api/v1/meetings/{meeting_id}/postprocess", headers=owner_headers)
    assert postprocess_resp.status_code == 200

    share_resp = client.post(f"/api/v1/meetings/{meeting_id}/share", headers=owner_headers)
    assert share_resp.status_code == 200
    share_token = share_resp.json()["share_token"]

    public_resp = client.get(f"/api/v1/shared/meetings/{share_token}")
    assert public_resp.status_code == 200
    body = public_resp.json()
    assert body["meeting"]["id"] == meeting_id
    assert body["meeting"]["summary"]
    assert isinstance(body["transcripts"], list)
    assert isinstance(body["tasks"], list)


def test_meeting_share_requires_organizer(client) -> None:
    organizer_resp = client.post(
        "/api/v1/users",
        json={
            "username": "share_owner_auth",
            "email": "share_owner_auth@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Share Owner Auth",
            "role": "member",
        },
    )
    assert organizer_resp.status_code == 201
    organizer_id = organizer_resp.json()["id"]

    other_user_resp = client.post(
        "/api/v1/users",
        json={
            "username": "share_other_auth",
            "email": "share_other_auth@example.com",
            "password_hash": get_password_hash("plain-password"),
            "full_name": "Share Other Auth",
            "role": "member",
        },
    )
    assert other_user_resp.status_code == 201

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "权限分享会议",
            "description": "仅组织者可分享",
            "organizer_id": organizer_id,
        },
        headers={"Authorization": "Bearer invalid"},
    )
    assert meeting_resp.status_code == 401

    organizer_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "share_owner_auth", "password": "plain-password"},
    )
    assert organizer_login_resp.status_code == 200
    organizer_token = organizer_login_resp.json()["access_token"]
    organizer_headers = {"Authorization": f"Bearer {organizer_token}"}

    other_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "share_other_auth", "password": "plain-password"},
    )
    assert other_login_resp.status_code == 200
    other_token = other_login_resp.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "权限分享会议",
            "description": "仅组织者可分享",
            "organizer_id": organizer_id,
        },
        headers=organizer_headers,
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    transcript_resp = client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "Owner",
            "segment_index": 1,
            "content": "请大家确认分享权限。",
        },
        headers=organizer_headers,
    )
    assert transcript_resp.status_code == 201

    postprocess_resp = client.post(f"/api/v1/meetings/{meeting_id}/postprocess", headers=organizer_headers)
    assert postprocess_resp.status_code == 200

    forbidden_share_resp = client.post(f"/api/v1/meetings/{meeting_id}/share", headers=other_headers)
    assert forbidden_share_resp.status_code == 403
    assert forbidden_share_resp.json()["detail"] == "Only meeting organizer can create share link"


def test_meeting_postprocess_idempotent_and_force_regenerate(auth_client) -> None:
    """后处理默认幂等，force_regenerate 可重建任务。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "pm02",
            "email": "pm02@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "PM2",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "迭代会",
            "description": "验证后处理幂等",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    transcript_resp = auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM2",
            "segment_index": 1,
            "content": "请王五今天内完成埋点校验。",
        },
    )
    assert transcript_resp.status_code == 201

    first_process_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert first_process_resp.status_code == 200
    assert len(first_process_resp.json()["tasks"]) == 1

    second_transcript_resp = auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM2",
            "segment_index": 2,
            "content": "李四负责下周前完成接口联调。",
        },
    )
    assert second_transcript_resp.status_code == 201

    second_process_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert second_process_resp.status_code == 200
    assert len(second_process_resp.json()["tasks"]) == 1

    force_process_resp = auth_client.post(
        f"/api/v1/meetings/{meeting_id}/postprocess?force_regenerate=true"
    )
    assert force_process_resp.status_code == 200
    assert len(force_process_resp.json()["tasks"]) == 2

    meeting_detail = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert meeting_detail.status_code == 200
    assert meeting_detail.json()["summary"]
    assert meeting_detail.json()["postprocessed_at"] is not None
    assert meeting_detail.json()["postprocess_version"] in ("rule-v1", "llm-summary-v1")


def test_audio_upload_for_meeting(auth_client) -> None:
    """会议音频可上传并返回元数据。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "audio01",
            "email": "audio01@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Audio User",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "音频上传会",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    upload_resp = auth_client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("demo.wav", b"RIFF....WAVEfmt", "audio/wav")},
    )
    assert upload_resp.status_code == 201
    body = upload_resp.json()
    assert body["meeting_id"] == meeting_id
    assert body["filename"] == "demo.wav"
    assert body["size_bytes"] > 0
    assert body["content_type"] == "audio/wav"
    assert body["storage_path"]


def test_transcribe_latest_audio_generates_transcript(auth_client) -> None:
    """占位语音识别可将最新音频写入转写记录。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "asr01",
            "email": "asr01@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "ASR User",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "语音识别会",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    upload_resp = auth_client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("speech.wav", b"RIFF....WAVEfmt", "audio/wav")},
    )
    assert upload_resp.status_code == 201

    transcribe_resp = auth_client.post(f"/api/v1/meetings/{meeting_id}/audio/transcribe")
    assert transcribe_resp.status_code == 201
    transcribe_body = transcribe_resp.json()
    assert transcribe_body["meeting_id"] == meeting_id
    assert transcribe_body["source"] in ("mock-asr", "manual")
    assert transcribe_body["content"]

    list_resp = auth_client.get(f"/api/v1/transcripts?meeting_id={meeting_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_task_status_transition_and_completed_at(auth_client) -> None:
    """任务状态流转合法时自动维护完成时间。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "task01",
            "email": "task01@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Task Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "任务状态会",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    task_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "完成接口联调",
            "assignee_id": organizer_id,
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    start_resp = auth_client.patch(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"})
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "in_progress"
    assert start_resp.json()["completed_at"] is None

    done_resp = auth_client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"})
    assert done_resp.status_code == 200
    assert done_resp.json()["status"] == "done"
    assert done_resp.json()["completed_at"] is not None

    reopen_resp = auth_client.patch(f"/api/v1/tasks/{task_id}", json={"status": "todo"})
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["status"] == "todo"
    assert reopen_resp.json()["completed_at"] is None


def test_task_status_transition_rejects_invalid_flow(auth_client) -> None:
    """非法状态流转应返回 400。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "task02",
            "email": "task02@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Task Owner 2",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "非法流转会",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    task_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "直接完成",
            "assignee_id": organizer_id,
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    invalid_resp = auth_client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"})
    assert invalid_resp.status_code == 400
    assert invalid_resp.json()["detail"] == "Invalid task status transition: todo -> done"


def test_list_tasks_can_filter_by_meeting_id(auth_client) -> None:
    """任务列表支持按 meeting_id 过滤。"""

    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "task03",
            "email": "task03@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Task Owner 3",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_a_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "过滤会议A", "organizer_id": organizer_id},
    )
    meeting_b_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "过滤会议B", "organizer_id": organizer_id},
    )
    meeting_a_id = meeting_a_resp.json()["id"]
    meeting_b_id = meeting_b_resp.json()["id"]

    auth_client.post(
        "/api/v1/tasks",
        json={"meeting_id": meeting_a_id, "title": "A任务1", "assignee_id": organizer_id},
    )
    auth_client.post(
        "/api/v1/tasks",
        json={"meeting_id": meeting_b_id, "title": "B任务1", "assignee_id": organizer_id},
    )

    filter_resp = auth_client.get(f"/api/v1/tasks?meeting_id={meeting_a_id}")
    assert filter_resp.status_code == 200
    body = filter_resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["meeting_id"] == meeting_a_id


def test_list_tasks_filters_and_sets_reminder_flags(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "task_filter_owner",
            "email": "task_filter_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Task Filter Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "任务筛选会议", "organizer_id": organizer_id},
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    overdue_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "紧急修复线上接口",
            "assignee_id": organizer_id,
            "priority": "high",
            "status": "todo",
            "due_at": "2000-01-01T00:00:00Z",
        },
    )
    assert overdue_resp.status_code == 201

    due_soon_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "整理发布说明文档",
            "assignee_id": organizer_id,
            "priority": "medium",
            "status": "in_progress",
            "due_at": "2999-01-01T00:00:00Z",
        },
    )
    assert due_soon_resp.status_code == 201

    done_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "历史归档任务",
            "assignee_id": organizer_id,
            "priority": "low",
            "status": "todo",
            "due_at": "2000-01-01T00:00:00Z",
        },
    )
    assert done_resp.status_code == 201

    done_id = done_resp.json()["id"]
    patched_in_progress_resp = auth_client.patch(
        f"/api/v1/tasks/{done_id}",
        json={"status": "in_progress"},
    )
    assert patched_in_progress_resp.status_code == 200

    back_to_done_resp = auth_client.patch(
        f"/api/v1/tasks/{done_id}",
        json={"status": "done"},
    )
    assert back_to_done_resp.status_code == 200

    filtered_resp = auth_client.get(
        "/api/v1/tasks"
        f"?meeting_id={meeting_id}&status=todo&priority=high&keyword=线上"
    )
    assert filtered_resp.status_code == 200
    body = filtered_resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "紧急修复线上接口"
    assert body["items"][0]["is_overdue"] is True
    assert body["items"][0]["is_due_soon"] is False

    status_resp = auth_client.get(f"/api/v1/tasks?meeting_id={meeting_id}&status=in_progress")
    assert status_resp.status_code == 200
    status_body = status_resp.json()
    assert status_body["total"] == 1
    assert len(status_body["items"]) == 1
    assert status_body["items"][0]["title"] == "整理发布说明文档"
    assert status_body["items"][0]["is_overdue"] is False
    assert status_body["items"][0]["is_due_soon"] is False

    done_list_resp = auth_client.get(f"/api/v1/tasks?meeting_id={meeting_id}&status=done")
    assert done_list_resp.status_code == 200
    done_body = done_list_resp.json()
    assert done_body["total"] == 1
    assert len(done_body["items"]) == 1
    assert done_body["items"][0]["title"] == "历史归档任务"
    assert done_body["items"][0]["is_overdue"] is False
    assert done_body["items"][0]["is_due_soon"] is False


def test_list_tasks_supports_pagination_total_and_due_at_sort(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "task_page_owner",
            "email": "task_page_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Task Page Owner",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    owner_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "分页排序会议", "organizer_id": owner_id},
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    early_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "early",
            "assignee_id": owner_id,
            "due_at": "2026-01-01T00:00:00Z",
        },
    )
    assert early_resp.status_code == 201
    early_id = early_resp.json()["id"]

    late_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "late",
            "assignee_id": owner_id,
            "due_at": "2026-12-31T00:00:00Z",
        },
    )
    assert late_resp.status_code == 201
    late_id = late_resp.json()["id"]

    null_resp = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "null",
            "assignee_id": owner_id,
        },
    )
    assert null_resp.status_code == 201
    null_id = null_resp.json()["id"]

    sort_resp = auth_client.get(
        f"/api/v1/tasks?meeting_id={meeting_id}&sort_by=due_at_asc"
    )
    assert sort_resp.status_code == 200
    sort_body = sort_resp.json()
    assert sort_body["total"] == 3
    assert [item["id"] for item in sort_body["items"]] == [early_id, late_id, null_id]

    page_resp = auth_client.get(
        f"/api/v1/tasks?meeting_id={meeting_id}&sort_by=due_at_asc&limit=1&offset=1"
    )
    assert page_resp.status_code == 200
    page_body = page_resp.json()
    assert page_body["total"] == 3
    assert len(page_body["items"]) == 1
    assert page_body["items"][0]["id"] == late_id


def test_invalid_task_filter_returns_422(auth_client) -> None:
    response = auth_client.get("/api/v1/tasks?status=blocked")

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "REQUEST_VALIDATION_ERROR"


def test_list_meetings_supports_filters_and_pagination(auth_client) -> None:
    owner_a_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "meeting_filter_a",
            "email": "meeting_filter_a@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Meeting Filter A",
            "role": "member",
        },
    )
    assert owner_a_resp.status_code == 201
    owner_a_id = owner_a_resp.json()["id"]

    owner_b_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "meeting_filter_b",
            "email": "meeting_filter_b@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Meeting Filter B",
            "role": "member",
        },
    )
    assert owner_b_resp.status_code == 201
    owner_b_id = owner_b_resp.json()["id"]

    meeting_a_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "筛选会议A", "organizer_id": owner_a_id},
    )
    assert meeting_a_resp.status_code == 201
    meeting_a_id = meeting_a_resp.json()["id"]

    meeting_b_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "筛选会议B", "organizer_id": owner_b_id},
    )
    assert meeting_b_resp.status_code == 201
    meeting_b_id = meeting_b_resp.json()["id"]

    meeting_c_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "筛选会议C", "organizer_id": owner_a_id},
    )
    assert meeting_c_resp.status_code == 201
    meeting_c_id = meeting_c_resp.json()["id"]

    patch_a_resp = auth_client.patch(f"/api/v1/meetings/{meeting_a_id}", json={"status": "ongoing"})
    assert patch_a_resp.status_code == 200
    patch_c_resp = auth_client.patch(f"/api/v1/meetings/{meeting_c_id}", json={"status": "done"})
    assert patch_c_resp.status_code == 200

    organizer_filter_resp = auth_client.get(f"/api/v1/meetings?organizer_id={owner_a_id}")
    assert organizer_filter_resp.status_code == 200
    organizer_body = organizer_filter_resp.json()
    organizer_data = organizer_body["items"]
    assert organizer_body["total"] == 2
    assert len(organizer_data) == 2
    assert [item["id"] for item in organizer_data] == [meeting_c_id, meeting_a_id]

    status_filter_resp = auth_client.get("/api/v1/meetings?status=ongoing")
    assert status_filter_resp.status_code == 200
    status_body = status_filter_resp.json()
    status_data = status_body["items"]
    assert status_body["total"] == 1
    assert len(status_data) == 1
    assert status_data[0]["id"] == meeting_a_id

    limit_offset_resp = auth_client.get("/api/v1/meetings?limit=1&offset=1")
    assert limit_offset_resp.status_code == 200
    limit_offset_body = limit_offset_resp.json()
    limit_offset_data = limit_offset_body["items"]
    assert limit_offset_body["total"] == 3
    assert len(limit_offset_data) == 1
    assert limit_offset_data[0]["id"] == meeting_b_id


def test_get_meeting_detail_includes_organizer_object(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "meeting_detail_owner",
            "email": "meeting_detail_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Meeting Detail Owner",
            "role": "admin",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "详情增强会议",
            "description": "检查 organizer 嵌套对象",
            "organizer_id": organizer_id,
        },
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    detail_resp = auth_client.get(f"/api/v1/meetings/{meeting_id}")
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["id"] == meeting_id
    assert body["organizer_id"] == organizer_id
    assert body["organizer"]["id"] == organizer_id
    assert body["organizer"]["username"] == "meeting_detail_owner"
    assert body["organizer"]["email"] == "meeting_detail_owner@example.com"
    assert body["organizer"]["full_name"] == "Meeting Detail Owner"
    assert body["organizer"]["role"] == "admin"


def test_update_meeting_rejects_invalid_scheduled_range(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "meeting_patch_schedule",
            "email": "meeting_patch_schedule@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Meeting Patch Schedule",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "Patch Scheduled 校验", "organizer_id": organizer_id},
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    patch_resp = auth_client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={
            "scheduled_start_at": "2026-03-14T10:00:00Z",
            "scheduled_end_at": "2026-03-14T09:00:00Z",
        },
    )

    assert patch_resp.status_code == 400
    assert patch_resp.json()["detail"] == "scheduled_end_at must be after or equal to scheduled_start_at"


def test_update_meeting_rejects_invalid_actual_range(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "meeting_patch_actual",
            "email": "meeting_patch_actual@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Meeting Patch Actual",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "Patch Actual 校验", "organizer_id": organizer_id},
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    patch_resp = auth_client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={
            "actual_start_at": "2026-03-14T10:00:00Z",
            "actual_end_at": "2026-03-14T09:00:00Z",
        },
    )

    assert patch_resp.status_code == 400
    assert patch_resp.json()["detail"] == "actual_end_at must be after or equal to actual_start_at"


def test_create_transcript_rejects_nonexistent_meeting(auth_client) -> None:
    transcript_resp = auth_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": 9999,
            "speaker_name": "Ghost Speaker",
            "segment_index": 1,
            "content": "不存在的会议转写",
        },
    )

    assert transcript_resp.status_code == 404
    assert transcript_resp.json()["detail"] == "Meeting not found"


def test_create_participant_rejects_nonexistent_meeting_or_user(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "participant_guard",
            "email": "participant_guard@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Participant Guard",
            "role": "member",
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    invalid_meeting_resp = auth_client.post(
        "/api/v1/participants",
        json={"meeting_id": 9999, "user_id": user_id},
    )
    assert invalid_meeting_resp.status_code == 404
    assert invalid_meeting_resp.json()["detail"] == "Meeting not found"

    owner_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "participant_owner",
            "email": "participant_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Participant Owner",
            "role": "member",
        },
    )
    assert owner_resp.status_code == 201
    organizer_id = owner_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "参与人校验会议", "organizer_id": organizer_id},
    )
    assert meeting_resp.status_code == 201
    meeting_id = meeting_resp.json()["id"]

    invalid_user_resp = auth_client.post(
        "/api/v1/participants",
        json={"meeting_id": meeting_id, "user_id": 9999},
    )
    assert invalid_user_resp.status_code == 404
    assert invalid_user_resp.json()["detail"] == "User not found"


def test_postprocess_returns_structured_ai_error_when_ai_service_fails(safe_client, monkeypatch) -> None:
    user_resp = safe_client.post(
        "/api/v1/users",
        json={
            "username": "ai_error_owner",
            "email": "ai_error_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "AI Error Owner",
            "role": "member",
        },
    )
    organizer_id = user_resp.json()["id"]

    meeting_resp = safe_client.post(
        "/api/v1/meetings",
        json={"title": "AI 异常会议", "organizer_id": organizer_id},
    )
    meeting_id = meeting_resp.json()["id"]

    safe_client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "AI Error Owner",
            "segment_index": 1,
            "content": "请张三今天完成接口文档。",
        },
    )

    async def raise_llm_error(*args, **kwargs):
        raise LLMServiceError("upstream llm unavailable")

    monkeypatch.setattr(
        "app.api.v1.endpoints.meetings.build_meeting_summary_with_llm",
        raise_llm_error,
    )

    response = safe_client.post(f"/api/v1/meetings/{meeting_id}/postprocess")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "AI service unavailable",
        "error_code": "AI_SERVICE_UNAVAILABLE",
    }


def test_upload_returns_structured_internal_error(safe_client, monkeypatch) -> None:
    user_resp = safe_client.post(
        "/api/v1/users",
        json={
            "username": "internal_error_owner",
            "email": "internal_error_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Internal Error Owner",
            "role": "member",
        },
    )
    organizer_id = user_resp.json()["id"]

    meeting_resp = safe_client.post(
        "/api/v1/meetings",
        json={"title": "内部异常会议", "organizer_id": organizer_id},
    )
    meeting_id = meeting_resp.json()["id"]

    def raise_runtime_error(*args, **kwargs):
        raise RuntimeError("disk write failed")

    monkeypatch.setattr(
        "app.api.v1.endpoints.meetings.save_meeting_audio",
        raise_runtime_error,
    )

    response = safe_client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("demo.wav", b"RIFF....WAVEfmt", "audio/wav")},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error",
        "error_code": "INTERNAL_SERVER_ERROR",
    }


def test_create_user_rejects_invalid_role(auth_client) -> None:
    response = auth_client.post(
        "/api/v1/users",
        json={
            "username": "invalid_role_user",
            "email": "invalid_role_user@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Invalid Role User",
            "role": "super-admin",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "REQUEST_VALIDATION_ERROR"


def test_update_meeting_rejects_invalid_status_value(auth_client) -> None:
    user_resp = auth_client.post(
        "/api/v1/users",
        json={
            "username": "meeting_status_owner",
            "email": "meeting_status_owner@example.com",
            "password_hash": "hashed_password_123",
            "full_name": "Meeting Status Owner",
            "role": "member",
        },
    )
    organizer_id = user_resp.json()["id"]

    meeting_resp = auth_client.post(
        "/api/v1/meetings",
        json={"title": "状态校验会议", "organizer_id": organizer_id},
    )
    meeting_id = meeting_resp.json()["id"]

    response = auth_client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={"status": "archived"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "REQUEST_VALIDATION_ERROR"


def test_create_task_rejects_nonexistent_related_resources(auth_client) -> None:
    response = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": 9999,
            "transcript_id": 9998,
            "title": "无效关联任务",
            "assignee_id": 9997,
            "reporter_id": 9996,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_create_task_rejects_invalid_priority_and_status(auth_client) -> None:
    response = auth_client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": 1,
            "title": "非法枚举任务",
            "priority": "urgent",
            "status": "blocked",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "REQUEST_VALIDATION_ERROR"
