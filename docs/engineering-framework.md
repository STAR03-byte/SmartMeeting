# SmartMeeting Engineering Framework

## Goal

Provide a strict, repeatable engineering baseline across backend (FastAPI), frontend (Vue3/Vite), and database SQL scripts.

## Framework Boundaries

- Backend: `backend/`
- Frontend: `frontend/`
- Database assets: `database/`
- Database orchestration and checks: `scripts/db/`
- Root governance entry: `package.json` scripts

## Standardized Entry Points

### Bootstrap

```bash
npm run bootstrap
```

Installs Python backend dependencies and frontend npm dependencies with project-local npm cache.

### Daily Development

```bash
npm run dev:backend
npm run dev:frontend
```

### Quality Gates

```bash
npm run check:db:order
npm run test:backend
npm run check:frontend:type
npm run build:frontend
```

or run all together:

```bash
npm run ci
```

## CI Baseline

`.github/workflows/ci.yml` now enforces:

1. DB migration script order validation (`scripts/db/check_sql_file_order.py`)
2. Backend tests (`python -m pytest backend/tests -v --tb=short`)
3. Frontend typecheck + build

## Database Script Governance

- `scripts/db/run_all.sql` must include all SQL files in `database/migrations/` in lexical order.
- `scripts/db/check_sql_file_order.py` is the source of truth validator for this rule.
- Any new migration file requires updating `scripts/db/run_all.sql`; CI will fail otherwise.

## Non-negotiable Rules

- No direct endpoint-heavy business logic in backend routes; keep logic in `backend/app/services/`.
- No frontend build result claims without `npm --prefix frontend run typecheck` and `npm --prefix frontend run build`.
- No DB completion claims without script-level checks (`check_health.sql` and performance/ordering checks as applicable).
