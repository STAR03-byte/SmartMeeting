# Scripts AGENTS.md

`scripts/` 放置工程化脚本（Python/SQL 编排），用于开发自检、DB 顺序校验与一键初始化依赖。

> 继承：根级 `AGENTS.md`（全局规则与命令入口）。

## STRUCTURE

```text
scripts/
├── db/     # DB 执行编排与校验（run_all.sql + order check）
├── dev/    # 开发自检/冒烟/依赖安装（qa.py/bootstrap.py/smoke.py）
└── *.py    # 少量一次性文档/模板生成脚本
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 一键质量门禁 | `dev/qa.py` | 串行跑 backend tests + frontend typecheck/build（可选 smoke） |
| 安装开发依赖 | `dev/bootstrap.py` | pip + npm install（Windows 兼容 npm.cmd） |
| DB 迁移顺序校验 | `db/check_sql_file_order.py` | 对齐 `run_all.sql` 与 `database/migrations/` |
| DB 一键初始化 | `db/run_all.sql` | migration + seeds |

## CONVENTIONS

- 脚本必须可在 repo root 运行（`cwd` 由脚本自行处理）。
- 失败必须返回非 0 exit code；不要吞异常。

## ANTI-PATTERNS

- 不要把 secrets 写进脚本或输出日志。
- 不要让脚本隐式修改大量文件（除非明确是生成器脚本，并在文档中说明）。
