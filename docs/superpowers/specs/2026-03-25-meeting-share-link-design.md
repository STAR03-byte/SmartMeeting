# SmartMeeting 会议分享链接设计

**日期**: 2026-03-25  
**状态**: Draft  
**项目**: SmartMeeting  
**基线提交**: `2a89dbc`

## 1. 背景

当前 SmartMeeting 已具备会议创建、音频上传、在线录音、转写、纪要生成、任务提取以及纪要导出能力。现在缺少的是一个更适合“分发”的只读入口：用户可以把会议结果发给别人看，但仍然要求对方先登录系统，避免把会议内容直接暴露为匿名公开页。

本设计聚焦一个最小闭环：**会议详情页生成可复制的分享链接，登录后打开只读分享页**。它与现有导出功能互补：导出适合离线保存与文件传递，分享链接适合在系统内快速阅读与跟进。

## 2. 目标

1. 会议详情页可以一键生成/复用分享链接。
2. 分享链接打开后仍然要求登录，未登录用户会被引导到登录页。
3. 登录后能够自动回到原分享页，而不是丢失目标地址。
4. 分享页只读展示会议摘要、任务、转写概览，不提供写操作。
5. 保持现有会议详情、导出、转写、任务流不被破坏。

## 3. 范围

### In Scope

- 会议详情页新增“生成分享链接 / 复制分享链接”入口
- 后端为会议生成并持久化 `share_token`
- 后端提供只读分享页数据接口
- 前端新增 `/shared/meetings/:token` 只读页面
- 登录守卫支持 `redirect` 回跳，确保登录后继续访问分享页
- 分享页展示摘要、任务、转写概览与空状态

### Out of Scope

- 匿名公开访问
- 邮件、IM、Webhook 等真实分发通道
- token 过期、撤销、轮换 UI
- 评论、协作编辑、二次审批
- PDF/DOCX 作为分享页的渲染内容

## 4. 方案对比

### 方案 A：Opaque Token + 登录守卫 + 只读页（推荐）

生成一个不可猜测的分享 token，前端通过独立分享路由展示只读页面；路由本身受现有登录守卫保护，未登录时先跳登录，再通过 `redirect` 回到分享页。

优点：安全边界清晰、与现有鉴权模型兼容、实现成本低、后续可扩展撤销/过期。  
缺点：需要补登录回跳逻辑。

### 方案 B：直接复制会议详情页链接

最省事，但链接没有“分发语义”，也不能把页面收敛为只读展示。

优点：改动最少。  
缺点：用户体验差，不像真正的分享链接。

### 方案 C：匿名公开分享页

任何拿到链接的人都能访问。

优点：使用门槛最低。  
缺点：安全边界差，不符合当前“登录后访问”的明确要求。

**结论**：采用方案 A。

## 5. 用户故事

### 5.1 会议组织者

- 我希望在会议结束后快速生成分享链接并复制出去。
- 我希望别人打开链接后看到的是整理好的结果，而不是后台管理界面。

### 5.2 团队成员

- 我希望打开链接后能直接看摘要、任务和转写内容。
- 如果我还没登录，我希望登录后自动回到刚才打开的链接。

### 5.3 系统维护者

- 我希望分享功能不引入额外的匿名公开风险。
- 我希望未来如果要撤销分享，只需要清空 token 或重新生成即可。

## 6. 功能设计

### 6.1 分享链接生成

- 在会议详情页增加分享按钮。
- 首次点击时生成 token；如果会议已有 token，则直接复用。
- 仅当会议已生成摘要时允许创建分享链接，避免生成空分享页。
- 返回完整分享 URL，前端直接复制到剪贴板。

### 6.2 登录后继续访问

- 前端路由守卫保持“未登录跳登录”的现有模式。
- 对分享页这类受保护路由，登录页需要保存原始目标地址到 `redirect`。
- 登录成功后，前端优先跳转到 `redirect`，其次再回到首页。
- `redirect` 仅允许站内相对路径：必须以 `/` 开头，且不能以 `//` 开头；否则回退到 `/`。
- 若分享页在已登录状态下请求返回 `401`，前端应按会话失效处理并回到登录页，同时保留当前分享页地址。

### 6.3 分享页展示内容

- 页面采用只读布局，不显示编辑、上传、后处理等按钮。
- 主内容优先展示会议摘要，其次展示任务列表与转写概览。
- 如果某一类内容为空，显示对应空态，不影响整页打开。

### 6.4 安全边界

- token 为 opaque 值，不暴露会议 ID 规律。
- 分享页面与 API 都要求已登录。
- 无效 token 返回 404。
- 没有摘要时创建分享返回 400。
- 分享 token 与登录 token 是两套不同的凭证：分享 token 只负责定位分享内容，登录 token 只负责访问权限。

## 7. 后端设计

### 7.1 数据模型

建议在 `meetings` 表增加：

- `share_token`：`varchar`，nullable，唯一索引
- `shared_at`：`datetime`，nullable

说明：

- 每个会议在 v1 只保留一个 active share token。
- 不引入 token 过期字段；后续如需撤销，可直接清空 token。

### 7.2 API 设计

#### 生成分享链接

- `POST /api/v1/meetings/{id}/share`
- 请求：空体或轻量请求体
- 返回：
  - `meeting_id`
  - `share_token`
  - `share_path`
  - `created_now`
  - `shared_at`

> 说明：`share_url` 不由后端返回；前端用当前 `window.location.origin` + `share_path` 组装完整链接，避免反向代理或部署域名变化带来的歧义。

#### 获取只读分享页数据

- `GET /api/v1/shared/meetings/{token}`

返回一个聚合型只读响应，建议 schema 命名为 `SharedMeetingOut`：

- `meeting`: `MeetingDetailOut`
- `transcripts`: `list[MeetingTranscriptOut]`
- `tasks`: `list[TaskOut]`

其中 `meeting` 继续复用现有会议详情结构即可；如后续希望在普通会议详情中展示分享状态，再单独评估是否补充 `share_token` / `shared_at`。

### 7.3 服务层职责

- `meeting_service.py`
  - 生成/复用 `share_token`
  - 组装分享页响应数据
  - 校验分享所需的会议状态
- `backend/app/api/v1/endpoints/shared_meetings.py`
  - 承载 `GET /api/v1/shared/meetings/{token}`
- `backend/app/api/v1/endpoints/meetings.py`
  - 仅保留“创建分享链接”的会议内操作
- 路由层只做参数校验、鉴权和错误映射，不写重逻辑

### 7.4 错误处理

- 404：会议不存在 / token 无效
- 400：会议尚无摘要，不能生成分享链接
- 401：未登录或登录态失效（由前端跳转登录并保留 redirect）
- 500：其他未预期错误沿用现有结构化响应

## 8. 前端设计

### 8.1 `MeetingDetailView.vue`

- 增加“生成分享链接”按钮。
- 生成成功后自动复制完整链接。
- 若会议没有摘要，按钮置灰并提示先生成纪要。

### 8.2 路由与登录页

- 新增路由：`/shared/meetings/:token`
- 路由守卫在未登录时附加 `redirect`
- `LoginView.vue` 登录成功后优先跳回 `redirect`
- `LoginView.vue` 需要在跳转前校验 `redirect` 是否为站内路径，防止 open redirect

### 8.3 `SharedMeetingView.vue`

- 新增只读页面，使用 `token` 拉取数据。
- 页面结构以阅读为主，不复用后台操作按钮。
- 移动端按单列堆叠展示。

### 8.4 API 封装

- 在 `frontend/src/api/meetings.ts` 增加分享相关 wrapper：
  - `createMeetingShareLink(meetingId)`
  - `getSharedMeeting(token)`
- 在 `frontend/src/api/types.ts` 增加分享返回类型：
  - `MeetingShareCreateResult`
  - `SharedMeetingDetail`
- 分享页数据请求也统一走 `apiClient`。

## 9. 数据流

1. 用户在会议详情页点击“生成分享链接”。
2. 前端请求 `POST /api/v1/meetings/{id}/share`。
3. 后端生成或复用 token，并返回完整链接。
4. 前端复制链接给用户。
5. 受邀用户打开 `/shared/meetings/:token`。
6. 若未登录，先跳登录页并保留 `redirect`。
7. 登录后自动回到分享页。
8. 分享页请求只读数据并渲染摘要、任务、转写概览。

## 10. 测试策略

### 后端

- 分享链接生成成功与幂等性测试
- 无摘要时生成分享链接返回 400
- token 无效返回 404
- 分享页数据接口返回只读内容
- 登录态失效时访问分享页返回 401 的处理路径

### 前端

- API wrapper 的请求路径与返回类型测试
- 登录后 `redirect` 回跳测试
- `redirect` 非法值被忽略的测试
- 分享页加载与空态展示 smoke test
- 会议详情页按钮状态与复制行为测试

## 11. 文件落点

### Backend

- Create: `database/migrations/006_meeting_share_links.sql`
- Create: `database/rollback/rollback_006_to_005.sql`
- Modify: `backend/app/models/meeting.py`
- Modify: `backend/app/schemas/meeting.py`
- Modify: `backend/app/services/meeting_service.py`
- Modify: `backend/app/api/v1/endpoints/meetings.py`
- Create: `backend/app/api/v1/endpoints/shared_meetings.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/tests/test_api.py`

### Frontend

- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/meetings.ts`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/views/MeetingDetailView.vue`
- Create: `frontend/src/views/SharedMeetingView.vue`
- Modify: `frontend/src/views/DashboardView.vue`（仅如需入口跳转时）

### Docs

- Modify: `docs/backend-api.md`
- Modify: `docs/frontend-runbook.md`

## 11. 验收标准

- 登录用户可从会议详情页生成并复制分享链接。
- 未登录用户打开分享链接会被引导登录。
- 登录后会回到原分享页。
- 分享页只读展示，不暴露写操作入口。
- 现有导出、录音、转写、任务功能不回归。
