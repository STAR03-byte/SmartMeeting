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

## 4. 生产部署资产位置

- 生产环境变量模板：`.env.prod.example`
- 生产 Compose 编排：`infrastructure/compose/docker-compose.prod.yml`
- 生产 Nginx 配置：`infrastructure/nginx/nginx.prod.conf`
- K8s 模板：
  - `infrastructure/k8s/configmap.yml`
  - `infrastructure/k8s/deployment.yml`
  - `infrastructure/k8s/service.yml`

如使用本地 Ollama，请确保宿主机上的 Ollama 可从容器访问。

## 5. Docker Compose（生产）

1. 复制环境变量模板并填写生产值：

```bash
cp .env.prod.example .env.prod
```

2. 解析配置并确认无误：

```bash
docker compose --env-file .env.prod -f infrastructure/compose/docker-compose.prod.yml config
```

### CPU 模式

无需额外 GPU 配置。

### GPU 模式

1. 安装 NVIDIA Container Toolkit。
2. 确保容器内 CUDA 运行时可用。
3. 将 `WHISPER_DEVICE` 设置为 `cuda`。

## 6. 启动

```bash
docker compose --env-file .env.prod -f infrastructure/compose/docker-compose.prod.yml up --build -d
```

## 7. 验证

- 后端健康检查返回 `200`
- 登录可用
- 会议上传与转写可回退到 mock ASR
- LLM 不可用时可回退到规则生成

## 8. K8s 生产建议

`infrastructure/k8s/` 提供最小可用模板：

- `configmap.yml`: 非敏感配置（数据库主机、模型参数、限流阈值）
- `deployment.yml`: backend/frontend/nginx 的副本数、探针、资源请求与限制
- `service.yml`: 服务暴露策略（`smartmeeting-nginx` 使用 `LoadBalancer`）

> 生产环境需要额外创建 Secret（仓库不提交密钥），至少包括：
>
> - `smartmeeting-db-secret`: `db-user`, `db-password`
> - `smartmeeting-app-secret`: `jwt-secret`, `llm-api-key`

可按以下顺序部署：

```bash
kubectl apply -f infrastructure/k8s/configmap.yml
kubectl apply -f infrastructure/k8s/deployment.yml
kubectl apply -f infrastructure/k8s/service.yml
```

部署后建议检查：

```bash
kubectl get pods
kubectl get svc
kubectl describe deployment smartmeeting-backend
```
