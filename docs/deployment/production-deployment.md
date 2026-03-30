# SmartMeeting 生产部署说明

## 1. 目标

SmartMeeting 的生产部署以 Docker Compose 为主，默认包含：MySQL、Backend、Frontend。音频转写使用 Whisper 时，需要额外满足 `openai-whisper` 与 `ffmpeg` 运行条件；LLM 支持 OpenAI-compatible 主后端与 Ollama 备用后端。

## 2. 基本要求

- Docker / Docker Compose
- MySQL 8.0
- 后端容器内可用 `ffmpeg`
- 如果启用 Whisper GPU：宿主机需支持 NVIDIA Container Toolkit 与 CUDA 运行时

## 3. 环境变量

### 数据库

- `DB_ROOT_PASSWORD`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### 安全与认证

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`

### LLM

- `LLM_PROVIDER=openai`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `LLM_TEMPERATURE`
- `LLM_MAX_TOKENS`
- `LLM_TIMEOUT`
- `LLM_FALLBACK_PROVIDER=ollama`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TEMPERATURE`
- `OLLAMA_MAX_TOKENS`
- `OLLAMA_TIMEOUT`

### Whisper

- `WHISPER_MODEL=base`
- `WHISPER_DEVICE=cpu`（GPU 时可改为 `cuda`）
- `WHISPER_LANGUAGE=zh`

## 4. Docker Compose

默认 `docker-compose.yml` 已为 backend 注入上述环境变量；如使用本地 Ollama，请确保宿主机上的 Ollama 可从容器访问。

### CPU 模式

无需额外 GPU 配置。

### GPU 模式

1. 安装 NVIDIA Container Toolkit。
2. 确保容器内 CUDA 运行时可用。
3. 将 `WHISPER_DEVICE` 设置为 `cuda`。

## 5. 启动

```bash
docker compose up --build -d
```

## 6. 验证

- 后端健康检查返回 `200`
- 登录可用
- 会议上传与转写可回退到 mock ASR
- LLM 不可用时可回退到规则生成
