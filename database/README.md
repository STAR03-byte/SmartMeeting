# SmartMeeting 数据库模块说明

本目录用于管理 SmartMeeting 的 PostgreSQL 16 数据库结构、种子数据和后续迁移。

## 目录说明

- `migrations/`: 建表与结构演进脚本（PostgreSQL 语法）
- `seeds/`: 初始化测试数据脚本
- `rollback/`: 回滚脚本（按版本逆向回退）
- `backups/`: 备份文件目录（不建议提交大体积备份）

## 技术栈

- PostgreSQL 16 + pgvector 扩展
- tsvector + GIN 索引（全文搜索预埋，Phase 2 使用）
- 测试环境可回退 SQLite（`DB_AUTO_FALLBACK_SQLITE=true`）

## 初始化顺序

按以下顺序执行（共 30 个迁移文件）：

1. `database/migrations/001_init_smartmeeting.sql` — 核心表 + `fn_set_updated_at()` 触发器函数
2. `database/migrations/002_enhance_smartmeeting.sql` — CHECK 约束、视图、completed_at 触发器
3. `database/migrations/003_sp_task_query.sql` — `sp_list_tasks_by_user()` 函数
4. `database/migrations/004_indexes_perf.sql` — 性能索引
5. `database/migrations/005_audit_and_participants.sql` — 审计日志 + 参与者表
6. `database/migrations/006_collaboration_share_fields.sql` — 协作字段
7. `database/migrations/007_fix_meeting_audio_cascade.sql` — 级联修复
8. `database/migrations/008_participant_unique_guard.sql` — 唯一约束
9. `database/migrations/009_extend_audit_logs_for_auth_events.sql` — 认证审计
10. `database/migrations/010_speaker_fields.sql` — 说话人字段
11. `database/migrations/011_hotwords_table.sql` — 热词表
12. `database/migrations/012_create_teams.sql` — 团队表
13. `database/migrations/013_create_team_members.sql` — 团队成员表
14. `database/migrations/014_add_team_id_to_meetings.sql` — 会议关联团队
15. `database/migrations/015_add_role_to_participants.sql` — 参与者角色
16. `database/migrations/016_clear_test_data.sql` — 清理测试数据
17. `database/migrations/018_create_team_invite_links.sql` — 团队邀请链接
18. `database/migrations/030_add_tsvector_columns.sql` — tsvector 预埋（Phase 2）

种子数据（可选）：

- `database/seeds/001_seed_basic_data.sql`
- `database/seeds/002_seed_participants.sql`

也可直接一键执行:

- `scripts/db/run_all.sql`

## 执行命令示例

```bash
# 单个迁移
psql -U <user> -d smartmeeting -f database/migrations/001_init_smartmeeting.sql

# 一键执行所有迁移
psql -U <user> -d smartmeeting -f scripts/db/run_all.sql

# Docker 方式（推荐）
docker compose up --build
```

## 校验建议

```sql
-- 查看所有表
\dt

-- 查看所有视图
\dv

-- 查看触发器
SELECT tgname, tgrelid::regclass FROM pg_trigger WHERE NOT tgisinternal;

-- 查看函数
\df

-- 查看索引
\di

-- 查看 tsvector 索引
SELECT indexname, tablename FROM pg_indexes WHERE indexname LIKE '%search_vector%';

-- 测试视图
SELECT * FROM v_meeting_overview LIMIT 10;
SELECT * FROM sp_list_tasks_by_user(1, NULL);

-- 测试全文搜索（Phase 2）
SELECT * FROM meetings WHERE search_vector @@ plainto_tsquery('simple', '测试');
```

## 回滚说明

回滚脚本位于 `database/rollback/`，按版本逆序执行:

```bash
psql -U <user> -d smartmeeting -f database/rollback/rollback_030_to_029.sql
psql -U <user> -d smartmeeting -f database/rollback/rollback_029_to_028.sql
# ... 依此类推
```
