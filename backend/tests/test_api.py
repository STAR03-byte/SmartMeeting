"""后端核心接口测试。"""


def test_health_check(client) -> None:
    """健康检查接口可用。"""

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user_crud_flow(client) -> None:
    """用户创建和查询流程可用。"""

    create_resp = client.post(
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

    get_resp = client.get(f"/api/v1/users/{user_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["username"] == "alice"

    list_resp = client.get("/api/v1/users")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_meeting_crud_flow(client) -> None:
    """会议创建和更新流程可用。"""

    user_resp = client.post(
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

    create_resp = client.post(
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

    patch_resp = client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={"status": "ongoing"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "ongoing"

    list_resp = client.get("/api/v1/meetings")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_meeting_postprocess_generates_summary_and_tasks(client) -> None:
    """会议转写后处理可生成摘要和任务。"""

    user_resp = client.post(
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

    assignee_resp = client.post(
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

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "周会",
            "description": "项目推进周会",
            "organizer_id": organizer_id,
            "location": "A101",
        },
    )
    meeting_id = meeting_resp.json()["id"]

    client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM",
            "segment_index": 1,
            "content": "今天确认了两个行动项：请张三本周五前提交接口文档；李四负责下周一前完成前端联调。",
        },
    )
    client.post(
        "/api/v1/transcripts",
        json={
            "meeting_id": meeting_id,
            "speaker_user_id": organizer_id,
            "speaker_name": "PM",
            "segment_index": 2,
            "content": "风险点是测试环境资源不足，需要运维支持扩容。",
        },
    )

    process_resp = client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert process_resp.status_code == 200

    body = process_resp.json()
    assert body["meeting_id"] == meeting_id
    assert body["summary"]
    assert len(body["tasks"]) >= 1
    assert body["tasks"][0]["meeting_id"] == meeting_id
    assert body["tasks"][0]["assignee_id"] == zhangsan_id
    assert body["tasks"][0]["priority"] == "high"

    meeting_detail = client.get(f"/api/v1/meetings/{meeting_id}")
    assert meeting_detail.status_code == 200
    assert meeting_detail.json()["summary"] == body["summary"]
    assert meeting_detail.json()["postprocessed_at"] is not None
    assert meeting_detail.json()["postprocess_version"] == "rule-v1"


def test_meeting_postprocess_requires_transcripts(client) -> None:
    """无转写数据时后处理应拒绝。"""

    user_resp = client.post(
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

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "空白会议",
            "description": "暂无转写",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    process_resp = client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert process_resp.status_code == 400
    assert process_resp.json()["detail"] == "No transcripts found for meeting"


def test_meeting_postprocess_idempotent_and_force_regenerate(client) -> None:
    """后处理默认幂等，force_regenerate 可重建任务。"""

    user_resp = client.post(
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

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "迭代会",
            "description": "验证后处理幂等",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    transcript_resp = client.post(
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

    first_process_resp = client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert first_process_resp.status_code == 200
    assert len(first_process_resp.json()["tasks"]) == 1

    second_transcript_resp = client.post(
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

    second_process_resp = client.post(f"/api/v1/meetings/{meeting_id}/postprocess")
    assert second_process_resp.status_code == 200
    assert len(second_process_resp.json()["tasks"]) == 1

    force_process_resp = client.post(
        f"/api/v1/meetings/{meeting_id}/postprocess?force_regenerate=true"
    )
    assert force_process_resp.status_code == 200
    assert len(force_process_resp.json()["tasks"]) == 2

    meeting_detail = client.get(f"/api/v1/meetings/{meeting_id}")
    assert meeting_detail.status_code == 200
    assert meeting_detail.json()["summary"]
    assert meeting_detail.json()["postprocessed_at"] is not None
    assert meeting_detail.json()["postprocess_version"] == "rule-v1"


def test_audio_upload_for_meeting(client) -> None:
    """会议音频可上传并返回元数据。"""

    user_resp = client.post(
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

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "音频上传会",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    upload_resp = client.post(
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


def test_transcribe_latest_audio_generates_transcript(client) -> None:
    """占位语音识别可将最新音频写入转写记录。"""

    user_resp = client.post(
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

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "语音识别会",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    upload_resp = client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("speech.wav", b"RIFF....WAVEfmt", "audio/wav")},
    )
    assert upload_resp.status_code == 201

    transcribe_resp = client.post(f"/api/v1/meetings/{meeting_id}/audio/transcribe")
    assert transcribe_resp.status_code == 201
    transcribe_body = transcribe_resp.json()
    assert transcribe_body["meeting_id"] == meeting_id
    assert transcribe_body["source"] == "mock-asr"
    assert transcribe_body["content"]

    list_resp = client.get(f"/api/v1/transcripts?meeting_id={meeting_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_task_status_transition_and_completed_at(client) -> None:
    """任务状态流转合法时自动维护完成时间。"""

    user_resp = client.post(
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

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "任务状态会",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    task_resp = client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "完成接口联调",
            "assignee_id": organizer_id,
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    start_resp = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"})
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "in_progress"
    assert start_resp.json()["completed_at"] is None

    done_resp = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"})
    assert done_resp.status_code == 200
    assert done_resp.json()["status"] == "done"
    assert done_resp.json()["completed_at"] is not None

    reopen_resp = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "todo"})
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["status"] == "todo"
    assert reopen_resp.json()["completed_at"] is None


def test_task_status_transition_rejects_invalid_flow(client) -> None:
    """非法状态流转应返回 400。"""

    user_resp = client.post(
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

    meeting_resp = client.post(
        "/api/v1/meetings",
        json={
            "title": "非法流转会",
            "organizer_id": organizer_id,
        },
    )
    meeting_id = meeting_resp.json()["id"]

    task_resp = client.post(
        "/api/v1/tasks",
        json={
            "meeting_id": meeting_id,
            "title": "直接完成",
            "assignee_id": organizer_id,
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    invalid_resp = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"})
    assert invalid_resp.status_code == 400
    assert invalid_resp.json()["detail"] == "Invalid task status transition: todo -> done"


def test_list_tasks_can_filter_by_meeting_id(client) -> None:
    """任务列表支持按 meeting_id 过滤。"""

    user_resp = client.post(
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

    meeting_a_resp = client.post(
        "/api/v1/meetings",
        json={"title": "过滤会议A", "organizer_id": organizer_id},
    )
    meeting_b_resp = client.post(
        "/api/v1/meetings",
        json={"title": "过滤会议B", "organizer_id": organizer_id},
    )
    meeting_a_id = meeting_a_resp.json()["id"]
    meeting_b_id = meeting_b_resp.json()["id"]

    client.post(
        "/api/v1/tasks",
        json={"meeting_id": meeting_a_id, "title": "A任务1", "assignee_id": organizer_id},
    )
    client.post(
        "/api/v1/tasks",
        json={"meeting_id": meeting_b_id, "title": "B任务1", "assignee_id": organizer_id},
    )

    filter_resp = client.get(f"/api/v1/tasks?meeting_id={meeting_a_id}")
    assert filter_resp.status_code == 200
    data = filter_resp.json()
    assert len(data) == 1
    assert data[0]["meeting_id"] == meeting_a_id
