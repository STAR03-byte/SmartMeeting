# Views AGENTS.md

`frontend/src/views/` 是页面编排层，负责把路由、store、API 调用与 Element Plus 交互组合成可用流程。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 登录与鉴权跳转 | `LoginView.vue` | 依赖 `authStore.signIn` |
| 会议列表编排 | `MeetingListView.vue` | 过滤/分页/创建/删除与 store 协同 |
| 会议工作台主流程 | `MeetingDetailView.vue` | 上传转写、后处理、任务创建与状态流转 |
| 任务中心 | `TasksView.vue` | 列表筛选与状态更新 |
| 用户管理 | `UsersView.vue` | 用户创建/删除流程 |

## CONVENTIONS

- 页面层职责是编排，不承载底层 HTTP 细节；请求优先经 `src/api/` 或 store action。
- 统一使用 `ElMessage` 做用户可见反馈，失败时输出可理解文案。
- 页面状态（loading/error/列表）优先复用 store，避免跨页面重复状态源。
- 保持 `<script setup lang="ts">` 且类型显式（表单/事件/状态值）。
- 大页面改动优先“拆小函数+保持流程顺序”，避免继续堆叠单函数复杂度。

## ANTI-PATTERNS

- 在 view 内直接 new axios 或手写后端 URL。
- 空 `catch` 或失败后只 `console.log` 不反馈。
- 在多个页面复制同一业务流程（应下沉 store/api）。
- 修改页面流程后不验证关键路径（登录、会议详情、任务状态更新）。

## NOTES

- `MeetingDetailView.vue` 为高复杂度热点文件，变更需重点回归“上传音频→转写→后处理→任务更新”链路。
