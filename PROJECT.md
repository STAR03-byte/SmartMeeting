# PROJECT.md — SmartMeeting 项目全景

> 本文件是项目的第一入口。任何 AI agent 或人类开发者在开始工作前，应先读此文件。

---

## 项目定位

SmartMeeting 是一个**自托管的团队会议记忆系统**。

核心价值主张：**"Never forget what was decided in a meeting."**

它不是视频会议工具，不是通用知识管理平台，不是实时协作工具。它解决的问题是：团队开了很多会，但决策和承诺散落在各处，无人追踪，事后无法回溯。

**数据不出内网**是硬性约束。

---

## 当前阶段

**版本：v3.0.0**（2026-05-12 发布）

三个 Phase 已全部完成并合并到 main：

| 阶段 | 版本 | 核心交付 |
|------|------|----------|
| Phase 1 — 平台层统一 | v2.0 | PostgreSQL 16 + pgvector、29 个迁移脚本重写、AI 服务治理（拆分为 3 个子模块）、远程 Whisper |
| Phase 2 — 会议记忆能力 | v2.5 | 跨会议语义搜索、决策/承诺提取与确认、承诺状态流转、主题抽取、Embedding 服务 |
| Phase 3 — 终端入口增强 | v3.0 | Tauri 桌面端（系统音频采集、离线转写队列、跨平台构建 CI）、Web 端响应式适配 |

**下一步方向：** 巩固已有功能、补齐测试缺口、优化性能、桌面端完善。详见 [TASKS.md](TASKS.md)。

---

## 架构原则

1. **路由薄、服务厚** — API 端点只做参数解析和调用 service，业务逻辑下沉到 `services/`。
2. **统一知识底座** — 搜索、决策、承诺、AI 助手共享同一套 Embedding + pgvector + tsvector 基础设施。
3. **候选提取 + 人工确认** — LLM 提取的结果是"候选"，用户可以确认、修正、删除。
4. **渐进增强** — 外部能力（LLM/Whisper）必须有 fallback 路径，不吞异常。
5. **数据不出内网** — 自托管部署，不依赖外部 SaaS（除可选的远程 Whisper API）。

---

## 核心模块

### 后端 (`backend/app/`)

```
backend/app/
├── api/v1/endpoints/   # 19 个路由文件，REST API 层（薄）
├── models/             # 19 个 SQLAlchemy ORM 模型
├── schemas/            # 16 个 Pydantic v2 Schema
├── services/
│   ├── business/       # 11 个业务服务（会议、任务、团队、权限等）
│   ├── ai/             # 13 个 AI 服务（LLM、Whisper、Embedding、实体提取等）
│   │   ├── llm/        # LLM 客户端子层（provider 链 + fallback）
│   │   └── prompts/    # Prompt 模板
│   └── pipeline/       # 4 个管线服务（音频处理、作业管理、GPU 管理）
├── core/               # 配置、数据库引擎、JWT、限流、错误处理
└── main.py             # FastAPI 应用入口
```

**关键文件（按复杂度排序）：**
- `services/business/meeting_service.py` (691 行) — 会议生命周期管理
- `services/ai/llm/client.py` (688 行) — LLM provider 链（OpenAI + Ollama + mock）
- `services/pipeline/job_manager.py` (545 行) — 音频处理作业调度
- `services/ai/whisper_service.py` (437 行) — 本地 Whisper ASR
- `services/ai/knowledge_service.py` (372 行) — 知识查询与 RAG
- `api/v1/endpoints/meetings.py` (620 行) — 会议 API 端点

### 前端 (`frontend/src/`)

```
frontend/src/
├── api/                # 24 个文件：类型化 API 客户端 + 测试
├── views/              # 17 个页面级组件
├── components/         # 12 个可复用组件（按领域分：ai/、meeting/、common/、workbench/）
├── stores/             # 4 个 Pinia 状态管理
├── composables/        # 6 个组合式函数
├── desktop/            # 4 个桌面端专用视图
├── router/             # 路由配置
├── locales/            # i18n（zh-CN、en-US）
└── utils/              # 工具函数
```

**关键文件（按复杂度排序）：**
- `views/MeetingDetailView.vue` (724 行) — 会议详情页（转写、摘要、任务、决策、承诺）
- `views/DashboardView.vue` (584 行) — 仪表盘
- `views/TasksView.vue` (565 行) — 任务中心
- `views/TeamDetailView.vue` (529 行) — 团队详情
- `views/AIAssistantView.vue` (517 行) — AI 助手对话

### 数据库 (`database/`)

```
database/
├── migrations/         # 30 个迁移文件（001~032，跳过 017、026）
├── seeds/              # 2 个种子数据文件
├── rollback/           # 20 个回滚脚本
├── docker-init.sh      # Docker 启动时自动执行迁移
└── README.md
```

- 数据库：PostgreSQL 16 + pgvector 扩展
- 表名/字段名 `snake_case`，时间字段 `created_at`/`updated_at`
- 迁移顺序由 CI 的 `check:db:order` 校验
- 030 号迁移预埋 tsvector 列和 GIN 索引
- 031 号迁移创建 decisions/commitments/meeting_topics 表
- 032 号迁移创建 embeddings 表（pgvector）

### 桌面端 (`desktop/src-tauri/`)

```
desktop/src-tauri/
├── src/
│   ├── main.rs             # Tauri 入口
│   ├── lib.rs              # 152 行：命令注册 + AppState
│   ├── audio_capture.rs    # 244 行：系统音频采集（cpal）
│   ├── meeting_session.rs  # 397 行：会议会话 + 离线队列（rusqlite）
│   └── transcription.rs    # 147 行：本地 Whisper 转写
├── Cargo.toml              # Rust 依赖
├── tauri.conf.json         # Tauri 配置
└── icons/                  # 跨平台图标
```

- Tauri 2.x，前端复用 `frontend/dist`
- `audio-capture` feature flag 控制 cpal/hound 依赖
- 离线队列基于本地 SQLite，上限 1000 条

### 基础设施

```
infrastructure/
├── compose/docker-compose.prod.yml   # 生产环境 Docker Compose
├── k8s/                              # Kubernetes 部署模板
│   ├── deployment.yml
│   ├── service.yml
│   └── configmap.yml
└── nginx/nginx.prod.conf             # Nginx 反向代理配置
```

### CI/CD (`.github/workflows/`)

- `ci.yml` — 迁移顺序检查 + 后端测试 + 前端类型检查 + 前端构建
- `desktop.yml` — Tauri 跨平台构建（Linux/macOS/Windows）

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI 0.135 + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| 数据库 | PostgreSQL 16 + pgvector |
| 向量搜索 | pgvector ivfflat 索引 |
| 全文搜索 | tsvector + GIN 索引 |
| LLM 客户端 | OpenAI SDK + Ollama 回退链 |
| ASR | Whisper (本地) / faster-whisper / Groq API (远程) |
| Embedding | sentence-transformers + bge-small-zh-v1.5 |
| 前端框架 | Vue 3.5 + TypeScript 5.9 |
| UI 组件库 | Element Plus 2.11 |
| 状态管理 | Pinia 3.0 |
| CSS | UnoCSS |
| 构建工具 | Vite 7.1 |
| 桌面端 | Tauri 2.11 (Rust) |
| 测试 | pytest (后端) + Vitest (前端) |
| CI | GitHub Actions |

---

## 常用命令

```bash
# 一键启动（前后端）
npm run dev

# 单独启动
npm run dev:backend       # http://127.0.0.1:8000
npm run dev:frontend      # http://127.0.0.1:5173

# 测试
npm run test:backend      # pytest
npx --prefix frontend vitest run  # 前端测试

# 类型检查
npm run check:frontend:type

# 完整 CI
npm run ci

# Docker 全栈
docker compose up --build   # 前端 :5174, 后端 :8000, PostgreSQL :5432

# 数据库迁移顺序校验
npm run check:db:order

# 历史数据 Embedding 回填
/usr/bin/python3 backend/scripts/backfill_embeddings.py --all
/usr/bin/python3 backend/scripts/backfill_embeddings.py --dry-run --all
```

---

## 环境变量

```bash
# 数据库
DB_BACKEND=postgresql|sqlite    DB_AUTO_FALLBACK_SQLITE=true
DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME

# LLM（不配置则使用规则回退）
LLM_PROVIDER=openai   LLM_API_KEY=sk-xxx   LLM_MODEL=gpt-4o-mini
LLM_FALLBACK_PROVIDER=ollama   OLLAMA_BASE_URL=http://host.docker.internal:11434

# JWT
JWT_SECRET_KEY=change-me-in-production

# Whisper（不配置则使用 mock ASR）
WHISPER_MODEL=base   WHISPER_DEVICE=cpu|cuda   WHISPER_LANGUAGE=zh

# Embedding（不配置则使用 mock）
EMBEDDING_MODEL=small   EMBEDDING_DEVICE=cpu
```

---

## 开发约束

1. **路由层不直接写 DB 查询** — 业务逻辑下沉到 `services/`
2. **Model/Schema 分离** — models 只做持久化，schemas 只做序列化校验
3. **外部能力必须有 fallback** — LLM/Whisper 不吞异常，有明确的降级路径
4. **前端构建前置类型检查** — `vue-tsc --noEmit` 不可绕过
5. **数据库变更通过迁移管理** — 新增迁移文件必须按顺序编号
6. **严禁硬编码密钥** — 敏感信息通过环境变量注入
7. **文件大小约束** — 单文件不超过 800 行，超过需拆分
8. **函数大小约束** — 单函数不超过 50 行，超过需提取

---

## 文件索引

| 文件 | 用途 |
|------|------|
| [PROJECT.md](PROJECT.md) | 本文件 — 项目全景 |
| [TASKS.md](TASKS.md) | 当前任务清单 |
| [HANDOFF.md](HANDOFF.md) | 交接记录 |
| [AGENTS.md](AGENTS.md) | 执行型 agent 指令（Codex 等） |
| [CLAUDE.md](CLAUDE.md) | 架构型 agent 指令（Claude 等） |
| [AI_CONFIG.md](AI_CONFIG.md) | 全局 AI 配置 |
| [README.md](README.md) | 项目介绍 |
| [docs/](docs/) | 详细文档（API、数据库设计、部署等） |
