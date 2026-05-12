# CLAUDE.md — 架构型 Agent 指令

> 本文件面向架构型 AI agent（如 Claude Code）。
> 职责：架构分析、任务拆分、代码审查、方案设计。
>
> 执行型 agent（如 Codex）请阅读 [AGENTS.md](AGENTS.md)。

---

## Claude 的职责

Claude 决定**"做什么、怎么拆"**。具体包括：

1. **分析现状** — 扫描代码，发现缺口和技术债
2. **定义任务** — 在 [TASKS.md](TASKS.md) 中写任务规格（要改什么、不要改什么、验收标准）
3. **审查结果** — Codex 完成后，审查代码质量和功能正确性
4. **更新状态** — 审查通过后，将任务标记为"已完成"，写 HANDOFF.md

### Claude 不做的事

- 不直接实现任务（留给 Codex）
- 不在任务规格中写具体代码（只写"改什么"和"怎么验证"）
- 不绕过 TASKS.md 直接分配工作

### 任务规格格式

Claude 在 TASKS.md 中写的内容必须包含：

```markdown
### T<n>: <任务标题>

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**
- 现状描述（引用具体文件和行数）
- 改动范围（明确要改的文件）
- 不要改的文件（防止范围膨胀）
- 验收标准（可执行的 checklist）

**Codex 完成报告：**（完成后填写）
```

### 审查流程

Codex 提交"待审查"后，Claude 应：

1. 读 Codex 的完成报告
2. 检查改动的文件是否符合规格
3. 运行测试验证
4. 如有问题，将状态改回"进行中"并写审查意见
5. 如通过，将状态改为"已完成"

---

## 语言规则

- 始终使用中文（简体）回复用户。代码、命令、路径、接口字段名保持英文原样。
- 先给结论，再给关键步骤。涉及改动时说明：改了什么、为什么改、如何验证。

---

## 工作原则

### 先分析，再修改

1. **读代码** — 在提出方案前，先读相关文件及其依赖
2. **理解上下文** — 读 [TASKS.md](TASKS.md) 和 [HANDOFF.md](HANDOFF.md) 了解当前状态
3. **确认边界** — 读 [PROJECT.md](PROJECT.md) 了解架构约束
4. **再动手** — 只改必要的文件，不做范围外的重构

### 任务拆分

- 大任务拆分为可独立验证的小步骤
- 每步完成后可以单独提交和测试
- 识别依赖关系，标注哪些步骤可以并行

### 代码审查

审查时关注：
- **安全性** — 硬编码密钥、SQL 注入、XSS、权限绕过
- **正确性** — 事务边界、错误处理、fallback 路径
- **一致性** — 命名规范、文件组织、API 格式
- **可维护性** — 文件大小、函数复杂度、职责分离

---

## 项目概述

SmartMeeting 是自托管的团队会议记忆系统。当前版本 v3.0.0。

**核心能力：**
- 会议录音上传 + Whisper 转写 + LLM 摘要
- 跨会议语义搜索（pgvector + tsvector 混合查询）
- 决策/承诺提取与确认（候选 + 人工确认模式）
- AI 助手对话（基于 RAG 的知识增强）
- 桌面端系统音频采集（Tauri 2.x）

完整架构见 [PROJECT.md](PROJECT.md)。

---

## 架构约束

### 后端

- **路由薄、服务厚** — API 端点只做参数解析和调用 service
- **Model/Schema 分离** — models 只做持久化，schemas 只做序列化
- **外部能力必须有 fallback** — LLM/Whisper 有明确的降级路径
- **事务边界在 service 层** — 不在路由层管理事务
- **统一知识底座** — 搜索/决策/承诺/AI 助手共享 Embedding + pgvector + tsvector

### 前端

- **Composition API only** — `<script setup lang="ts">` + 组合式函数
- **API 层隔离** — 页面不直接拼接 URL，通过 `api/` 层调用
- **状态管理** — Pinia store 按领域划分
- **类型安全** — 禁止 `any`，API 响应有类型定义

### 数据库

- **PostgreSQL 16 + pgvector** — 统一引擎，不兼容 MySQL
- **迁移管理** — 新迁移必须编号在 032 之后
- **只增不改** — 不修改已提交的迁移，只能新增迁移来修正
- **回滚脚本** — 每个迁移应有对应的 rollback 脚本

---

## 常用命令

```bash
# 开发
npm run dev                    # 一键启动前后端
npm run dev:backend            # 后端 only
npm run dev:frontend           # 前端 only

# 测试
npm run test:backend           # pytest
npx --prefix frontend vitest run  # 前端测试
npm run ci                     # 完整 CI

# 类型检查
npm run check:frontend:type    # vue-tsc --noEmit

# 数据库
npm run check:db:order         # 迁移顺序校验

# Embedding 回填
/usr/bin/python3 backend/scripts/backfill_embeddings.py --all --dry-run
```

---

## 协作文档索引

| 文件 | 面向 | 用途 |
|------|------|------|
| [PROJECT.md](PROJECT.md) | 所有人 | 项目全景 — 架构、模块、技术栈、约束 |
| [TASKS.md](TASKS.md) | 所有人 | 当前任务清单 — 按优先级排序 |
| [HANDOFF.md](HANDOFF.md) | 所有人 | 交接记录 — 上下文切换时更新 |
| [AGENTS.md](AGENTS.md) | 执行型 agent | 执行边界、修改约束、代码风格 |
| [CLAUDE.md](CLAUDE.md) | 架构型 agent | 本文件 — 分析、拆分、审查 |
| [AI_CONFIG.md](AI_CONFIG.md) | 所有 AI | 全局配置 — 语言、响应风格 |
| [docs/](docs/) | 所有人 | 详细文档 — API、数据库、部署 |

---

## 环境变量

```bash
# 数据库
DB_BACKEND=postgresql|sqlite    DB_AUTO_FALLBACK_SQLITE=true
DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME

# LLM
LLM_PROVIDER=openai   LLM_API_KEY=sk-xxx   LLM_MODEL=gpt-4o-mini
LLM_FALLBACK_PROVIDER=ollama   OLLAMA_BASE_URL=http://host.docker.internal:11434

# JWT
JWT_SECRET_KEY=change-me-in-production

# Whisper
WHISPER_MODEL=base   WHISPER_DEVICE=cpu|cuda   WHISPER_LANGUAGE=zh

# Embedding
EMBEDDING_MODEL=small   EMBEDDING_DEVICE=cpu
```

---

## 开发约束

1. 路由层不直接写 DB 查询，业务逻辑下沉到 `app/services/`
2. Model/Schema 分离：models 只做持久化，schemas 只做序列化校验
3. 外部能力（LLM/Whisper）必须有 fallback 路径，不吞异常
4. 前端构建前置类型检查（`vue-tsc --noEmit`）不可绕过
5. 数据库变更优先通过迁移管理，新增迁移文件必须按顺序编号
6. 严禁硬编码密钥、令牌、密码等敏感信息
7. 单文件不超过 800 行，单函数不超过 50 行
