# Scripts DB AGENTS.md

`scripts/db/` 提供数据库执行编排与校验脚本：通过 `SOURCE` 组合迁移/种子，并在 CI 中校验迁移顺序一致性。

> 继承：`database/AGENTS.md`（数据库管理约定）。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 一键初始化 | `run_all.sql` | `SOURCE database/migrations/*.sql` 后再 `SOURCE database/seeds/*.sql` |
| 顺序一致性校验 | `check_sql_file_order.py` | 比对 `run_all.sql` 的 migration SOURCES 与 `database/migrations/` 文件名排序 |
| 健康检查 | `check_health.sql` | 基础表/视图/过程检查 |
| 性能检查 | `check_performance.sql` | EXPLAIN/索引相关校验 |
| 回滚编排 | `run_rollbacks.sql` | 串行执行 rollback 脚本 |

## CONVENTIONS

- `run_all.sql` 的 migration SOURCES 必须与 `database/migrations/*.sql` 文件名排序完全一致（CI 强制）。
- seed 允许可选，但必须在 migrations 之后。

## ANTI-PATTERNS

- 只新增 migration 文件但忘记更新 `run_all.sql`（会导致 CI 失败）。
- 在 SQL/脚本中硬编码 DB 凭据。
