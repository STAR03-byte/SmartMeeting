# ui-ux-pro-max-skill-main AGENTS.md

## OVERVIEW

`ui-ux-pro-max-skill-main/` 是 UI/UX 能力仓：`src/ui-ux-pro-max/` 为 source of truth，`cli/` 为安装器分发层。

## STRUCTURE

```text
ui-ux-pro-max-skill-main/
├── src/ui-ux-pro-max/   # 数据/脚本/模板源
├── cli/                 # npm CLI（uipro-cli）与 assets 打包
├── .claude-plugin/      # 市场发布相关
├── .claude/ / .factory/ # 本地技能适配
└── CLAUDE.md            # 本目录专用规则
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 规则/数据更新 | `src/ui-ux-pro-max/data/` | 先改源，再考虑同步 |
| 搜索/生成逻辑 | `src/ui-ux-pro-max/scripts/` | `search.py` 为入口 |
| 平台模板 | `src/ui-ux-pro-max/templates/` | 基础模板 + 平台模板分层 |
| CLI 行为 | `cli/src/` | 模板渲染与 init 命令 |

## CONVENTIONS

- Source of truth 在 `src/ui-ux-pro-max/`，不要直接把 `cli/assets/` 当主编辑目标。
- 涉及发布前同步时，按 CLAUDE.md 的 `cp -r` 顺序同步 data/scripts/templates。
- 不直接 push 到 `main`，保持分支 + PR 流程。

## ANTI-PATTERNS

- 仅改 `cli/assets/*` 而不改 `src/ui-ux-pro-max/*`。
- 跳过本地构建/安装验证就声明 CLI 可用。
- 在该目录混入 SmartMeeting 主业务代码改动。

## COMMANDS

```bash
# 搜索引擎示例
python3 src/ui-ux-pro-max/scripts/search.py "dashboard" --domain chart

# CLI 构建（在 cli/ 目录）
bun run build
```
