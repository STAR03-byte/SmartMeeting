# TASKS.md — 协作任务清单

> 本文件是 Claude 和 Codex 的协作接口。
>
> **分工：**
> - Claude 负责分析现状、决定做什么、拆分任务、写任务规格
> - Codex 负责按规格实现、更新任务状态、写完成报告
>
> **流程：** Claude 写规格 → Codex 认领 → Codex 实现 → Codex 写报告 → Claude 审查

**最后更新：** 2026-05-12
**当前分支：** main (v3.0.0)

---

## 任务状态说明

| 状态 | 含义 |
|------|------|
| `待认领` | Claude 已写好规格，Codex 可以开始 |
| `进行中` | Codex 已认领，正在实现 |
| `待审查` | Codex 已完成，等 Claude 审查 |
| `已完成` | Claude 审查通过，已合并 |
| `已阻塞` | 依赖其他任务或有未解决的问题 |

---

## P0 — 必须做

### T1: 后处理管线接入实体提取和 Embedding

**状态：** `已完成`
**实际完成：** `job_manager.py` 第 357-421 行已接入实体提取（`extract_entities`）和 Embedding（`encode_single`/`encode_texts`），在 v3.0 之前已实现。

---

### T2: 大文件拆分

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

拆分 3 个超大文件，仅拆分文件结构，不改业务逻辑。公开 API 保持不变。

**2a. `test_api.py` (2675 行) → 按功能域拆分**

拆分为以下文件（行数为估算）：
- `test_meetings_api.py` (~800 行) — 会议 CRUD、上传、转写、摘要相关测试
- `test_tasks_api.py` (~400 行) — 任务 CRUD、分配、状态相关测试
- `test_auth_api_extended.py` (~300 行) — 认证、权限、token 相关测试
- `test_teams_api_extended.py` (~300 行) — 团队、成员、邀请相关测试
- `test_api_misc.py` (~200 行) — 健康检查、配置、杂项测试
- `test_api.py` 保留为入口，只 import 上述模块（或直接删除，由 conftest 统一）

移动时保持 test 函数名不变，保持 conftest 的 fixture 使用方式不变。

**2b. `meeting_service.py` (691 行) → 提取子模块**

- `meeting_lifecycle.py` — 开始会议、结束会议、状态流转、删除
- `meeting_content.py` — 转写管理、摘要生成、导出
- `meeting_service.py` — 保留为 facade，re-export 公开 API

所有 import 路径不变（通过 `meeting_service.py` re-export）。

**2c. `llm/client.py` (688 行) → 提取子模块**

- `provider_chain.py` — provider 选择、fallback 链、健康检查
- `streaming.py` — 流式响应处理
- `client.py` — 保留为 facade

**要改的文件：** 仅上述目标文件
**不要改的文件：** 业务逻辑、API 端点、Schema

**验收标准：**
- [ ] 每个新文件 < 800 行
- [ ] `npm run ci` 全部通过
- [ ] 所有现有 import 路径仍然有效
- [ ] 无功能回归

**Codex 完成报告：**（完成后填写）
```
- 改了什么：
- 测试结果：
- 遗留问题：
```

---

### T3: 补齐迁移回滚脚本

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

为以下 9 个迁移创建回滚脚本，放在 `database/rollback/` 下：

| 迁移 | 回滚文件名 | 操作 |
|------|-----------|------|
| 020 | `rollback_020_team_invitations.sql` | DROP TABLE team_invitations |
| 021 | `rollback_021_conversations.sql` | DROP TABLE conversation_messages; DROP TABLE conversations |
| 022 | `rollback_022_conversation_messages.sql` | DROP TABLE conversation_messages |
| 024 | `rollback_024_processing_jobs.sql` | DROP TABLE processing_jobs |
| 025 | `rollback_025_llm_usage.sql` | DROP TABLE llm_usage |
| 027 | `rollback_027_hotwords_user_id.sql` | 还原 user_id 类型 |
| 028 | `rollback_028_meeting_audios.sql` | DROP TABLE meeting_audios |
| 029 | `rollback_029_team_tables_types.sql` | 还原类型修改 |
| 030 | `rollback_030_tsvector.sql` | DROP COLUMN search_vector |

每个回滚脚本只做 DROP 或 ALTER COLUMN，不删除其他表的数据。

**验收标准：**
- [ ] `npm run check:db:order` 通过
- [ ] 回滚脚本语法正确（可用 psql 验证）

**Codex 完成报告：**（完成后填写）
```
- 改了什么：
- 测试结果：
- 遗留问题：
```

---

## P1 — 应该做

### T4: 清理根目录临时文件

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

删除根目录的 3 个临时文件：
- `backend-run.err` (207KB)
- `frontend-run.err` (211B)
- `dev-one-command.err` (323B)

确认 `.gitignore` 包含 `*.err` 规则。如果没有，添加。

**验收标准：**
- [ ] 3 个文件已删除
- [ ] `.gitignore` 包含 `*.err`

---

### T5: 更新过时的 AI_CONFIG.md

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

更新 `AI_CONFIG.md` 中的过时内容：
1. 第 28 行：`数据库：MySQL（`database/``）` → `数据库：PostgreSQL 16 + pgvector（`database/``）`
2. 第 50-61 行的"推荐实现顺序（MVP）"：更新为当前阶段的开发重点，参考 PROJECT.md 的架构原则

**验收标准：**
- [ ] 不再引用 MySQL
- [ ] 推荐顺序反映当前 v3.0 阶段

---

### T6: Embedding 服务集成验证

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

在 `test_embedding_service.py` 中补充 3 个测试：

1. **mock 模型生成向量** — mock `sentence-transformers` 的 encode 方法，验证返回 384 维浮点数组
2. **写入 pgvector** — 使用 SQLite 兼容的方式验证 embedding 存储逻辑
3. **搜索命中** — 验证 `vector_store.search()` 能返回相似度最高的结果

同时在 `job_manager.py` 的 Embedding 生成处添加 `logger.info()` 输出，记录生成了多少条 embedding。

**验收标准：**
- [ ] 新测试通过
- [ ] Embedding 生成有日志输出

---

### T7: 搜索 API 测试补全

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

扩充 `test_search_api.py`（当前 34 行），补充以下测试场景：

1. **语义搜索命中** — 预置 embedding 数据，搜索相似内容，验证返回结果
2. **权限过滤** — 用户 A 的会议不应出现在用户 B 的搜索结果中
3. **混合查询** — 同时包含语义匹配和关键词匹配的结果
4. **空查询** — 验证空字符串返回空结果（已有，确认保留）
5. **分页** — 验证 limit/offset 参数生效

使用 conftest 中的 `auth_client` fixture，mock embedding_service。

**验收标准：**
- [ ] 至少 5 个测试用例
- [ ] 全部通过

---

## P2 — 可以做

### T8: 桌面端前端组件验证

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

验证 `frontend/src/desktop/` 下 4 个组件的 Tauri invoke 调用是否与 `desktop/src-tauri/src/lib.rs` 中注册的命令匹配：

| 组件 | 需要验证的 invoke |
|------|------------------|
| RecordingControls.vue | `start_meeting_session`, `sync_transcript`, `stop_meeting_session` |
| MeetingHistory.vue | `get_meeting_session_status` |
| SettingsView.vue | `update_whisper_config`, `get_whisper_config`, `set_server_config` |
| DesktopLayout.vue | 路由和布局，无 invoke |

逐一检查 invoke 调用的参数名和类型是否与 Rust 端的 `#[tauri::command]` 函数签名一致。不匹配的记录在报告中。

**验收标准：**
- [ ] 每个组件的 invoke 调用与 Rust 端签名一致
- [ ] 不匹配的地方有明确记录

---

### T9: E2E 测试框架搭建

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

搭建 Playwright E2E 测试框架：

1. 安装 `@playwright/test`（如未安装）
2. 创建 `e2e/` 目录
3. 编写第一个测试：`e2e/auth.spec.ts`
   - 打开登录页
   - 输入用户名密码
   - 验证跳转到 Dashboard
4. 创建 `playwright.config.ts`
5. 在 `package.json` 添加 `"test:e2e": "playwright test"` 脚本

**验收标准：**
- [ ] `npx playwright test e2e/auth.spec.ts` 可运行（不要求通过，框架搭建即可）

---

### T10: i18n 字符串清理

**状态：** `待认领`
**分支：** （认领后填写）

**Claude 规格：**

1. 运行 `scripts/dev/extract_i18n.py` 提取代码中实际使用的 i18n key
2. 与 `frontend/src/locales/zh-CN.ts` 和 `en-US.ts` 对比，找出未使用的 key
3. 删除未使用的 key
4. 确认 `npm run check:frontend:type` 通过

**验收标准：**
- [ ] 未使用的 key 已清理
- [ ] 类型检查通过

---

## 已完成（归档）

| 版本 | 任务 | 提交 |
|------|------|------|
| v2.0 | PostgreSQL 迁移 + pgvector | 43c3f6b |
| v2.0 | 迁移脚本重写 | 3902f21 |
| v2.0 | AI 服务拆分 | 99c00c7 |
| v2.0 | 工程体系收敛 | 151cca7 ~ 722505b |
| v2.5 | 跨会议语义搜索 | b38de02 |
| v2.5 | 决策/承诺提取与确认 | 47f07ab ~ 4541f5c |
| v2.5 | 承诺追踪 + 主题抽取 | 3584a6a |
| v2.5 | AI 助手知识增强 | 468b533 |
| v3.0 | 桌面端基础 + 会话管理 | 784ec01 ~ a86616a |
| v3.0 | 桌面端 UI + 跨平台 CI | d0e81dd ~ 7522a42 |
| v3.0 | Web 端响应式适配 | d7d1cc8 |
