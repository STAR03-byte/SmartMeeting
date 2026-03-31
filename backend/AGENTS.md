# Backend AGENTS.md

`backend/` 是 SmartMeeting 的 FastAPI 服务端，提供鉴权、会议/任务 API、音频处理、转写（Whisper）以及 AI 总结/任务抽取（含回退路径）。

## STRUCTURE

```text
backend/app/
├─ api/v1/endpoints/  # Route handlers (REST endpoints)
├─ core/              # Config, DB engine, security
├─ models/            # SQLAlchemy 2.0 ORM models
├─ schemas/           # Pydantic v2 validation schemas
├─ services/          # Business logic & AI processing (ASR, LLM)
└─ main.py            # App entry & lifespan hooks
```

## WHERE TO LOOK

| Task | Location |
| :--- | :--- |
| 新增 API endpoint | `app/api/v1/endpoints/` |
| 定义 DB schema（ORM） | `app/models/` |
| 定义 API I/O（Pydantic） | `app/schemas/` |
| 新增业务逻辑 | `app/services/` |
| DB 连接 / 配置 / 安全 | `app/core/` |

## CONVENTIONS

- **路由薄、服务厚**：`endpoints/` 不直接做复杂业务或大量 DB 操作，统一下沉 `app/services/`。
- **API 版本前缀**：生产端点统一在 `/api/v1/`。
- **Model/Schema 分离**：`models/` 只做持久化；`schemas/` 只做请求/响应序列化与校验。
- **依赖注入**：数据库 Session 用 `Depends(get_db)` 获取。
- **音频存储**：当前实现写入 `backend/storage/audio/`。
- **服务层本地规则**：详见 `app/services/AGENTS.md`。

## ANTI-PATTERNS

- 不要在 `endpoints/` 内直接写 `db.query` / 大段 SQLAlchemy 查询（应放 `services/`）。
- 不要硬编码路径或配置；使用 `app/core/config.py` settings。
- 避免“胖模型”；业务逻辑放在 services。
- 不要省略服务函数参数类型标注。

## COMMANDS

在 `backend/` 目录运行：

```bash
# Development server
python -m uvicorn app.main:app --reload

# Testing
pytest tests/ -v

# Full suite (repo root)
python -m pytest backend/tests -v --tb=short
```
