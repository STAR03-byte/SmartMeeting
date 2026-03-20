# SmartMeeting
AI Meeting Recording and Task Management System

## Quick Start

### Docker (Recommended)

```bash
docker compose up --build
```

- Frontend: `http://localhost:5174`
- Backend: `http://localhost:8000`
- MySQL: `localhost:3307`

Default account: `alice_admin` / `admin123`

### Local Development

**Backend:**
```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

**Frontend:**
```bash
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
npm --prefix frontend run dev
```

## Current Progress

### Core Features
- User auth (login/register, JWT, role-based access)
- Meeting CRUD (create, list, detail, filter, search)
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
- Real LLM integration (set LLM_API_KEY in .env)
- Whisper ASR production deployment (install ffmpeg + openai-whisper)
- Deployment documentation
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
```

## Documents

- Backend API: `docs/backend-api.md`
- Frontend runbook: `docs/frontend-runbook.md`
- Database design: `docs/database-design.md`
- Project planning: `docs/SmartMeeting智能会议系统项目立项规划书`
