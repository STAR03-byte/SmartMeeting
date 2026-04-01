# SmartMeeting Backend API 文档

## 1. 基础信息

- Base URL: `http://127.0.0.1:8000`
- API 前缀: `/api/v1`
- 健康检查: `GET /health`

## 2. 会议相关接口

### 2.1 查询会议列表

- `GET /api/v1/meetings`
- 返回: `MeetingListOut`

Query 参数：

- `status?: planned | ongoing | done | cancelled`
- `organizer_id?: int`
- `keyword?: string`（标题/描述关键词）
- `sort_by?: string`
  - `id_desc`（默认）
  - `scheduled_start_at_asc`
  - `scheduled_start_at_desc`
- `limit?: int`（1..100）
- `offset?: int`（>=0，默认 0）

响应示例：

```json
{
  "items": [
    {
      "id": 1,
      "title": "Weekly Sync",
      "description": "...",
      "status": "planned",
      "organizer_id": 1,
      "scheduled_start_at": "2026-03-31T10:00:00",
      "scheduled_end_at": "2026-03-31T10:30:00",
      "actual_start_at": null,
      "actual_end_at": null,
      "summary": null,
      "postprocessed_at": null,
      "postprocess_version": null,
      "created_at": "2026-03-31T09:50:00",
      "updated_at": "2026-03-31T09:50:00"
    }
  ],
  "total": 1
}
```

### 2.2 查询会议详情

- `GET /api/v1/meetings/{meeting_id}`
- 返回字段包含:
  - `summary`
  - `postprocessed_at`
  - `postprocess_version`

### 2.3 上传会议音频

- `POST /api/v1/meetings/{meeting_id}/audio`
- Content-Type: `multipart/form-data`
- 表单字段:
  - `file`: 音频文件
- 成功返回 `201`，响应示例:

```json
{
  "id": 1,
  "meeting_id": 10,
  "filename": "demo.wav",
  "storage_path": "backend/storage/audio/10/xxxx.wav",
  "content_type": "audio/wav",
  "size_bytes": 102400,
  "uploaded_at": "2026-03-12T11:00:00"
}
```

### 2.4 转写最新音频（Whisper ASR）

- `POST /api/v1/meetings/{meeting_id}/audio/transcribe`
- 逻辑: 对该会议最新上传音频执行 Whisper 转写，生成多条 `meeting_transcripts` 记录
- 返回: `MeetingTranscriptOut`
- 成功返回 `201`，失败场景:
  - 会议不存在: `404 Meeting not found`
  - 无音频: `400 No audio found for meeting`

### 2.5 会议后处理（摘要+任务抽取）

- `POST /api/v1/meetings/{meeting_id}/postprocess`
- Query:
  - `force_regenerate`（可选，默认 `false`）
- 行为:
  - 优先使用 LLM 从转写中生成摘要并落库到会议
  - 优先使用 LLM 抽取任务，失败时回退到规则抽取
  - 默认幂等；`force_regenerate=true` 时重建任务

### 2.6 会议分享链接

- `POST /api/v1/meetings/{meeting_id}/share`
- 作用: 生成或复用会议分享链接
- 访问要求: 已登录且必须是会议组织者；非组织者返回 `403`
- 前置条件: 会议必须已有 `summary`
- 成功返回:

```json
{
  "meeting_id": 10,
  "share_token": "...",
  "share_path": "/shared/meetings/...",
  "created_now": true,
  "shared_at": "2026-03-25T00:00:00Z"
}
```

- `GET /api/v1/shared/meetings/{share_token}`
- 作用: 获取只读分享页数据
- 返回:
  - `meeting`
  - `transcripts`
  - `tasks`
- 访问要求: 公开访问（无需登录）
- 无效 `share_token` 返回 `404 Shared meeting not found`

## 3. 用户接口

### 3.1 查询用户列表

- `GET /api/v1/users`
- 返回：`UserOut[]`

### 3.2 查询用户详情

- `GET /api/v1/users/{user_id}`
- 资源不存在返回 `404 User not found`

### 3.3 创建用户

- `POST /api/v1/users`
- 返回：`UserOut`

### 3.4 更新用户

- `PATCH /api/v1/users/{user_id}`
- 返回：`UserOut`

### 3.5 删除用户

- `DELETE /api/v1/users/{user_id}`
- 成功返回 `204`

## 4. 参与人接口

### 4.1 查询参与人列表

- `GET /api/v1/participants`
- Query:
  - `meeting_id?: int`
- 返回：`MeetingParticipantOut[]`

### 4.2 查询参与人详情

- `GET /api/v1/participants/{participant_id}`
- 资源不存在返回 `404 Participant not found`

### 4.3 创建参与人

- `POST /api/v1/participants`
- 前置校验：`meeting_id`、`user_id` 必须存在
- 返回：`MeetingParticipantOut`

### 4.4 更新参与人

- `PATCH /api/v1/participants/{participant_id}`
- 返回：`MeetingParticipantOut`

### 4.5 删除参与人

- `DELETE /api/v1/participants/{participant_id}`
- 成功返回 `204`

## 5. 转写接口

### 5.1 查询转写列表

- `GET /api/v1/transcripts`
- Query:
  - `meeting_id?: int`
- 返回：`MeetingTranscriptOut[]`

### 5.2 查询转写详情

- `GET /api/v1/transcripts/{transcript_id}`
- 资源不存在返回 `404 Transcript not found`

### 5.3 创建转写

- `POST /api/v1/transcripts`
- 前置校验：`meeting_id` 必须存在
- 返回：`MeetingTranscriptOut`

### 5.4 更新转写

- `PATCH /api/v1/transcripts/{transcript_id}`
- 返回：`MeetingTranscriptOut`

### 5.5 删除转写

- `DELETE /api/v1/transcripts/{transcript_id}`
- 成功返回 `204`

## 6. 任务接口

### 3.1 查询任务列表

- `GET /api/v1/tasks`

返回：`TaskListOut`（`{ items, total }`）

Query 参数：

- 过滤（可选）：
  - `assignee_id?: int`
  - `meeting_id?: int`
  - `status?: TaskStatus`（`todo | in_progress | done`）
  - `priority?: TaskPriority`（`high | medium | low`）
  - `keyword?: string`（任务标题模糊匹配，trim 后为空则忽略）
- 分页（可选）：
  - `limit?: int`（1..100）
  - `offset?: int`（>=0，默认 0）
- 排序（可选）：
  - `sort_by?: string`
    - `id_desc`（默认，按创建顺序近似：`id desc`）
    - `due_at_asc`（截止时间近→远，`null` 排最后）
    - `due_at_desc`（截止时间远→近，`null` 排最后）

响应示例：

```json
{
  "items": [
    {
      "id": 1,
      "meeting_id": 10,
      "transcript_id": null,
      "title": "补齐接口文档",
      "description": "补齐接口文档",
      "assignee_id": 1,
      "reporter_id": null,
      "priority": "medium",
      "status": "todo",
      "progress_note": null,
      "due_at": "2026-03-31T10:00:00Z",
      "completed_at": null,
      "is_overdue": false,
      "is_due_soon": false,
      "created_at": "2026-03-31T09:50:00Z",
      "updated_at": "2026-03-31T09:50:00Z"
    }
  ],
  "total": 123
}
```

### 3.2 更新任务状态

- `PATCH /api/v1/tasks/{task_id}`
- 状态机规则:
  - `todo -> in_progress`
  - `in_progress -> done | todo`
  - `done -> todo`
- 非法流转返回 `400`:

```json
{
  "detail": "Invalid task status transition: todo -> done"
}
```

- `completed_at` 自动维护:
  - 切到 `done` 自动写入时间
  - 从 `done` 回退自动清空

## 7. 错误码约定

### 4.1 统一错误响应结构

后端所有错误响应统一返回 JSON：

```json
{
  "detail": "...",
  "error_code": "..."
}
```

- `detail`：可读错误信息；对 `422` 请求参数校验失败时为错误数组（来自 FastAPI `RequestValidationError`）。
- `error_code`：稳定的机器可读错误码（便于前端按类处理）。

### 4.2 通用 error_code 映射

| HTTP status | error_code |
|---:|---|
| 400 | `BAD_REQUEST` |
| 401 | `UNAUTHORIZED` |
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 409 | `CONFLICT` |
| 422 | `REQUEST_VALIDATION_ERROR` |
| 429 | `TOO_MANY_REQUESTS` |
| other 4xx | `CLIENT_ERROR` |

- `400`: 业务前置条件不满足（无音频、无转写、非法状态流转）
- `500`: AI 服务不可用且无可恢复降级路径
- `404`: 资源不存在（meeting/task/transcript/user/share token）
- `401`: 登录态失效或未登录（鉴权接口/分享页读取）
- `422`: 请求参数校验失败

## 8. 当前 AI 能力说明

- ASR: 本地 `Whisper`
- 摘要: 优先 LLM 生成，失败时回退规则摘要（取前两段有效转写）
- 任务抽取: 优先 LLM 抽取，失败时回退关键词和句式规则
- 版本标记: `postprocess_version` 根据实际链路写入 `llm-summary-v1` / `llm-task-v1` / `rule-fallback-v1`
