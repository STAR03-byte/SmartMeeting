def test_protected_meeting_list_requires_auth(client) -> None:
    resp = client.get("/api/v1/meetings")

    assert resp.status_code == 401


def test_protected_task_list_requires_auth(client) -> None:
    resp = client.get("/api/v1/tasks")

    assert resp.status_code == 401
