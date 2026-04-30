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

### 路由层 (endpoints/)
- **路由薄、服务厚**：`endpoints/` 不直接做复杂业务或大量 DB 操作，统一下沉 `app/services/`。
- **API 版本前缀**：生产端点统一在 `/api/v1/`。
- **依赖注入**：数据库 Session 用 `Depends(get_db)` 获取。
- endpoint 只做：参数解析/校验、`Depends(...)` 注入、调用 `app/services/`、返回 schema。

### 服务层 (services/)
- 服务函数必须有完整类型标注，返回类型可读且稳定。
- 事务边界收敛在服务层：写操作统一 `add/commit/refresh`，避免分散提交。
- 外部能力（LLM/Whisper）必须提供 fallback 或可观测失败路径，不吞异常。
- 命名遵循动作语义：`create_*`, `list_*`, `generate_*`, `build_*`, `extract_*`。

### 模型/Schema
- **Model/Schema 分离**：`models/` 只做持久化；`schemas/` 只做请求/响应序列化与校验。
- **音频存储**：当前实现写入 `backend/storage/audio/`。

## ANTI-PATTERNS

### 路由层
- 不要在 `endpoints/` 内直接写 `db.query` / 大段 SQLAlchemy 查询（应放 `services/`）。
- 不要在 endpoint 内做跨领域编排（如”上传→转写→后处理→任务生成”链路），应在 service 层提供单入口。
- 不要硬编码路径或配置；使用 `app/core/config.py` settings。

### 服务层
- 避免”胖模型”；业务逻辑放在 services。
- 不要省略服务函数参数类型标注。
- 用 `Any` 或弱类型返回值掩盖 schema/model 不一致。
- LLM 调用失败后直接静默成功（必须返回 fallback 来源标识）。
- 跨函数隐式提交事务（导致部分写入不可控）。

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
