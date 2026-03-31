def test_protected_meeting_list_requires_auth(client) -> None:
    resp = client.get("/api/v1/meetings")

    assert resp.status_code == 401
    body = resp.json()
    assert body["detail"]
    assert body["error_code"] == "UNAUTHORIZED"


def test_protected_task_list_requires_auth(client) -> None:
    resp = client.get("/api/v1/tasks")

    assert resp.status_code == 401
    body = resp.json()
    assert body["detail"]
    assert body["error_code"] == "UNAUTHORIZED"
