# Endpoints AGENTS.md

`backend/app/api/v1/endpoints/` 是 API v1 的路由薄层：只负责 HTTP 输入输出、依赖注入与状态码，不承载业务规则。

> 继承：`backend/AGENTS.md`（全局后端约定） + `backend/app/services/AGENTS.md`（业务层规则）。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 路由聚合 | `../router.py` | 统一 include 各 endpoint router |
| 认证 | `auth.py` | 登录、当前用户依赖 `get_current_user` |
| 会议 CRUD/音频/后处理 | `meetings.py` | 只做参数校验与调用 services |
| 分享/公开访问 | `meeting_shares.py`, `shared_meetings.py` | token/权限与返回结构 |
| 任务/转写/参与人 | `tasks.py`, `transcripts.py`, `participants.py` | 列表查询与状态流转入口 |
| 用户管理 | `users.py` | 创建/列表/删除与权限约束 |

## CONVENTIONS

- endpoint 只做：参数解析/校验、`Depends(...)` 注入、调用 `app/services/`、返回 schema。
- 数据库 Session 通过 `Depends(get_db)` 注入；不要在 endpoint 内创建 engine/session。
- 路由统一挂载在 `/api/v1`（由 `backend/app/main.py` include）。
- 错误处理：用明确的 `HTTPException` 状态码与可操作信息；不要吞异常。

## ANTI-PATTERNS

- 不要在 endpoint 内直接写复杂业务或大量 DB 操作（应下沉 `app/services/`）。
- 不要在 endpoint 内做跨领域编排（如“上传→转写→后处理→任务生成”链路），应在 service 层提供单入口。
- 不要硬编码路径/配置（使用 `app/core/config.py` settings）。
