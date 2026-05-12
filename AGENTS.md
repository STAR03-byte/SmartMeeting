# AGENTS.md — 执行型 Agent 指令

> 本文件面向执行型 AI agent（如 Codex、Cursor、Windsurf 等）。
> 目标：让 agent 能安全、准确地在 SmartMeeting 项目中执行编码任务。
>
> 架构型 agent（如 Claude）请阅读 [CLAUDE.md](CLAUDE.md)。

---

## Codex 的职责

Codex 决定**"怎么把这件事做完"**。具体包括：

1. **认领任务** — 在 TASKS.md 中找到状态为"待认领"的任务，将状态改为"进行中"，填写分支名
2. **按规格实现** — 严格按照 Claude 写的规格执行，不超出改动范围
3. **验证结果** — 运行测试，确认验收标准全部满足
4. **写完成报告** — 将状态改为"待审查"，填写完成报告

### Codex 不做的事

- 不自己决定"做什么"（那是 Claude 的职责）
- 不超出任务规格中定义的改动范围
- 不修改规格中明确标注"不要改"的文件
- 不引入规格中未提及的新依赖

### 工作流程

```
1. 读 TASKS.md → 找到"待认领"的任务
2. 读任务规格 → 理解要改什么、不要改什么
3. 创建分支 → 如 codex/t1-pipeline
4. 读相关代码 → 理解现有实现
5. 实现改动 → 严格按规格
6. 运行测试 → npm run test:backend 或 npm run ci
7. 更新 TASKS.md → 状态改为"待审查"，填写完成报告
8. 提交代码 → 等 Claude 审查
```

### 完成报告格式

```markdown
**Codex 完成报告：**
- 改了什么：<具体文件和改动描述>
- 测试结果：<通过/失败，附关键输出>
- 遗留问题：<如有，说明原因和建议>
```

---

## 项目一句话

SmartMeeting 是自托管的团队会议记忆系统。FastAPI 后端 + Vue 3 前端 + PostgreSQL 16 + Tauri 桌面端。

完整项目说明见 [PROJECT.md](PROJECT.md)。

---

## 执行前必读

1. **先读 [TASKS.md](TASKS.md)** — 找到"待认领"的任务，理解 Claude 的规格
2. **先读 [HANDOFF.md](HANDOFF.md)** — 了解上一个 agent 的交接上下文
3. **先读相关代码** — 不要凭假设修改，先读目标文件及其依赖

---

## 执行边界

### 可以做

- 修改 `backend/app/` 下的 Python 文件
- 修改 `frontend/src/` 下的 TypeScript/Vue 文件
- 修改 `database/migrations/` 和 `database/rollback/` 下的 SQL 文件
- 修改 `scripts/` 下的脚本文件
- 新增测试文件（遵循现有命名规范）
- 新增迁移文件（必须按顺序编号）

### 不可以做

- 不要修改 `backend/app/core/config.py` 的环境变量名（会破坏部署）
- 不要修改 `backend/app/api/v1/router.py` 的路由前缀（会破坏前端）
- 不要修改数据库表名或字段名（会破坏现有数据）
- 不要删除 `.github/workflows/` 下的 CI 配置
- 不要修改 `docker-compose.yml` 的端口映射（除非任务明确要求）
- 不要硬编码密钥、令牌、密码
- 不要引入新的外部依赖（除非任务明确要求，并更新 requirements.txt 或 package.json）

---

## 文件组织规则

### 后端 (Python)

```
路由层 (api/v1/endpoints/)  →  只做参数解析、调用 service、返回 schema
业务层 (services/business/) →  业务逻辑、事务边界
AI 层 (services/ai/)        →  LLM 调用、Whisper、Embedding、实体提取
管线层 (services/pipeline/) →  音频处理、作业调度
模型层 (models/)            →  ORM 模型，只做持久化
Schema 层 (schemas/)        →  Pydantic Schema，只做序列化校验
```

**关键约束：**
- 路由层不直接写 DB 查询
- 服务函数必须有完整类型标注
- 单文件不超过 800 行，单函数不超过 50 行

### 前端 (TypeScript/Vue)

```
views/       →  页面级组件，编排逻辑
components/  →  可复用组件，按领域分目录
stores/      →  Pinia 状态管理
composables/ →  组合式函数
api/         →  类型化 API 客户端
```

**关键约束：**
- 使用 `<script setup lang="ts">` + Composition API
- 避免 `any`，API 异常必须有可见反馈
- 组件命名 PascalCase，composable 命名 `useXxx.ts`

---

## 测试要求

### 必须做的事

- 新功能必须有对应测试
- 修改现有功能必须确认现有测试通过
- 测试文件放在对应目录下：
  - 后端：`backend/tests/test_*.py`
  - 前端：与源文件同目录，后缀 `.test.ts`

### 运行测试

```bash
# 后端全量测试
/usr/bin/python3 -m pytest backend/tests/ -v --tb=short

# 单个测试文件
/usr/bin/python3 -m pytest backend/tests/test_entity_extraction.py -v

# 前端测试
npx --prefix frontend vitest run

# 完整 CI
npm run ci
```

### 测试注意事项

- 后端测试使用 SQLite 内存数据库（不要求 PostgreSQL）
- 前端测试使用 Vitest + jsdom
- 测试文件中的 `client` fixture 是 FastAPI TestClient
- mock 外部服务（LLM、Whisper），不要在测试中调用真实 API

---

## 代码风格

### Python

- PEP 8，4 空格缩进
- 函数和变量 `snake_case`，类 `PascalCase`
- 所有公开函数必须有类型标注
- 错误处理：明确捕获，不吞异常
- 日志：使用 `logging` 模块，不用 `print()`

### TypeScript/Vue

- 2 空格缩进
- 组件 `PascalCase`，变量/函数 `camelCase`
- 接口用 `interface`，类型别名用 `type`
- 使用 `unknown` 而非 `any`

### SQL

- 关键字大写：`CREATE TABLE`、`SELECT`、`WHERE`
- 表名/字段名 `snake_case`
- 时间字段 `created_at` / `updated_at`

---

## 提交规范

```
<type>: <简短描述>

<可选正文：为什么改、影响范围>
```

type：`feat` / `fix` / `refactor` / `migrate` / `test` / `ci` / `docs` / `chore`

**关键约束：**
- 每个 commit 只包含一个主题
- 不混杂多个改动
- 数据库迁移单独 commit
- CI 配置变更单独 commit

---

## 交接要求

完成任务后，必须在 [HANDOFF.md](HANDOFF.md) 中添加一条交接记录，包含：

1. **时间** — 完成时间
2. **做了什么** — 具体改动描述
3. **改了哪些文件** — 文件列表
4. **验证结果** — 测试是否通过、CI 是否通过
5. **已知问题** — 遗留的 bug 或限制
6. **下一步建议** — 后续 agent 应该做什么

---

## 常见陷阱

1. **不要在路由层写 DB 查询** — 业务逻辑下沉到 service
2. **不要忘记 fallback** — LLM/Whisper 调用必须有降级路径
3. **不要忽略迁移顺序** — 新迁移必须编号在 032 之后
4. **不要修改已提交的迁移** — 只能新增迁移来修正
5. **不要在前端使用 `any`** — 使用 `unknown` 或具体类型
6. **不要硬编码环境变量** — 使用 `config.py` 中的配置

---

## 关键文件速查

| 文件 | 用途 |
|------|------|
| `backend/app/main.py` | FastAPI 应用入口 |
| `backend/app/core/config.py` | 所有配置项 |
| `backend/app/core/database.py` | 数据库引擎和 Session |
| `backend/app/api/v1/router.py` | 路由注册 |
| `backend/app/services/pipeline/job_manager.py` | 后处理管线 |
| `backend/app/services/ai/entity_extraction_service.py` | 实体提取 |
| `backend/app/services/ai/embedding_service.py` | Embedding 生成 |
| `frontend/src/api/client.ts` | API 客户端基类 |
| `frontend/src/api/types.ts` | 共享类型定义 |
| `frontend/src/router/index.ts` | 路由配置 |
| `database/migrations/` | 数据库迁移 |
