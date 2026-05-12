# HANDOFF.md — 交接记录

> 本文件记录每次重要的上下文切换、阶段性收尾、或 agent 之间的任务交接。
> 每条记录包含：时间、交接人、当前状态、下一步建议、关键上下文。

---

## 2026-05-12 — 建立 Claude-Codex 协作协议

**交接人：** Claude (架构负责人)
**触发：** 用户要求建立 Claude 和 Codex 的分工协作机制。

### 协作分工

- **Claude：** 决定"做什么、怎么拆" — 分析现状、写任务规格、审查结果
- **Codex：** 决定"怎么做完" — 认领任务、按规格实现、写完成报告

### 协作流程

```
Claude 扫描代码 → 写 TASKS.md 规格
                    ↓
Codex 认领任务 → 改状态为"进行中"
                    ↓
Codex 实现 → 运行测试 → 改状态为"待审查" → 写完成报告
                    ↓
Claude 审查 → 通过则改"已完成" / 不通过则改"进行中"并写意见
```

### 关键文件

| 文件 | 作用 |
|------|------|
| TASKS.md | 协作接口 — Claude 写规格，Codex 填状态和报告 |
| HANDOFF.md | 上下文传递 — 记录每次重要切换 |
| CLAUDE.md | Claude 的职责和工作流 |
| AGENTS.md | Codex 的职责和工作流 |

### 当前任务状态

TASKS.md 中已有 10 个任务（T1-T10），全部状态为"待认领"。Codex 可以从 T1 开始。

---

## 2026-05-12 — v3.0.0 发布，协作文档初始化

**交接人：** Claude (架构负责人)
**触发：** 用户要求生成 5 个协作文档，作为 Claude 和 Codex 的长期协作入口。

### 当前状态

- **分支：** main，领先 origin 24 个提交
- **版本：** v3.0.0（tag 已打）
- **CI：** 全量通过（224 后端测试、前端类型检查、前端构建）
- **工作区：** 干净（仅有 `.claude/settings.local.json` 和 `frontend/components.d.ts` 未暂存）

### 已完成的里程碑

| 里程碑 | 版本 | 提交范围 | 核心交付 |
|--------|------|----------|----------|
| 平台层统一 | v2.0.0 | 43c3f6b ~ 722505b | PostgreSQL 16 + pgvector、迁移重写、AI 服务拆分 |
| 会议记忆能力 | v2.5.0 | 47f07ab ~ d7d1cc8 | 跨会议搜索、决策/承诺提取、主题抽取 |
| 终端入口增强 | v3.0.0 | 784ec01 ~ 150a953 | 桌面端、跨平台 CI、响应式适配 |

### 关键技术决策记录

1. **数据库从 MySQL 迁移到 PostgreSQL 16** — 为了支持 pgvector 向量搜索和 tsvector 全文搜索
2. **AI 服务拆分为 3 个子模块** — `knowledge_service.py`（知识查询）、`chat_service.py`（对话管理）、`context_builder.py`（上下文构建），facade `ai_assistant_service.py` 保持公开 API
3. **Embedding 使用 bge-small-zh-v1.5** — 中文效果好，CPU 可跑，384 维
4. **桌面端使用 Tauri 2.x + rusqlite 离线队列** — 服务器不可达时本地缓存，恢复后自动同步
5. **实体提取采用"候选 + 人工确认"模式** — LLM 输出不直接等于正式事实

### 已知缺口

详见 [TASKS.md](TASKS.md)。最关键的：
- 后处理管线未接入实体提取和 Embedding（T1）
- 大文件需要拆分（T2）
- 9 个迁移缺少回滚脚本（T3）

### 下一步建议

1. 先做 T1（后处理管线接入），这是 Phase 2 功能能否真正生效的关键
2. T2（大文件拆分）和 T3（回滚脚本）可以并行
3. 完成后跑一次 `npm run ci` 验证

### 项目文档索引

| 文件 | 用途 |
|------|------|
| [PROJECT.md](PROJECT.md) | 项目全景 — 架构、模块、技术栈 |
| [TASKS.md](TASKS.md) | 当前任务清单 — 按优先级排序 |
| [HANDOFF.md](HANDOFF.md) | 本文件 — 交接记录 |
| [AGENTS.md](AGENTS.md) | 执行型 agent 指令 |
| [CLAUDE.md](CLAUDE.md) | 架构型 agent 指令 |
| [AI_CONFIG.md](AI_CONFIG.md) | 全局 AI 配置 |
| [docs/](docs/) | 详细文档 |
