# Database AGENTS.md

## OVERVIEW

`database/` 采用 SQL 脚本驱动的三段式管理：`migrations/`、`seeds/`、`rollback/`。

## STRUCTURE

```text
database/
├── migrations/   # 结构演进（001+ 按序执行）
├── seeds/        # 初始化/测试数据（可选）
├── rollback/     # 逆向回滚脚本（按版本）
└── README.md     # 执行顺序与校验 SQL
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 新增表/索引/视图/过程 | `migrations/*.sql` | 文件名保持递增编号 |
| 初始化数据 | `seeds/*.sql` | 与 schema 版本匹配 |
| 回滚路径 | `rollback/*.sql` | 与迁移一一对应 |
| 一键执行与健康检查 | `scripts/db/*.sql` | 与 README 顺序保持一致 |

## CONVENTIONS

- 先 migration，后 seed；不得跨顺序执行。
- 命名沿用 `snake_case`，时间字段维持 `created_at/updated_at`。
- 结构变更必须补对应 rollback（至少到上一个版本）。
- 性能相关变更（索引/存储过程）应附带 `EXPLAIN` 校验路径。

## ANTI-PATTERNS

- 只改 migration 不补 rollback。
- 在不同脚本里重复定义同名对象且无 drop/if exists 策略。
- 跳过 `scripts/db/check_health.sql` 就宣称 DB 变更完成。
- 把环境凭据硬编码进 SQL 或说明文档。

## COMMANDS

```bash
mysql -u <user> -p < scripts/db/run_all.sql
mysql -u <user> -p < scripts/db/check_health.sql
mysql -u <user> -p < scripts/db/check_performance.sql
mysql -u <user> -p < scripts/db/run_rollbacks.sql
```
