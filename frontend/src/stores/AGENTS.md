# Stores AGENTS.md

`frontend/src/stores/` 是 Pinia 状态层：负责可复用的页面状态、缓存与跨视图流程编排（但不承载底层 HTTP 细节）。

> 继承：`frontend/AGENTS.md`（前端全局约定） + `frontend/src/api/AGENTS.md`（请求层约定）。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 登录/登出与当前用户 | `authStore.ts` | token 持久化 key：`smartmeeting_access_token` |
| 会议工作台数据编排 | `meetingStore.ts` | 会议详情、转写、任务列表与状态更新主链路 |
| store 单测 | `meetingStore.test.ts` | vitest 约束核心行为 |

## CONVENTIONS

- store action 遇到 API 失败必须给出可见错误：统一 `getApiErrorMessage(error)`，同时 `throw` 让 view 决定 UI 行为。
- token 读写集中在 `authStore.ts`，其他模块不要复制 storage key。
- store 层只调用 `src/api/` wrapper，不在 store 拼 URL 或 new axios。
- loading/error 的生命周期要可预测：action 开始置位，finally 复位。

## ANTI-PATTERNS

- 在 store 内吞异常（空 `catch`）或只记录日志不更新 `error`。
- 在多个 store/页面重复实现同一条“上传→转写→刷新详情”等流程，应抽到单一 action。
- 返回未声明结构导致隐式 `any`（保持与 `src/api/types.ts` 对齐）。
