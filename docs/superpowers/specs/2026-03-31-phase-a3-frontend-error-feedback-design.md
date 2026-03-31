#+ SmartMeeting Phase A-3: Frontend error visibility design

**Date**: 2026-03-31  
**Status**: Draft  
**Project**: SmartMeeting  
**Baseline commit**: `1d1d6d0`

## 1. Background

SmartMeeting 前端已具备基础错误展示能力：

- API 层通过 `getApiErrorMessage(err)` 归一化错误文本（`frontend/src/api/client.ts`）。
- 多数视图在操作失败时使用 `ElMessage.error(getApiErrorMessage(err))` 弹出 toast。
- 会议列表/详情页也会通过 store 的 `error` 字符串配合 `AppErrorAlert` 做页面级持久提示。

但目前错误提示逻辑分散在多个视图内，且存在少量“可能静默失败/用户不可见”的风险点（例如启动时拉取当前用户失败的路径）。

本阶段聚焦一个最小闭环：**让关键用户流程中的 API 失败都“可见”，并把重复 toast 错误提示收敛为一个可复用的工具函数**。

## 2. Goals

1. 关键用户流程中，任意 API 失败都有明确的用户可见反馈（toast 或页面级 alert）。
2. 对错误 toast 的调用方式收敛为统一入口，降低重复代码并便于后续扩展（去重/节流/埋点）。
3. 不改变现有 store / view 的职责边界：store 仍可维护 `error` 状态并抛出异常，view 决定 UI 展示策略。
4. 保持变更最小化，避免引入全局响应拦截器导致重复提示或流程变化。

## 3. Scope

### In scope

- 新增统一错误 toast 工具：`frontend/src/utils/notify.ts`
- 修复/补齐 `authStore.loadCurrentUser` 的错误可见性（避免静默失败）
- 在高影响视图中，用新工具替换重复的 `ElMessage.error(getApiErrorMessage(err))`
  - `frontend/src/views/MeetingDetailView.vue`
  - `frontend/src/views/MeetingListView.vue`
  - `frontend/src/views/TasksView.vue`
  - `frontend/src/views/UsersView.vue`

### Out of scope

- axios 全局 response interceptor（避免重复 toast、隐式跳转等副作用）
- 大范围重构（只做“错误可见反馈”相关最小改动）
- 引入新的 UI 组件体系（继续使用 Element Plus 的 `ElMessage` 与现有 `AppErrorAlert`）

## 4. Proposed approaches

### Approach A: lightweight utility + targeted fixes (Recommended)

新增一个小工具函数 `notifyApiError(err)` 作为统一 toast 入口；在关键流程视图中替换重复用法；补齐启动拉取用户失败路径的错误处理。

Pros:

- 变更小、风险低，便于回滚
- 不改变现有数据流；仅收敛 UI 提示
- 后续可在工具函数中统一做去重/节流/埋点

Cons:

- 仍然需要在视图层显式调用（不会自动覆盖所有遗漏点）

### Approach B: axios response interceptor auto-toast

在 `apiClient` 增加响应拦截器，自动对 4xx/5xx 弹 toast。

Pros:

- 全覆盖，调用方无需关心

Cons:

- 容易重复提示（调用方已有 toast）
- 对登录过期/401 等场景需要更复杂的策略
- 难以区分“静默失败允许/不允许”的不同交互

结论：采用 Approach A。

## 5. Design details

### 5.1 notify utility

Create `frontend/src/utils/notify.ts`:

- `notifyApiError(err: unknown, options?: { prefix?: string })`
- 内部实现：`ElMessage.error(prefix ? `${prefix}: ${msg}` : msg)`
- `msg` 来源：`getApiErrorMessage(err)`

约束：

- 不吞错误（工具函数只负责展示，不做 try/catch 包装）。
- 默认不做节流/去重；先保证正确性与一致性。

### 5.2 authStore.loadCurrentUser

Modify `frontend/src/stores/authStore.ts`:

- 在 `loadCurrentUser` 中捕获错误并设置 `this.error = getApiErrorMessage(err)`
- 对外仍抛出错误（或返回失败状态），由调用方决定是否 toast。

理由：

- 启动时的“当前用户加载失败”应可诊断（至少在页面有 error 状态），避免 silent failure。

### 5.3 View-level changes

在以下页面中，将重复的 toast 错误提示统一替换为 `notifyApiError(err)`：

- `MeetingDetailView.vue`
- `MeetingListView.vue`
- `TasksView.vue`
- `UsersView.vue`

页面级持久错误展示策略保持不变：

- 继续使用 `AppErrorAlert` 展示 store.error 或页面 error state（用于“持久、需要用户注意”的错误）。
- toast 用于“操作失败/一次性错误”。

## 6. Testing strategy

- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`
- `python scripts/dev/qa.py`

若项目已有前端单测框架并覆盖相关模块，可补充：

- `notifyApiError` 单元测试（验证 prefix 拼接与 msg 来源）

否则本阶段以类型检查与构建为主，确保无回归。

## 7. Rollout / risk

- 变更为局部替换 + 新工具函数，风险主要在导入路径与运行时依赖（Element Plus message）。
- 若出现重复 toast：优先保证“至少可见”，再按页面逐步去除额外提示。
