# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-17
**Commit:** 369a823
**Branch:** main

## OVERVIEW

SmartMeeting 主工程是 FastAPI + Vue 3 + MySQL 的会议系统（MVP 阶段）。
仓库同时包含两个外部技能工程（`skills-main/`、`ui-ux-pro-max-skill-main/`），与主业务代码分域维护。

## STRUCTURE

```text
SmartMeeting/
├── backend/                   # 主后端服务（有独立 AGENTS）
├── frontend/                  # 主前端应用（新增独立 AGENTS）
├── database/                  # SQL 迁移/种子/回滚（新增独立 AGENTS）
├── docs/                      # 业务与运行文档
├── scripts/                   # 辅助脚本（含 DB 批量执行脚本）
├── skills-main/               # 外部技能仓（新增独立 AGENTS）
└── ui-ux-pro-max-skill-main/  # UI/UX 技能仓（新增独立 AGENTS）
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 新增/修改后端 API | `backend/app/api/v1/endpoints/` | 业务逻辑下沉到 `backend/app/services/` |
| 调整后端模型/校验 | `backend/app/models/`, `backend/app/schemas/` | Model 与 Schema 分离 |
| 前端页面/路由/状态 | `frontend/src/views/`, `frontend/src/router/`, `frontend/src/stores/` | Vue 3 + Pinia |
| DB 结构变更 | `database/migrations/` | 回滚在 `database/rollback/` |
| DB 初始化/健康检查 | `scripts/db/` | 对应 `database/README.md` 顺序 |
| 技能工程修改 | `skills-main/`, `ui-ux-pro-max-skill-main/` | 按各自子目录 AGENTS 执行 |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `app` | FastAPI app | `backend/app/main.py` | 应用实例与异常处理挂载 |
| `lifespan` | function | `backend/app/main.py` | 启停生命周期日志与资源处理 |
| `router` | Vue Router | `frontend/src/router/index.ts` | 前端路由入口 |
| `meetingStore` | Pinia store | `frontend/src/stores/meetingStore.ts` | 会议状态管理 |
| `api` | Axios client | `frontend/src/api/client.ts` | 统一 HTTP 客户端 |

## CONVENTIONS

- 中文沟通；代码/命令/路径保持英文。
- 变更尽量最小化，优先改现有文件；避免无关重构。
- 后端保持“路由薄、服务厚”模式；`/api/v1` 版本化入口。
- 前端使用 `<script setup lang="ts">` + Composition API + Pinia。
- 禁止硬编码 secrets/token/password。

## ANTI-PATTERNS (THIS PROJECT)

- 未确认影响前执行破坏性命令（reset/覆盖历史等）。
- 擅自删除用户已有改动。
- 在前端/后端中引入 `any`、空 `catch`、无类型服务接口。
- 在后端 endpoint 中直接写复杂业务或大量 DB 操作（应放 services）。

## UNIQUE STYLES

- 主工程 + 外部技能工程共仓：改动时先确认目标域，避免跨域误改。
- `database/` 采用“migrations + seeds + rollback”三段式，而非 alembic。
- 前端构建脚本内置类型检查：`build = vue-tsc --noEmit && vite build`。

## COMMANDS

```bash
# backend
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
pytest backend/tests -v
ruff check backend/app backend/tests
black backend/app backend/tests
isort backend/app backend/tests
mypy backend/app

# frontend
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
npm --prefix frontend run dev
npm --prefix frontend run typecheck
npm --prefix frontend run build

# database
mysql -u <user> -p < scripts/db/run_all.sql
mysql -u <user> -p < scripts/db/check_health.sql
```

## HIERARCHY

- `./AGENTS.md`（本文件）
  - `./backend/AGENTS.md`
  - `./frontend/AGENTS.md`
  - `./database/AGENTS.md`
  - `./skills-main/AGENTS.md`
  - `./ui-ux-pro-max-skill-main/AGENTS.md`
