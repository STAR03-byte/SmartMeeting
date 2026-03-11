# AGENTS.md

This document defines build/test commands and coding conventions for agentic coding tools
working in `D:\SmartMeeting`.

## Repository Status

- Current repo is mostly scaffold-level (limited source code committed so far).
- Stack target: FastAPI + Vue 3 + MySQL + Whisper + LLM.
- Follow existing structure and extend it incrementally; do not regenerate whole modules.

## Project Structure (Expected)

```text
SmartMeeting/
├─ backend/                 # FastAPI service
│  ├─ app/
│  │  ├─ api/               # Route handlers
│  │  ├─ models/            # Pydantic schemas / ORM models
│  │  ├─ services/          # Business logic
│  │  └─ utils/             # Helpers
│  ├─ tests/
│  ├─ main.py
│  └─ requirements.txt
├─ frontend/                # Vue 3 + TypeScript app
│  ├─ src/
│  │  ├─ api/
│  │  ├─ components/
│  │  ├─ stores/
│  │  └─ views/
│  └─ package.json
├─ database/                # SQL scripts / migrations
└─ docs/
```

## Build, Lint, Test Commands

Use these commands from repository root unless noted otherwise.

### Backend (FastAPI / Python)

```bash
# install
python -m pip install -r backend/requirements.txt

# run dev server
python -m uvicorn backend.main:app --reload

# run all tests
pytest backend/tests -v

# run single test file
pytest backend/tests/test_meeting_api.py -v

# run single test case
pytest backend/tests/test_meeting_api.py::TestMeetingAPI::test_create_meeting -v

# lint / format / type-check
ruff check backend/app backend/tests
black backend/app backend/tests
isort backend/app backend/tests
mypy backend/app
```

### Frontend (Vue 3 / TypeScript)

```bash
# install
npm --prefix frontend install

# dev / build / preview
npm --prefix frontend run dev
npm --prefix frontend run build
npm --prefix frontend run preview

# tests
npm --prefix frontend run test:unit

# run single unit test file (Vitest)
npm --prefix frontend run test:unit -- src/components/__tests__/MeetingList.spec.ts

# lint / type-check / format
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run format
```

### Database (MySQL)

```bash
# example local migration execution
mysql -u <user> -p <database> < database/init.sql
```

If Alembic or another migration tool is added later, document and prefer that flow.

## Code Style Guidelines

## 1) General

- Keep changes minimal and localized; edit existing files first.
- Avoid broad refactors unless required by the task.
- Keep functions focused; extract complex logic into services/utilities.
- Do not hardcode secrets, tokens, or connection strings.

## 2) Python / FastAPI

- **Formatting**: Black defaults, max line length 88 unless project config says otherwise.
- **Imports**: stdlib, third-party, local modules (grouped with blank lines).
- **Naming**:
  - modules/functions/variables: `snake_case`
  - classes: `PascalCase`
  - constants: `UPPER_SNAKE_CASE`
- **Types**:
  - add type hints for public functions and service interfaces.
  - prefer explicit return types.
  - use Pydantic models for request/response contracts.
- **API design**:
  - use dependency injection for DB/session/auth where possible.
  - validate inputs at schema level first.
  - keep route handlers thin; move logic to `services/`.
- **Error handling**:
  - raise `HTTPException` with accurate status code and actionable detail.
  - do not swallow exceptions silently.
  - log internal errors with context; avoid leaking sensitive internals.

## 3) Vue 3 / TypeScript

- Use `<script setup lang="ts">` and Composition API.
- **Naming**:
  - components: `PascalCase.vue`
  - composables: `useXxx.ts`
  - utilities and variables: `camelCase`
  - CSS classes: `kebab-case`
- **Types**:
  - type all props/emits/API payloads.
  - avoid `any`; prefer explicit interfaces/types.
- **State**:
  - keep global state in Pinia stores.
  - avoid duplicating server state across unrelated components.
- **Error handling**:
  - handle API errors in a user-visible and recoverable way.
  - avoid empty `catch` blocks.

## 4) MySQL / Data

- Table and column names use `snake_case`.
- Standard timestamp fields: `created_at`, `updated_at`.
- Prefer migrations over manual schema edits in production workflows.
- Add indexes for high-frequency filters/joins.

## 5) Testing Guidelines

- Add/adjust tests for behavior changes.
- Keep tests deterministic and isolated.
- For bug fixes, include a regression test that fails before and passes after fix.
- Prefer one focused assertion block per scenario.

## 6) Git & PR Conventions

- Commit types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
- Example: `feat(meeting): add meeting summary endpoint`.
- Commit after each coherent change and push promptly.
- Do not rewrite shared history unless explicitly requested.

## 7) Agent-Specific Rules

- Always check for existing conventions before introducing new patterns.
- If command/tooling differs from this file, follow actual project config files first.
- When commands fail due to missing files (common in early scaffold), report clearly and
  propose the minimal setup needed.

## Cursor / Copilot Rules Discovery

- Checked `.cursor/rules/`: not found.
- Checked `.cursorrules`: not found.
- Checked `.github/copilot-instructions.md`: not found.
- If these files are added later, merge their rules into this document and prioritize
  repository-specific instructions over generic guidance.
