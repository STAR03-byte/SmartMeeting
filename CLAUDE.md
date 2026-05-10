# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言规则

- 始终使用中文（简体）回复用户。代码、命令、路径、接口字段名保持英文原样。
- 先给结论，再给关键步骤。涉及改动时说明：改了什么、为什么改、如何验证。

## 项目概述

SmartMeeting 是 AI 驱动的智能会议录音与任务管理系统。前后端分离架构，后端 FastAPI + 前端 Vue 3，PostgreSQL 16 数据库（pgvector 扩展），集成 Whisper 语音识别和 LLM 会议总结。

## 常用命令

```bash
# 开发（一键启动前后端，自动安装依赖）
npm run dev

# 单独启动
npm run dev:backend       # 后端 uvicorn --reload (http://127.0.0.1:8000)
npm run dev:frontend      # 前端 Vite dev server (http://127.0.0.1:5173)

# 测试
npm run test:backend      # pytest backend/tests -v --tb=short
npx --prefix frontend vitest run   # 前端单元测试

# 类型检查
npm run check:frontend:type   # vue-tsc --noEmit

# 完整 CI 流水线（迁移顺序检查 → 后端测试 → 前端类型检查 → 前端构建）
npm run ci

# 生产构建
npm run build:frontend    # vue-tsc --noEmit && vite build

# Docker 全栈
docker compose up --build   # 前端 :5174, 后端 :8000, PostgreSQL :5432

# 数据库迁移顺序校验
npm run check:db:order

# 冒烟测试 / QA
npm run smoke
npm run qa
```

## 架构

### 后端 (`backend/`)

FastAPI 应用，遵循 **路由薄、服务厚** 原则：

- `app/api/v1/endpoints/` — REST 路由处理器，只做参数解析、依赖注入、调用 service、返回 schema
- `app/services/` — 业务逻辑层（会议、任务、认证、AI 处理等）
- `app/models/` — SQLAlchemy 2.0 ORM 模型（16 个），仅负责持久化
- `app/schemas/` — Pydantic v2 请求/响应 Schema，仅负责序列化与校验
- `app/core/` — 配置、数据库引擎、JWT 安全、限流
- `app/services/ai/` — LLM 客户端（OpenAI + Ollama 回退链）、Whisper ASR、说话人分离、知识查询、对话管理、上下文构建
- `app/services/pipeline/` — 音频处理管线、作业管理器、GPU 管理

API 统一前缀 `/api/v1`。数据库 Session 通过 `Depends(get_db)` 注入。服务函数必须有完整类型标注，事务边界收敛在服务层。

### 前端 (`frontend/`)

Vue 3 + TypeScript + Pinia + Element Plus + UnoCSS：

- `src/api/` — 类型化 API 客户端，统一错误处理与 baseURL，页面层不直接拼接 URL
- `src/views/` — 页面级组件（14 个），职责是编排，HTTP 细节下沉到 api/store
- `src/stores/` — Pinia 状态管理（auth、meeting、taskCenter、aiAssistant）
- `src/composables/` — 组合式函数（录音、转写、摘要、作业进度、说话人分离）
- `src/components/` — 可复用组件，按领域分目录（meeting/、ai/、common/、workbench/）
- `src/locales/` — i18n 翻译（zh-CN、en-US）

强制使用 `<script setup lang="ts">` + Composition API。组件命名 PascalCase，composable 命名 `useXxx.ts`。避免 `any`，API 异常必须有可见反馈。

### 数据库 (`database/`)

PostgreSQL 16 + pgvector 扩展，测试时使用 SQLite 快速回退。

- `migrations/` — 30 个顺序编号的 SQL 迁移文件（001 ~ 030），PostgreSQL 语法
- `seeds/` — 种子数据
- `rollback/` — 按版本逆序回滚脚本
- 表名/字段名 `snake_case`，时间字段 `created_at`/`updated_at`
- 迁移顺序由 CI 的 `check:db:order` 校验，新增迁移必须按序编号
- 030 号迁移预埋 tsvector 列和 GIN 索引，为 Phase 2 全文搜索做准备

### 关键环境变量

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
```

## 开发约束

- 路由层不直接写 DB 查询，业务逻辑下沉到 `app/services/`
- Model/Schema 分离：models 只做持久化，schemas 只做序列化校验
- 外部能力（LLM/Whisper）必须有 fallback 路径，不吞异常
- 前端构建前置类型检查（`vue-tsc --noEmit`）不可绕过
- 数据库变更优先通过迁移管理，新增迁移文件必须按顺序编号
- 严禁硬编码密钥、令牌、密码等敏感信息
