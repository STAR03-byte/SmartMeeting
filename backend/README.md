# SmartMeeting Backend

FastAPI 后端，负责会议、转写、摘要、任务提取与鉴权。

## 快速开始

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

## 入口

- `backend/main.py`：uvicorn 兼容入口
- `backend/app/main.py`：FastAPI 主应用

## 环境变量

主要配置见 `backend/app/core/config.py`，常用项：

- `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`
- `DB_BACKEND`：`mysql` 或 `sqlite`
- `DB_AUTO_FALLBACK_SQLITE`：MySQL 连接失败时是否回退 SQLite
- `SQLITE_PATH`
- `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`
- `LLM_FALLBACK_PROVIDER` / `OLLAMA_BASE_URL` / `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT` / `OLLAMA_TEMPERATURE` / `OLLAMA_MAX_TOKENS`
- `JWT_SECRET_KEY` / `JWT_ALGORITHM` / `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `WHISPER_MODEL` / `WHISPER_DEVICE` / `WHISPER_LANGUAGE`

生产环境建议：`LLM_PROVIDER=openai`，`LLM_FALLBACK_PROVIDER=ollama`，并显式填写 `JWT_SECRET_KEY` 与数据库连接信息。
如果启用 `WHISPER_DEVICE=cuda`，还需要宿主机具备 NVIDIA Container Toolkit 和 CUDA 运行时支持。

## 数据库行为

`backend/app/core/database.py` 默认优先连接 MySQL；若失败且允许回退，则自动切换到 SQLite。
开发模式下会在启动时自动建表。

## API 概览

统一前缀：`/api/v1`

- `auth`：登录、当前用户
- `users`：用户管理
- `meetings`：会议 CRUD、音频上传、转写、后处理
- `transcripts`：转写记录
- `tasks`：任务列表与状态流转
- `participants`：会议参与人

详细接口说明见：`docs/backend-api.md`

## 测试

```bash
pytest backend/tests -v
```

## 备注

- 业务逻辑放在 `app/services/`
- 路由只做薄控制器
