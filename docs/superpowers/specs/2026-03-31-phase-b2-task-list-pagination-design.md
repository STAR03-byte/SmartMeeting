# Phase B-2 Design: Task list pagination + total (2026-03-31)

## Context

Phase B aims to enhance business capabilities. Phase B-1 has already updated meeting list pagination by changing `GET /api/v1/meetings` to return `{ items, total }`, enabling the frontend to show accurate pagination.

The task center currently supports filtering (assignee/meeting/status/priority/keyword) but **does not support pagination** at the API contract level (it returns a plain array). This is inconsistent with the meeting list and blocks scalable task browsing.

## Goals

1. Align `GET /api/v1/tasks` with the meeting list contract: return a stable object shape `{ items, total }`.
2. Add pagination parameters `limit`/`offset` (and keep existing filters).
3. Add sorting support in a minimal, explicit way.
4. Update frontend task API wrapper and `TasksView.vue` to use pagination UI.
5. Update tests and `docs/backend-api.md` to reflect the new contract.

## Non-Goals

- No batch operations (bulk status update) in this phase.
- No new task fields or schema changes.
- No global axios interceptor changes; frontend errors continue to use existing `notifyApiError` where appropriate.

## API Contract

### Endpoint

`GET /api/v1/tasks`

### Query params

- Existing (keep):
  - `assignee_id?: int`
  - `meeting_id?: int`
  - `status?: TaskStatus`
  - `priority?: TaskPriority`
  - `keyword?: string`
- New:
  - `limit?: int` (1..100)
  - `offset?: int` (>=0)
  - `sort_by?: string` (optional; see below)

### sort_by values (minimal set)

- default: `id_desc` (current behavior)
- `due_at_asc` (nulls last)
- `due_at_desc` (nulls last)

### Response

Change from `TaskOut[]` to:

```json
{
  "items": [ /* TaskOut[] */ ],
  "total": 123
}
```

`total` is computed with the same filters applied but **without** `limit/offset`.

## Backend Design

### Schemas

- Add `TaskListOut` (Pydantic) with:
  - `items: list[TaskOut]`
  - `total: int`

### Service layer

- Extend `task_service.list_tasks(...)` to accept `sort_by`, `limit`, `offset` and apply:
  - filters first
  - ordering
  - `offset` then `limit`
- Add `task_service.count_tasks(...)` with the same filters to compute `total`.

### Endpoint

- Update `backend/app/api/v1/endpoints/tasks.py`:
  - `response_model=TaskListOut`
  - accept new query params
  - call `count_tasks(...)` and `list_tasks(...)`
  - return `TaskListOut(items=[...], total=...)`

## Frontend Design

### API wrapper

- Add `TaskListResult` type `{ items: TaskItem[]; total: number }`.
- Update `getTasks()` to return `Promise<TaskListResult>` and include new params:
  - `limit`, `offset`, `sortBy`

### TasksView

- Add pagination state:
  - `currentPage`, `pageSize`, `totalCount`
- Modify `refreshTasks()` to send `limit/offset` and update `tasks` + `totalCount`.
- Add an optional sort selector (minimal: default, due date asc/desc).
- Behavior:
  - Changing filters resets to page 1.
  - Changing page triggers `refreshTasks()`.

## Tests

### Backend

- Update existing task list tests (if any) to assert `{items,total}`.
- Add/extend tests for:
  - `limit/offset` returns correct item count while `total` remains the filtered total.
  - sorting by `due_at` behavior.

### Frontend

- Update `frontend/src/api/tasks.test.ts` to mock `{items,total}`.
- Add tests for query serialization of `limit/offset/sort_by`.

## Docs

- Update `docs/backend-api.md` section `GET /api/v1/tasks`:
  - response type and example payload
  - new query params

## Rollout / Compatibility

This is a breaking change for any client expecting `TaskOut[]` from `GET /api/v1/tasks`. We will update the built-in frontend accordingly in the same PR.

## Verification

- `python -m pytest backend/tests -v --tb=short`
- `python scripts/dev/qa.py --smoke`
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`
- `npx --prefix frontend vitest run`
