# SmartMeeting
AI Meeting Recording and Task Management System

## Quick Start

### Backend

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

### Frontend

```bash
npm --prefix frontend install --cache "D:\SmartMeeting\.npm-cache"
npm --prefix frontend run dev
```

### Docker

```bash
copy .env.example .env
docker compose up --build
```

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

## Current MVP Progress

- Backend core CRUD ready (users/meetings/transcripts/tasks/participants)
- Audio upload + mock ASR transcription ready
- Meeting postprocess ready (summary + task extraction, idempotent and force-regenerate)
- Task status transition with validation and `completed_at` auto-management ready
- Frontend dashboard/detail pages ready for end-to-end local integration

## Documents

- Backend API: `docs/backend-api.md`
- Frontend runbook: `docs/frontend-runbook.md`
- Project planning: `docs/项目立项规划书.md`
- Database design: `docs/database-design.md`
