# SmartMeeting V0.2 协作能力增强 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 SmartMeeting 增加会议分享、会议/任务筛选搜索、以及任务到期提醒展示能力，并保持现有 MVP 接口与前端主流程兼容。

**Architecture:** 以后端增量扩展现有 meetings/tasks 列表接口与服务层为主，新增公开分享只读接口，并在前端现有页面上补最小必要交互。优先复用既有模型、schema、store 和页面结构，不做登录鉴权、通知通道或大范围重构。

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic, pytest, Vue 3, TypeScript, Pinia, Element Plus

---

## 文件结构与职责映射

### Backend

- Modify: `backend/app/api/v1/router.py`
  - 挂载公开分享路由
- Modify: `backend/app/models/meeting.py`
  - 增加 `share_token`、`shared_at`
- Modify: `backend/app/schemas/meeting.py`
  - 增加分享接口返回模型、公开分享页响应模型、会议列表筛选契约支持
- Modify: `backend/app/schemas/task.py`
  - 增加提醒状态字段与任务筛选查询契约所需输出
- Modify: `backend/app/services/meeting_service.py`
  - 会议筛选、分享 token 生成/复用、公开分享聚合查询
- Modify: `backend/app/services/task_service.py`
  - 任务筛选与提醒状态计算
- Modify: `backend/app/api/v1/endpoints/meetings.py`
  - 会议列表筛选参数、分享接口、公开分享接口
- Modify: `backend/app/api/v1/endpoints/tasks.py`
  - 任务筛选参数扩展
- Test: `backend/tests/test_api.py`
  - 分享、筛选、提醒状态的回归测试

### Frontend

- Modify: `frontend/src/api/meetings.ts`
  - 增加会议列表筛选、分享接口、公开分享接口
- Modify: `frontend/src/api/tasks.ts`
  - 增加状态/优先级/关键词等筛选参数
- Modify: `frontend/src/api/types.ts`
  - 增加 share / public meeting / reminder tag 相关类型
- Modify: `frontend/src/stores/meetingStore.ts`
  - 接入会议筛选与分享行为（仅在确有必要时修改，避免膨胀）
- Modify: `frontend/src/views/DashboardView.vue`
  - 增加会议搜索/状态筛选与空态
- Modify: `frontend/src/views/TasksView.vue`
  - 增加筛选栏与提醒状态展示
- Modify: `frontend/src/views/MeetingDetailView.vue`
  - 增加分享操作
- Create: `frontend/src/views/SharedMeetingView.vue`
  - 新增公开只读分享页
- Modify: `frontend/src/router/index.ts`
  - 注册 `/share/:token` 路由

### Docs

- Modify: `docs/backend-api.md`
  - 更新分享接口与筛选参数说明
- Modify: `docs/frontend-runbook.md`
  - 补充分享页与筛选验证步骤

### Database

- Create: `database/migrations/006_collaboration_share_fields.sql`
  - 为 `meetings` 增加 `share_token`、`shared_at`，并建立唯一索引
- Create: `database/rollback/rollback_006_to_005.sql`
  - 回滚分享字段相关变更

---

## Chunk 1: Backend 数据模型与 Schema

### Task 1: 先补数据库迁移与回滚脚本

**Files:**
- Create: `database/migrations/006_collaboration_share_fields.sql`
- Create: `database/rollback/rollback_006_to_005.sql`

- [ ] **Step 1: 写迁移脚本**

在 `006_collaboration_share_fields.sql` 中完成：
- 为 `meetings` 增加 `share_token` nullable 列
- 为 `meetings` 增加 `shared_at` nullable 列
- 为 `share_token` 创建唯一索引

- [ ] **Step 2: 写回滚脚本**

在 `rollback_006_to_005.sql` 中完成：
- 删除分享唯一索引
- 删除 `share_token`
- 删除 `shared_at`

- [ ] **Step 3: 验证脚本语义与命名**

核对与现有 `database/migrations/005_audit_and_participants.sql`、`database/rollback/rollback_005_to_004.sql` 风格一致。

- [ ] **Step 4: 如本地有 MySQL 环境，先执行一次迁移语法验证**

Run: `mysql -u <user> -p <database> < database/migrations/006_collaboration_share_fields.sql`
Expected: 执行成功，`meetings` 表新增 `share_token`、`shared_at`

- [ ] **Step 5: Commit**

```bash
git add database/migrations/006_collaboration_share_fields.sql database/rollback/rollback_006_to_005.sql
git commit -m "feat(database): add meeting share migration"
```

### Task 2: 以纵向切片完成会议分享后端主链路

**Files:**
- Create or Modify: `backend/app/api/v1/endpoints/share.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/app/models/meeting.py`
- Modify: `backend/app/services/meeting_service.py`
- Modify: `backend/app/api/v1/endpoints/meetings.py`
- Modify: `backend/app/schemas/meeting.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: 写精确失败测试**

在 `backend/tests/test_api.py` 增加至少这 4 个测试：
- `test_create_meeting_share_is_idempotent`
- `test_create_meeting_share_returns_404_for_missing_meeting`
- `test_get_public_share_returns_read_only_payload`
- `test_get_public_share_returns_404_for_invalid_token`

- [ ] **Step 2: 运行单测确认失败**

Run: `pytest backend/tests/test_api.py::test_create_meeting_share_is_idempotent -v`
Expected: FAIL，因为分享接口尚不存在。

- [ ] **Step 3: 增加 model 和 schema 支撑**

添加：
- `share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)`
- `shared_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)`

并在 `backend/app/schemas/meeting.py` 增加：
- `MeetingShareOut`
- `PublicMeetingDetailOut`

保持其余字段与命名风格不变。

- [ ] **Step 4: 实现 service 与两个 endpoint**

在 `backend/app/services/meeting_service.py` 实现：
- `create_or_get_meeting_share(...)`
- `get_public_shared_meeting(...)`

在路由层实现：
- `POST /api/v1/meetings/{id}/share`
- `GET /api/v1/share/{token}`

若 `meetings.py` 不适合承载无前缀公开接口，则新增 `backend/app/api/v1/endpoints/share.py`，并在 `backend/app/api/v1/router.py` 挂载。

- [ ] **Step 5: 运行精确测试直到转绿**

Run:
- `pytest backend/tests/test_api.py::test_create_meeting_share_is_idempotent -v`
- `pytest backend/tests/test_api.py::test_get_public_share_returns_read_only_payload -v`

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/meeting.py backend/app/schemas/meeting.py backend/app/services/meeting_service.py backend/app/api/v1/endpoints/meetings.py backend/app/api/v1/router.py backend/tests/test_api.py
git commit -m "feat(meeting): add share endpoints"
```

若创建了 `backend/app/api/v1/endpoints/share.py`，一并加入 commit。

### Task 3: 扩展 Task schema 输出契约

**Files:**
- Modify: `backend/app/schemas/task.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: 写失败测试，约束任务提醒字段**

在测试中断言任务列表返回：
- `is_overdue`
- `is_due_soon`

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_api.py -k due -v`
Expected: FAIL，schema 未覆盖这些字段。

- [ ] **Step 3: 扩展 task schema**

在 `backend/app/schemas/task.py`：
- 为 `TaskOut` 增加 `is_overdue: bool = False`
- 为 `TaskOut` 增加 `is_due_soon: bool = False`

不要引入 `Any` 或模糊字典。

- [ ] **Step 4: 运行测试验证 schema 通过解析**

Run: `pytest backend/tests/test_api.py -k due -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/task.py backend/tests/test_api.py
git commit -m "feat(task): add reminder response fields"
```

---

## Chunk 2: Backend 服务层与接口

### Task 4: 扩展会议列表筛选服务与 API

**Files:**
- Modify: `backend/app/services/meeting_service.py`
- Modify: `backend/app/api/v1/endpoints/meetings.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: 写精确失败测试覆盖会议筛选**

新增测试：
- 按 `status` 筛选会议
- 按 `keyword` 匹配会议标题
- 多条件组合使用 AND 逻辑
- 无结果返回 `200 + []`
- 非法 `status` 返回 `422`

建议测试函数名：
- `test_list_meetings_filters_by_status_and_keyword`
- `test_list_meetings_invalid_status_returns_422`

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_api.py::test_list_meetings_filters_by_status_and_keyword -v`

- [ ] **Step 3: 在服务层增加筛选参数**

更新 `list_meetings(...)`：
- 增加 `keyword: str | None`
- `keyword` 对标题做 `LIKE` / `ilike` 匹配
- 保持原有 `status`, `organizer_id`, `limit`, `offset` 行为兼容

- [ ] **Step 4: 在 `meetings.py` 暴露 typed query 参数**

为 `GET /api/v1/meetings` 增加 `keyword` query 参数，并确保 `status` 使用现有允许值约束，而不是自由字符串，以支持非法值 `422`。

- [ ] **Step 5: 运行定向测试**

Run:
- `pytest backend/tests/test_api.py::test_list_meetings_filters_by_status_and_keyword -v`
- `pytest backend/tests/test_api.py::test_list_meetings_invalid_status_returns_422 -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/meeting_service.py backend/app/api/v1/endpoints/meetings.py backend/tests/test_api.py
git commit -m "feat(meeting): add meeting search filters"
```

### Task 5: 扩展任务筛选与提醒状态计算

**Files:**
- Modify: `backend/app/services/task_service.py`
- Modify: `backend/app/api/v1/endpoints/tasks.py`
- Modify: `backend/app/schemas/task.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: 写精确失败测试覆盖任务筛选和提醒**

测试点：
- `status`, `priority`, `meeting_id`, `keyword`, `assignee_id` 可组合筛选
- `due_at < now` 的未完成任务返回 `is_overdue = true`
- `now <= due_at < now + 48h` 的未完成任务返回 `is_due_soon = true`
- 已完成任务不打提醒
- `due_at is null` 不打提醒
- 非法 `status` / `priority` 返回 `422`

- 建议测试函数名：
- `test_list_tasks_filters_and_sets_reminder_flags`
- `test_invalid_task_filter_returns_422`

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_api.py::test_list_tasks_filters_and_sets_reminder_flags -v`

- [ ] **Step 3: 在 `task_service.py` 扩展列表函数**

更新 `list_tasks(...)`：
- 增加 `status`, `priority`, `keyword`
- 保留 `assignee_id`, `meeting_id`
- 以 AND 逻辑组合过滤
- `keyword` 仅匹配 `Task` 自身字段（如 `title`, `description`），不联查会议标题
- 在输出前为每条任务计算提醒字段

建议提炼纯函数：
- `build_task_reminder_flags(task, now_utc) -> tuple[bool, bool]`

提醒计算统一按 UTC 进行，避免本地时区漂移。

- [ ] **Step 4: 在 `tasks.py` 暴露 typed query 参数**

为 `GET /api/v1/tasks` 增加：
- `status`
- `priority`
- `keyword`

并确保非法值走 `422`，而不是静默忽略。

- [ ] **Step 5: 运行测试转绿**

Run:
- `pytest backend/tests/test_api.py::test_list_tasks_filters_and_sets_reminder_flags -v`
- `pytest backend/tests/test_api.py::test_invalid_task_filter_returns_422 -v`

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/task_service.py backend/app/api/v1/endpoints/tasks.py backend/app/schemas/task.py backend/tests/test_api.py
git commit -m "feat(task): add filters and reminder flags"
```

---

## Chunk 3: Frontend API 与页面

### Task 6: 扩展前端 API 类型与请求函数

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/meetings.ts`
- Modify: `frontend/src/api/tasks.ts`

- [ ] **Step 1: 先更新类型定义**

在 `types.ts` 增加：
- 会议分享返回类型
- 公开分享页类型
- 任务提醒标记字段

- [ ] **Step 2: 扩展 meetings API**

在 `meetings.ts` 增加：
- `getMeetings(params)`，支持 `keyword`, `status`
- `createMeetingShare(meetingId)`
- `getSharedMeeting(token)`

保持现有 `getMeetings()` 调用方可平滑升级。

- [ ] **Step 3: 扩展 tasks API**

在 `tasks.ts` 增加：
- `status`, `priority`, `keyword` 参数
- 保持现有 `assigneeId`, `meetingId` 兼容

- [ ] **Step 4: 运行前端类型检查**

Run: `npm --prefix frontend run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/types.ts frontend/src/api/meetings.ts frontend/src/api/tasks.ts
git commit -m "feat(frontend-api): add share and filter clients"
```

### Task 7: 为 Dashboard 增加会议搜索与状态筛选

**Files:**
- Modify: `frontend/src/views/DashboardView.vue`
- Modify: `frontend/src/stores/meetingStore.ts`（仅当需要 store 持有过滤状态时）

- [ ] **Step 1: 增加筛选栏骨架 UI**

先实现最小 UI 骨架：
- 搜索框
- 状态筛选下拉
- 空结果提示

- [ ] **Step 2: 绑定本地筛选状态**

使用本地 `ref`/`reactive` 管理关键词和状态，而不是先改 store 为重量状态机。

- [ ] **Step 3: 接入 API 请求参数**

筛选变化时重新请求会议列表，而不是在前端对已加载列表做复杂二次过滤。

- [ ] **Step 4: 保持现有会议卡片布局不变**

只在头部插入筛选栏，避免重写列表视觉结构。

- [ ] **Step 5: 运行类型检查与构建**

Run:
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`

- [ ] **Step 6: 执行手动 QA**

手动检查：
- 输入关键词后会议列表变化
- 切换状态后会议列表变化
- 无结果时出现空态

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/DashboardView.vue frontend/src/stores/meetingStore.ts
git commit -m "feat(dashboard): add meeting search and status filters"
```

### Task 8: 为 Tasks 页面增加筛选栏与提醒标签

**Files:**
- Modify: `frontend/src/views/TasksView.vue`

- [ ] **Step 1: 增加筛选栏 UI**

加入：
- 状态下拉
- 优先级下拉
- 关键词输入框
- 会议筛选（可先用 meeting id，若已有会议列表可显示标题映射）

- [ ] **Step 2: 绑定筛选状态并接入 API**

筛选变化时重新调用 `getTasks(params)`，不要在全量列表上做复杂前端二次筛选。

- [ ] **Step 3: 渲染提醒标签**

在任务表新增一列：
- `已逾期`
- `即将到期`
- 或空

- [ ] **Step 4: 保留现有状态变更交互**

不要把状态修改与筛选状态混在一起；更新任务状态失败时仍按原逻辑 refresh。

- [ ] **Step 5: 运行类型检查与构建**

Run:
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`

- [ ] **Step 6: 执行手动 QA**

手动检查：
- 多条件筛选组合生效
- 已完成任务不显示提醒
- 逾期 / 即将到期标签展示正确

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/TasksView.vue
git commit -m "feat(tasks): add filters and reminder indicators"
```

### Task 9: 为会议详情页增加分享操作

**Files:**
- Modify: `frontend/src/views/MeetingDetailView.vue`

- [ ] **Step 1: 增加分享按钮和结果提示位**

按钮文案建议：
- `生成分享链接`
- 若已生成，也可以统一为 `复制分享链接`

- [ ] **Step 2: 接入分享 API**

调用 `createMeetingShare(meetingId)`，前端用 `window.location.origin + share_path` 组成完整 URL。

- [ ] **Step 3: 复制到剪贴板并做错误处理**

优先使用 Clipboard API；失败时至少把链接展示给用户手动复制。

- [ ] **Step 4: 运行类型检查与构建**

Run:
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`

- [ ] **Step 5: 执行手动 QA**

手动检查：
- 首次点击可生成链接
- 再次点击仍可复制稳定链接
- Clipboard 失败时有可见降级提示

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/MeetingDetailView.vue
git commit -m "feat(meeting-detail): add share action"
```

### Task 10: 新增公开分享页与路由

**Files:**
- Create: `frontend/src/views/SharedMeetingView.vue`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 创建分享页组件骨架**

页面需展示：
- 会议标题 / 描述
- 摘要
- 转写记录列表
- 任务列表与提醒状态

风格应偏只读阅读页，不复用后台操作按钮。

- [ ] **Step 2: 注册 `/share/:token` 路由**

在 `router/index.ts` 增加懒加载路由。

- [ ] **Step 3: 接入公开分享 API**

在页面 mounted 时读取 token 并请求 `getSharedMeeting(token)`。

- [ ] **Step 4: 处理异常与空态**

无效 token 显示清晰错误信息，而不是白屏。

- [ ] **Step 5: 运行类型检查与构建**

Run:
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`

- [ ] **Step 6: 执行手动 QA**

手动检查：
- 有效 token 可渲染只读页
- 无效 token 显示错误态
- 页面无上传/后处理/编辑按钮

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/SharedMeetingView.vue frontend/src/router/index.ts
git commit -m "feat(share): add public shared meeting page"
```

---

## Chunk 4: 文档、回归与手动验证

### Task 11: 更新文档

**Files:**
- Modify: `docs/backend-api.md`
- Modify: `docs/frontend-runbook.md`

- [ ] **Step 1: 更新 backend API 文档**

补充：
- `GET /api/v1/meetings` 的 `keyword` / `status`
- `POST /api/v1/meetings/{id}/share`
- `GET /api/v1/share/{token}`
- `GET /api/v1/tasks` 的新增筛选参数与提醒字段

- [ ] **Step 2: 更新 frontend runbook**

补充：
- 如何在会议详情页生成分享链接
- 如何访问分享页
- 如何验证 Dashboard / Tasks 筛选

- [ ] **Step 3: Commit**

```bash
git add docs/backend-api.md docs/frontend-runbook.md
git commit -m "docs: update collaboration feature runbook"
```

### Task 12: 后端回归验证

**Files:**
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: 运行后端全量测试**

Run: `pytest backend/tests -v`
Expected: PASS

- [ ] **Step 2: 运行迁移脚本验证（如有 MySQL 环境）**

Run: `mysql -u <user> -p <database> < database/migrations/006_collaboration_share_fields.sql`
Expected: 执行成功，`meetings` 表新增 `share_token`、`shared_at`

- [ ] **Step 3: 如失败，仅修复本计划引入问题**

不要顺手重构无关模块。

- [ ] **Step 4: 重新运行全量测试直到通过**

Run: `pytest backend/tests -v`

### Task 13: 前端验证

**Files:**
- Modify if needed: `frontend/src/**`

- [ ] **Step 1: 运行前端类型检查**

Run: `npm --prefix frontend run typecheck`
Expected: PASS

- [ ] **Step 2: 运行前端构建**

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] **Step 3: 若有浏览器验证条件，做手动 QA**

手动验证清单：
- Dashboard 关键词 / 状态筛选可用
- Tasks 多条件筛选可用
- MeetingDetail 可复制分享链接
- `/share/:token` 可读且无编辑按钮
- 逾期 / 即将到期标签显示正确

- [ ] **Step 4: 记录验证证据**

在最终汇报中列出执行命令和观察到的结果。

---

## Plan Notes

- 实施时严格遵守现有代码约定：route 层轻量，业务逻辑进入 `services/`
- 不得引入 `as any`、`@ts-ignore`、`@ts-expect-error`
- 不得把筛选逻辑主要放在前端本地数组处理上；以后端查询参数为主
- 不得把公开分享页做成可编辑后台页
- 当前仓库 `frontend/package.json` 没有测试脚本，本计划的前端部分采用 contract-first + `typecheck` + `build` + 手动 QA，不宣称前端 TDD
- 若后端测试夹带 pre-existing failure，必须明确区分“本次引入”与“仓库原有”

---

Plan complete and saved to `docs/superpowers/plans/2026-03-17-v0-2-collaboration-implementation.md`. Ready to execute?
