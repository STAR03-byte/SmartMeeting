# SmartMeeting
AI Meeting Recording and Task Management System

## Quick Start

### Docker (Recommended)

```bash
docker compose up --build
```

- Frontend: `http://localhost:5174`
- Backend: `http://localhost:${BACKEND_BIND_PORT:-8000}`
- MySQL: `localhost:3307`

Default account: configured in the seed data

### Local Development

**One command (Recommended):**
```bash
npm run dev
```

This command will:

- install/update backend + frontend dependencies automatically
- start backend on `http://127.0.0.1:8000`
- start frontend on `http://127.0.0.1:5173`

**Backend:**
```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

**Frontend:**
```bash
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
# 默认代理后端地址为 http://127.0.0.1:8000
# 如需覆盖：set SMARTMEETING_DEV_BACKEND_URL=http://127.0.0.1:8000
npm --prefix frontend run dev
```

### Project Engineering Entry (Recommended)

```bash
npm run bootstrap
```

Unified commands:

```bash
npm run dev
npm run dev:backend
npm run dev:frontend
npm run ci
```

## Current Progress

### Core Features
- User auth (login/register, JWT, role-based access)
- Meeting CRUD (create, list, detail, filter, search)
- Online recording from microphone (start/pause/resume/stop then transcribe)
- Audio upload + Whisper transcription (mock ASR fallback with realistic multi-segment output)
- AI meeting summary + task extraction (real LLM or rule-based fallback)
- Task management (status transition, priority, due dates, reminder flags)
- Participant management
- Transcript viewing

### Frontend Pages
- Dashboard with stats overview and recent meetings
- Login page with JWT auth
- Meeting list with filter/search/pagination
- Meeting detail workbench (summary, transcripts, tasks, create task)
- Task center with status toggle, priority tags, meeting links
- User management with create/delete

### Engineering
- Docker Compose one-click startup (MySQL + backend + frontend)
- GitHub Actions CI (backend tests + frontend build)
- Backend test suite (33/33 passing)
- Frontend typecheck + build passing
- Project documentation (backend, frontend, docs READMEs)

### Next Steps
- Production environment configuration

## Configuration

### LLM (AI Summary & Task Extraction)

Without configuration, the system uses rule-based fallback. To enable real AI:

```bash
# .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-key
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1  # optional
LLM_FALLBACK_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TIMEOUT=60
OLLAMA_TEMPERATURE=0.3
OLLAMA_MAX_TOKENS=2000
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Whisper (Speech Recognition)

Without Whisper, the system uses mock ASR with realistic multi-segment transcripts. To enable real transcription:

```bash
# Install
pip install openai-whisper
# On Windows, also install ffmpeg: https://ffmpeg.org/download.html

# .env
WHISPER_MODEL=base
WHISPER_DEVICE=cpu  # or "cuda" for GPU
WHISPER_LANGUAGE=zh
WHISPER_HOT_WORDS=SmartMeeting,WhisperX,项目推进,接口联调
```

If you set `WHISPER_DEVICE=cuda`, make sure the host has NVIDIA Container Toolkit and a CUDA-capable PyTorch runtime available inside the container.

## Documents

- Backend API: `docs/backend-api.md`
- Frontend runbook: `docs/frontend-runbook.md`
- Database design: `docs/database-design.md`
- Engineering framework: `docs/engineering-framework.md`
- Project planning: `docs/SmartMeeting智能会议系统项目立项规划书`
