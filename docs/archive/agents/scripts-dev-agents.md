# Scripts Dev AGENTS.md

`scripts/dev/` 是本地工程化入口：依赖安装、质量门禁与关键路径冒烟。

> 继承：根级 `AGENTS.md`（全局命令） + `scripts/AGENTS.md`（脚本约定）。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 安装开发依赖 | `bootstrap.py` | `pip install -r backend/requirements.txt` + `npm --prefix frontend install` |
| 质量门禁 | `qa.py` | backend tests + frontend typecheck/build；Windows 下自动解析 npm.cmd |
| 冒烟链路 | `smoke.py` | 会议全生命周期关键用例（pytest 单测选择性执行） |

## COMMANDS

```bash
python scripts/dev/bootstrap.py
python scripts/dev/qa.py
python scripts/dev/qa.py --smoke
```

## CONVENTIONS

- `qa.py` 是本地复现 CI 的首选入口；新增工程门禁优先落在此脚本。

## ANTI-PATTERNS

- 不要让脚本依赖本机固定路径（除 npm cache 由脚本创建管理）。
