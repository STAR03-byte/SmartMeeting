# SmartMeeting 任务细粒度权限设计

> **Goal:** 在现有“组织者看全量、普通成员只看自己任务”的基础上，进一步把“能看到任务”和“能对任务做什么”拆开，确保负责人只能推进执行，组织者才拥有任务定义与删除权限。

**Architecture:** 任务权限分成两层：第一层是 **visibility**（谁能看到任务）；第二层是 **capability**（谁能执行哪类操作）。后端在任务查询响应中返回细粒度能力字段，前端据此决定显示哪些按钮；同时后端接口本身也做同样的能力校验，防止仅靠前端禁用控件造成越权。

**Tech Stack:** FastAPI endpoint 权限校验、`task_service.py` 任务序列化、Vue 3 + Pinia 条件渲染、现有 `/api/v1/tasks` REST 接口。

---

## 1. Background

当前系统已经完成第一步权限收紧：

- `admin` / 会议组织者可以看到该会议全部任务；
- 普通成员只能看到自己被指派的任务；
- 前端通过 `can_manage` 控制编辑按钮和状态切换。

这一步解决了“谁能看到任务”的问题，但“看到之后能做什么”仍然过粗。现在负责人一旦能管理任务，就默认能修改标题、描述、负责人、截止时间，甚至删除任务。这和实际协作场景不一致：负责人更像执行者，应该推进状态和反馈进展，而任务定义、改派和删除应由会议组织者控制。

因此，这次设计的重点不是再改可见范围，而是把任务操作拆成更细的权限层。

## 2. Goals

1. 保持当前任务可见范围不变：组织者全量可见，负责人只见自己的任务。
2. 让负责人只能处理“执行态”字段，不再修改任务定义字段。
3. 让组织者 / admin 保留完整任务管理权，包括改派和删除。
4. 前端按钮与后端权限一致，避免出现“按钮可点但请求 403”的体验。
5. 权限命名清晰，后续如果继续扩展（例如评论、附件、审批）可以沿用同一模式。

## 3. Non-goals

- 不改动会议可见性规则。
- 不引入新的 RBAC 表或数据库权限模型。
- 不新增独立的任务审批流。
- 不重构整套任务页面，只做和权限直接相关的接口与 UI 收口。

## 4. Candidate approaches

### Approach A: Two-level split (Recommended)

把任务能力拆成两类：

- **执行权限**：负责人可改 `status`、`progress_note`
- **定义权限**：组织者 / admin 可改 `title`、`description`、`assignee_id`、`priority`、`due_at`、`reminder_at`，并可删除

**Pros**

- 和当前协作角色最匹配：负责人负责推进，组织者负责定义。
- 改动范围适中，能直接套进现有 API/UI。
- 对用户来说最容易理解。

**Cons**

- 负责人如果发现截止时间明显不合理，仍需找组织者修改。

### Approach B: 执行权限放宽到时间字段

负责人可改 `status`、`progress_note`、`due_at`、`reminder_at`；组织者 / admin 仍保留其它字段和删除。

**Pros**

- 执行层更灵活，负责人可以快速延后提醒或截止时间。

**Cons**

- 时间字段本质上仍属于任务定义的一部分，容易引起“谁在重新定义任务”的责任混淆。

### Approach C: 单接口 + 后端动态白名单过滤

保留一个 `PATCH /tasks/{id}`，后端根据角色把不允许的字段从 payload 中剔除。

**Pros**

- 表面上改动最少。

**Cons**

- 行为不透明：用户提交了字段，但后端静默忽略，很难理解为什么没生效。
- 测试和调试都更困难。

**Decision:** 采用 Approach A。

## 5. Final design

### 5.1 权限模型

权限分为 4 个显式能力字段：

- `can_update_status`
- `can_edit_progress_note`
- `can_edit_core_fields`
- `can_delete`

其中：

- `admin` / 会议组织者：4 个能力均为 `true`
- 任务负责人：
  - `can_update_status = true`
  - `can_edit_progress_note = true`
  - `can_edit_core_fields = false`
  - `can_delete = false`
- 其他成员：全部为 `false`

这里把 `progress_note` 和 `status` 放在一起，是因为它们都属于执行反馈，而不改变任务定义本身。

### 5.2 后端接口策略

现有统一的 `PATCH /api/v1/tasks/{task_id}` 不再适合承载所有更新行为，需要按语义拆分：

#### Option 1（推荐实现方式）

保留现有 `PATCH /api/v1/tasks/{task_id}`，但在后端显式区分两类更新：

- 如果 payload 只包含 `status`、`progress_note`：允许负责人或组织者提交
- 如果 payload 包含核心字段（`title`、`description`、`assignee_id`、`priority`、`due_at`、`reminder_at`、`reporter_id`、`transcript_id`）：仅允许组织者 / admin

这样可以避免前端接口大改，同时让规则在 endpoint 层清晰可控。

#### Option 2（备选，不推荐优先做）

拆成两个接口：

- `PATCH /tasks/{id}/execution`
- `PATCH /tasks/{id}`

可读性更强，但会扩大前端和测试改动面。

**Decision:** 先用 Option 1，在单接口内做显式字段级校验。

### 5.3 后端校验规则

在 `backend/app/api/v1/endpoints/tasks.py` 增加 3 类判断函数：

1. **查看权限**：沿用现有逻辑
2. **执行态更新权限**：负责人 / 组织者 / admin 可用
3. **核心字段编辑权限**：仅组织者 / admin 可用
4. **删除权限**：仅组织者 / admin 可用

推荐增加辅助函数（命名示意）：

- `_can_update_task_execution(...)`
- `_can_edit_task_core_fields(...)`
- `_assert_task_delete_permission(...)`
- `_classify_task_update_payload(...)`

其中 `_classify_task_update_payload(...)` 负责判断这次 PATCH 属于：

- `execution_only`
- `core_edit`
- `mixed`

如果是 `mixed`，也按更严格的 `core_edit` 走。

### 5.4 响应结构调整

当前 `TaskOut` 只有一个 `can_manage`，需要替换或扩展为更细粒度字段。推荐直接改成：

- `can_update_status: bool`
- `can_edit_progress_note: bool`
- `can_edit_core_fields: bool`
- `can_delete: bool`

`can_manage` 可以删除，避免语义重复；如果担心前端一次性改动过大，也可以短期保留，但不再作为新逻辑依据。

### 5.5 前端交互策略

#### 任务中心 `TasksView.vue`

- 状态下拉：只在 `can_update_status` 为真时可用
- “编辑”按钮：只在 `can_edit_core_fields` 为真时显示/启用
- 新增“进度备注”快捷编辑入口：只在 `can_edit_progress_note` 为真时显示
- 删除按钮：只在 `can_delete` 为真时显示

#### 会议详情 `TaskManager.vue`

- 状态切换：使用 `can_update_status`
- 编辑按钮：使用 `can_edit_core_fields`
- 删除按钮：使用 `can_delete`
- 新建任务入口：继续只给组织者 / admin

#### 表单层

如果保留统一编辑弹窗，则需要按权限裁剪字段：

- 负责人进入时，只显示 `status`、`progress_note`
- 组织者进入时，显示完整表单

这样比“字段显示了但提交被拒绝”更自然。

### 5.6 文案与用户理解

为了避免用户误解，建议增加轻量提示：

- 任务中心副文案可提示“这里只显示你负责的任务”
- 负责人编辑区域可写“你可以更新状态与进展说明”
- 删除操作需二次确认，文案明确说明“删除后不可恢复”

## 6. Acceptance criteria

1. 负责人只能修改 `status` 与 `progress_note`。
2. 负责人尝试修改负责人、优先级、标题、截止时间等核心字段时，后端返回 403。
3. 组织者 / admin 可修改全部字段并删除任务。
4. 前端不会向负责人展示超出权限的核心编辑入口或删除按钮。
5. 任务中心与会议详情页行为一致。

## 7. Verification plan

### Backend

新增或更新这些测试场景：

- 负责人可修改 `status`
- 负责人可修改 `progress_note`
- 负责人修改 `title` / `assignee_id` / `priority` / `due_at` / `reminder_at` 时返回 403
- 组织者可修改全部字段
- 负责人删除任务返回 403
- 组织者删除任务成功

### Frontend

新增或更新这些测试场景：

- `TaskItem` 能力字段序列化测试
- 任务中心根据能力字段禁用/隐藏控件
- 会议详情任务区根据能力字段禁用/隐藏控件

### Manual QA

1. 以组织者身份进入会议详情，确认可新建/编辑/改派/删除。
2. 以负责人身份进入任务中心，只能改状态和进度备注。
3. 以负责人身份尝试改负责人或删除任务，确认前端无入口、后端也拒绝绕过请求。
4. 以无关成员身份确认无任务可见、也无操作入口。
