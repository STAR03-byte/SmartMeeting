"""后端核心接口测试。"""

from app.services.llm_service import LLMServiceError


def test_health_check(auth_client) -> None:
    """健康检查接口可用。"""

    response = auth_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
    assert len(list_resp.json()) == 1


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
    data = filter_resp.json()
    assert len(data) == 1
    assert data[0]["meeting_id"] == meeting_a_id


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
    data = filtered_resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "紧急修复线上接口"
    assert data[0]["is_overdue"] is True
    assert data[0]["is_due_soon"] is False

    status_resp = auth_client.get(f"/api/v1/tasks?meeting_id={meeting_id}&status=in_progress")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert len(status_data) == 1
    assert status_data[0]["title"] == "整理发布说明文档"
    assert status_data[0]["is_overdue"] is False
    assert status_data[0]["is_due_soon"] is False

    done_list_resp = auth_client.get(f"/api/v1/tasks?meeting_id={meeting_id}&status=done")
    assert done_list_resp.status_code == 200
    done_data = done_list_resp.json()
    assert len(done_data) == 1
    assert done_data[0]["title"] == "历史归档任务"
    assert done_data[0]["is_overdue"] is False
    assert done_data[0]["is_due_soon"] is False


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
    organizer_data = organizer_filter_resp.json()
    assert len(organizer_data) == 2
    assert [item["id"] for item in organizer_data] == [meeting_c_id, meeting_a_id]

    status_filter_resp = auth_client.get("/api/v1/meetings?status=ongoing")
    assert status_filter_resp.status_code == 200
    status_data = status_filter_resp.json()
    assert len(status_data) == 1
    assert status_data[0]["id"] == meeting_a_id

    limit_offset_resp = auth_client.get("/api/v1/meetings?limit=1&offset=1")
    assert limit_offset_resp.status_code == 200
    limit_offset_data = limit_offset_resp.json()
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
