# skills-main AGENTS.md

## OVERVIEW

`skills-main/` 是外部技能仓，包含多种技能定义与配套脚本（docx/pptx/xlsx/pdf 等）。

## STRUCTURE

```text
skills-main/
├── skills/                     # 各技能目录（含 SKILL.md、脚本、模板）
├── scripts/                    # 仓级脚本
├── README.md
└── THIRD_PARTY_NOTICES.md
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 修改某个技能行为 | `skills/<skill-name>/SKILL.md` | 优先就地最小改动 |
| 技能脚本修复 | `skills/<skill-name>/scripts/` | 保持现有输入输出契约 |
| 技能级依赖 | `skills/<skill-name>/requirements.txt` | 仅在必要时变更 |

## CONVENTIONS

- 该目录与主业务（backend/frontend/database）解耦；避免跨域引用主工程代码。
- 优先修复目标技能，不做整仓统一重构。
- 资源型文件（schema/template/fonts）视为稳定资产，修改需明确影响范围。

## ANTI-PATTERNS

- 在 `skills-main/` 中引入对主工程私有路径的硬依赖。
- 未验证下游技能脚本即批量替换模板/数据。
- 为“风格统一”重写大量历史技能文档。

## COMMANDS

```bash
# 按目标技能进入后执行（示例）
python -m pip install -r skills-main/skills/<skill-name>/requirements.txt
```
