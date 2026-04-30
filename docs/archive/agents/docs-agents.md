# Docs AGENTS.md

`docs/` 是项目文档域：API 说明、架构/部署文档、过程与计划记录。

> 继承：根级 `AGENTS.md`（项目概览与命令）。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 文档索引 | `README.md` | 建议阅读顺序与目录说明 |
| 后端接口说明 | `backend-api.md` | `/api/v1` 端点与字段 |
| 前端联调手册 | `frontend-runbook.md` | Vite 代理/启动与常见问题 |
| 数据库设计 | `database-design.md` | 表结构、索引与过程 |
| 工程规范 | `engineering-framework.md` | 工程化与质量门禁说明 |
| 生产部署 | `deployment/production-deployment.md` | 部署步骤与注意事项 |
| 架构决策/方案 | `adr/`, `architecture/` | 设计决策与演进 |

## CONVENTIONS

- 文档以索引为中心：新增关键文档时同步更新 `docs/README.md`。
- 文档描述应指向真实入口文件/脚本（避免漂移）。

## ANTI-PATTERNS

- 不要在文档中写入密钥、token、账号密码。
- 不要复制过时的命令片段；优先引用根 `package.json` / `scripts/dev/*.py` 的真实入口。
