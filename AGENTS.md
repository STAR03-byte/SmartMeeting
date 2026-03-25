# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-25
**Commit:** 1c0278c
**Branch:** main

## OVERVIEW

SmartMeeting 是 FastAPI + Vue 3 + MySQL 的会议与任务系统。仓库为多域结构：业务代码（backend/frontend/database）+ 运维与文档（scripts/infrastructure/docs）。

## STRUCTURE

```text
SmartMeeting/
├── backend/         # FastAPI 服务（有独立 AGENTS）
│   └── app/
│       └── services/  # 业务核心（新增独立 AGENTS）
├── frontend/        # Vue3 + TS 应用（有独立 AGENTS）
│   └── src/
│       ├── api/       # API 封装（新增独立 AGENTS）
│       └── views/     # 页面编排（新增独立 AGENTS）
├── database/        # SQL 迁移/种子/回滚（有独立 AGENTS）
├── scripts/         # 执行脚本（db 编排在 scripts/db）
├── infrastructure/  # 部署资产目录（compose/docker/k8s/nginx）
└── docs/            # 文档与计划
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 后端路由/鉴权入口 | `backend/app/api/v1/endpoints/` | 路由保持薄层，复杂逻辑下沉 `services/` |
| 后端业务规则/AI回退 | `backend/app/services/` | LLM + rule fallback、任务抽取、事务操作 |
| 前端接口封装 | `frontend/src/api/` | 统一 `apiClient` + typed payload/response |
| 前端页面流程编排 | `frontend/src/views/` | 大页面集中，优先调用 store/api 而非直接拼 URL |
| 前端路由与守卫 | `frontend/src/router/index.ts` | 登录守卫依赖 auth store |
| 数据库变更与回滚 | `database/migrations/`, `database/rollback/` | 执行入口在 `scripts/db/*.sql` |
| CI 与基础校验 | `.github/workflows/ci.yml` | backend tests + frontend typecheck/build |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `app` | FastAPI app | `backend/app/main.py` | 应用实例、异常处理、`/api/v1` 挂载 |
| `lifespan` | function | `backend/app/main.py` | 启停资源管理 |
| `create_meeting` | service fn | `backend/app/services/meeting_service.py` | 会议写入主流程入口 |
| `apiClient` | Axios instance | `frontend/src/api/client.ts` | 统一 HTTP 客户端与 Bearer 注入 |
| `getApiErrorMessage` | function | `frontend/src/api/client.ts` | API 错误文本归一化 |
| `router` | Vue Router | `frontend/src/router/index.ts` | 路由表与登录守卫 |
| `useAuthStore` | Pinia store | `frontend/src/stores/authStore.ts` | token 持久化与当前用户加载 |
| `useMeetingStore` | Pinia store | `frontend/src/stores/meetingStore.ts` | 会议详情/转写/任务编排 |

## CONVENTIONS

- 中文沟通；代码/命令/路径保持英文。
- 增量改动优先：先改已有文件，再考虑新增文件。
- 后端遵循“路由薄、服务厚”；路由统一挂在 `/api/v1`。
- 前端固定 `<script setup lang="ts">` + Composition API。
- 前端构建链不可跳过类型检查：`build = vue-tsc --noEmit && vite build`。
- DB 管理采用 `migrations + seeds + rollback` 脚本链路（非 alembic）。

## ANTI-PATTERNS (THIS PROJECT)

- 未确认影响就执行破坏性命令（reset/覆盖历史/强制历史操作）。
- 擅自删除用户已有改动。
- 硬编码 secrets/token/password/DB 凭据。
- 引入 `any` / 无类型服务接口 / 空 `catch` 吞异常。
- 在后端 endpoint 直接写复杂业务或大量 DB 操作（应放 `services/`）。
- 跳过 `frontend` typecheck 或 `scripts/db/check_health.sql` 后宣称完成。

## UNIQUE STYLES

- 后端存在双入口：`backend/main.py`（uvicorn兼容）+ `backend/app/main.py`（真实应用装配）。
- DB 资产与执行脚本分离：定义在 `database/`，编排在 `scripts/db/`。
- 当前仓库无 `skills-main/`、`ui-ux-pro-max-skill-main/` 实体目录，避免按旧层级误改。

## COMMANDS

```bash
# backend
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
python -m pytest backend/tests -v --tb=short

# frontend
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
npm --prefix frontend run dev
npm --prefix frontend run typecheck
npm --prefix frontend run build

# database
mysql -u <user> -p < scripts/db/run_all.sql
mysql -u <user> -p < scripts/db/check_health.sql
mysql -u <user> -p < scripts/db/check_performance.sql
```

## HIERARCHY

- `./AGENTS.md`（root）
  - `./backend/AGENTS.md`
    - `./backend/app/services/AGENTS.md`
  - `./frontend/AGENTS.md`
    - `./frontend/src/api/AGENTS.md`
    - `./frontend/src/views/AGENTS.md`
  - `./database/AGENTS.md`
