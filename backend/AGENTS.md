# Backend AGENTS.md

FastAPI backend for SmartMeeting providing audio transcription, AI-driven meeting summarization, and automated task extraction.

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
| Add API endpoint | `app/api/v1/endpoints/` |
| Define DB schema | `app/models/` |
| Define API I/O | `app/schemas/` |
| Add business logic | `app/services/` |
| DB connection/env | `app/core/` |

## CONVENTIONS

- **Services Layer**: Controllers (`endpoints/`) must not perform DB operations or heavy logic directly. Delegate all processing to `app/services/`.
- **API Versioning**: All production endpoints reside under `/api/v1/` prefix.
- **Model/Schema Split**: Keep `models/` strictly for DB persistence and `schemas/` for request/response serialization.
- **Dependency Injection**: Use `Depends(get_db)` for database sessions in route handlers.
- **Audio Storage**: Local development uses `storage/audio/` for raw file persistence.

## ANTI-PATTERNS

- NO `db.query` inside `endpoints/` files.
- NO hardcoded paths; use `app/core/config.py` settings.
- Avoid fat models; keep logic in services.
- DO NOT skip type hints for service function arguments.

## COMMANDS

Run from `backend/` directory:

```bash
# Development server
python -m uvicorn app.main:app --reload

# Testing
pytest tests/ -v
```
