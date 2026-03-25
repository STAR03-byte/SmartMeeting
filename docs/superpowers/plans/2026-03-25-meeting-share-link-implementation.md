# SmartMeeting Meeting Share Link Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add login-required share links for meetings so users can copy a share URL from meeting detail, open a read-only shared page, and return to that page after login.

**Architecture:** Keep the current authenticated app flow intact and add a separate share route backed by a dedicated read-only API. Generate or reuse an opaque share token on the backend, expose a shared-meeting aggregate response, and let the frontend compose the full share URL while preserving `redirect` across login.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic, pytest, Vue 3, TypeScript, Pinia, Element Plus

---

## File Structure and Responsibilities

### Backend

- Create: `database/migrations/006_meeting_share_links.sql`
  - Add `share_token` and `shared_at` to `meetings`
- Create: `database/rollback/rollback_006_to_005.sql`
  - Remove share-link columns/index cleanly
- Modify: `backend/app/models/meeting.py`
  - Add share fields to ORM model
- Modify: `backend/app/schemas/meeting.py`
  - Add share-create response and shared-meeting response schemas
- Modify: `backend/app/services/meeting_service.py`
  - Generate/reuse share token and build shared-meeting payload
- Modify: `backend/app/api/v1/endpoints/meetings.py`
  - Add `POST /api/v1/meetings/{id}/share`
- Create: `backend/app/api/v1/endpoints/shared_meetings.py`
  - Add `GET /api/v1/shared/meetings/{token}`
- Modify: `backend/app/api/v1/router.py`
  - Register shared-meetings router
- Modify: `backend/tests/test_api.py`
  - Cover share creation, invalid token, read-only payload, and no-summary failure

### Frontend

- Modify: `frontend/src/api/types.ts`
  - Add share response and shared-meeting types
- Modify: `frontend/src/api/meetings.ts`
  - Add `createMeetingShareLink()` and `getSharedMeeting()` wrappers
- Modify: `frontend/src/router/index.ts`
  - Preserve `redirect` on login-required navigation
  - Register `/shared/meetings/:token`
- Modify: `frontend/src/views/LoginView.vue`
  - Redirect to safe `redirect` target after login
- Modify: `frontend/src/views/MeetingDetailView.vue`
  - Add share-link generation/copy action
- Create: `frontend/src/views/SharedMeetingView.vue`
  - Render read-only shared meeting content
- Modify: `frontend/src/stores/meetingStore.ts` only if needed for reuse

### Docs

- Modify: `docs/backend-api.md`
  - Document share endpoints and response shapes
- Modify: `docs/frontend-runbook.md`
  - Document share page and login redirect behavior

---

## Chunk 1: Backend schema and persistence

### Task 1: Add meeting share columns

**Files:**
- Create: `database/migrations/006_meeting_share_links.sql`
- Create: `database/rollback/rollback_006_to_005.sql`
- Modify: `backend/app/models/meeting.py`

- [ ] **Step 1: Write the failing migration shape**

Create SQL migration that adds nullable `share_token` and `shared_at` to `meetings`, plus a unique index on `share_token`.

- [ ] **Step 2: Write the rollback script**

Remove the unique index and drop both columns in the rollback file.

- [ ] **Step 3: Update ORM model**

Add matching `Mapped` fields in `backend/app/models/meeting.py`.

- [ ] **Step 4: Verify file names and schema consistency**

Check the migration naming against the existing `database/migrations/` and `database/rollback/` conventions.

- [ ] **Step 5: Commit**

```bash
git add database/migrations/006_meeting_share_links.sql database/rollback/rollback_006_to_005.sql backend/app/models/meeting.py
git commit -m "feat(database): add meeting share columns"
```

### Task 2: Add share-related schemas

**Files:**
- Modify: `backend/app/schemas/meeting.py`
- Modify: `backend/app/schemas/task.py` only if needed for shared payload reuse

- [ ] **Step 1: Write schema-first tests**

Add backend tests that assert the response payload can serialize the new share response and shared-meeting aggregate response.

- [ ] **Step 2: Run the targeted tests and confirm failure**

Run: `pytest backend/tests/test_api.py -k share -v`
Expected: FAIL because the schemas do not exist yet.

- [ ] **Step 3: Add the new Pydantic models**

Add:
- `MeetingShareOut`
- `SharedMeetingOut`

Use existing meeting/transcript/task schemas where appropriate.

- [ ] **Step 4: Re-run targeted tests**

Run: `pytest backend/tests/test_api.py -k share -v`
Expected: PASS or move on to the next implementation failure.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/meeting.py backend/app/schemas/task.py backend/tests/test_api.py
git commit -m "feat(meeting): add share response schemas"
```

---

## Chunk 2: Backend share endpoints

### Task 3: Generate and reuse share tokens

**Files:**
- Modify: `backend/app/services/meeting_service.py`
- Modify: `backend/app/api/v1/endpoints/meetings.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write failing tests for share creation**

Add tests for:
- create share token for a meeting with summary
- reuse the same token on repeated requests
- return 400 when summary is missing
- return 404 for missing meeting

- [ ] **Step 2: Run one focused test and confirm it fails**

Run: `pytest backend/tests/test_api.py::test_meeting_share_is_idempotent -v`

- [ ] **Step 3: Implement token generation in service layer**

Add a service function that creates or reuses an opaque token and stores `shared_at`.

- [ ] **Step 4: Add the `POST /api/v1/meetings/{id}/share` endpoint**

Keep HTTP logic thin and delegate to the service.

- [ ] **Step 5: Re-run the focused tests**

Run:
- `pytest backend/tests/test_api.py::test_meeting_share_is_idempotent -v`
- `pytest backend/tests/test_api.py::test_meeting_share_requires_summary -v`

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/meeting_service.py backend/app/api/v1/endpoints/meetings.py backend/app/api/v1/router.py backend/tests/test_api.py
git commit -m "feat(meeting): add share link generation"
```

### Task 4: Add shared-meeting read endpoint

**Files:**
- Create: `backend/app/api/v1/endpoints/shared_meetings.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/app/services/meeting_service.py`
- Modify: `backend/app/schemas/meeting.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write failing tests for shared page payload**

Add tests for:
- valid token returns read-only payload
- invalid token returns 404
- payload includes meeting, transcripts, and tasks

- [ ] **Step 2: Run the targeted test and confirm failure**

Run: `pytest backend/tests/test_api.py::test_get_shared_meeting_returns_read_only_payload -v`

- [ ] **Step 3: Implement shared payload assembly**

Return the shared-meeting aggregate response from a dedicated endpoint module.

- [ ] **Step 4: Re-run the targeted tests**

Run:
- `pytest backend/tests/test_api.py::test_get_shared_meeting_returns_read_only_payload -v`
- `pytest backend/tests/test_api.py::test_get_shared_meeting_invalid_token_returns_404 -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/endpoints/shared_meetings.py backend/app/services/meeting_service.py backend/app/schemas/meeting.py backend/app/api/v1/router.py backend/tests/test_api.py
git commit -m "feat(meeting): add shared meeting read endpoint"
```

---

## Chunk 3: Frontend share flow

### Task 5: Add share API types and wrappers

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/meetings.ts`
- Test: `frontend/src/api/meetings.test.ts`

- [ ] **Step 1: Write failing API tests**

Add tests for:
- creating a share link calls `/api/v1/meetings/{id}/share`
- fetching a shared meeting calls `/api/v1/shared/meetings/{token}`

- [ ] **Step 2: Run the targeted vitest file and confirm failure**

Run: `npm --prefix frontend exec -- vitest run src/api/meetings.test.ts`

- [ ] **Step 3: Add typed API wrappers**

Add `createMeetingShareLink()` and `getSharedMeeting()`.

- [ ] **Step 4: Re-run the API tests**

Run: `npm --prefix frontend exec -- vitest run src/api/meetings.test.ts`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/types.ts frontend/src/api/meetings.ts frontend/src/api/meetings.test.ts
git commit -m "feat(frontend): add share link api wrappers"
```

### Task 6: Preserve redirect and render shared meeting page

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/views/MeetingDetailView.vue`
- Create: `frontend/src/views/SharedMeetingView.vue`

- [ ] **Step 1: Write route/login behavior tests or smoke checks**

Cover:
- unauthenticated access to `/shared/meetings/:token` stores `redirect`
- login success returns to the original share URL
- invalid redirect values are ignored

- [ ] **Step 2: Implement redirect preservation**

Update the router guard and login view so the original share URL survives the login hop.

- [ ] **Step 3: Add share-link action to meeting detail**

Generate the URL, copy it to clipboard, and show success/error messages.

- [ ] **Step 4: Build the read-only shared-meeting view**

Render meeting summary, transcripts, and tasks without write actions.

- [ ] **Step 5: Re-run frontend verification**

Run:
- `npm --prefix frontend exec -- vitest run src/api/meetings.test.ts src/api/auth.test.ts src/api/tasks.test.ts src/utils/recorder.test.ts`
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`

- [ ] **Step 6: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/views/LoginView.vue frontend/src/views/MeetingDetailView.vue frontend/src/views/SharedMeetingView.vue
git commit -m "feat(frontend): add read-only meeting share page"
```

---

## Chunk 4: Docs and final verification

### Task 7: Update docs and validate the end-to-end flow

**Files:**
- Modify: `docs/backend-api.md`
- Modify: `docs/frontend-runbook.md`

- [ ] **Step 1: Update the API docs**

Document the share creation endpoint, shared-meeting endpoint, response shapes, and redirect behavior.

- [ ] **Step 2: Update the frontend runbook**

Add the share-link QA steps and login redirect notes.

- [ ] **Step 3: Run backend and frontend verification**

Run:
- `pytest backend/tests/test_api.py -v --tb=short`
- `npm --prefix frontend exec -- vitest run src/api/meetings.test.ts src/api/auth.test.ts src/api/tasks.test.ts src/utils/recorder.test.ts`
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`

- [ ] **Step 4: Commit docs**

```bash
git add docs/backend-api.md docs/frontend-runbook.md
git commit -m "docs: document meeting share links"
```
