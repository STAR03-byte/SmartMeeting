# Phase A-3 Frontend Error Feedback Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make API failures in key frontend flows visibly surfaced (toast or page alert) and reduce duplicated `ElMessage.error(getApiErrorMessage(err))` by centralizing toast error notification.

**Architecture:** Add a tiny `notifyApiError()` utility that maps `unknown` errors to a user-facing message via `getApiErrorMessage()` and displays it via Element Plus `ElMessage`. Update a small set of high-impact views and `authStore.loadCurrentUser()` to avoid silent failures while keeping existing store/view responsibilities intact.

**Tech Stack:** Vue 3, TypeScript, Pinia, Element Plus, Axios, Vitest (existing)

---

## File Structure and Responsibilities

### Create

- `frontend/src/utils/notify.ts`
  - Single responsibility: show a toast error message for an `unknown` error.

### Modify

- `frontend/src/stores/authStore.ts`
  - Ensure `loadCurrentUser()` sets `error` on failure and rethrows (no silent failure).
- `frontend/src/views/MeetingDetailView.vue`
  - Replace repeated `ElMessage.error(getApiErrorMessage(err))` with `notifyApiError(err)`.
- `frontend/src/views/MeetingListView.vue`
  - Replace API-failure toast in create/delete flows with `notifyApiError(err)` (use the caught error, not `store.error`).
- `frontend/src/views/TasksView.vue`
  - Replace `ElMessage.error(getApiErrorMessage(err))` with `notifyApiError(err)` in status update.
- `frontend/src/views/UsersView.vue`
  - Replace `ElMessage.error(getApiErrorMessage(err))` with `notifyApiError(err)` for create/delete.

### Test

- `frontend/src/utils/notify.test.ts`
  - Unit test `notifyApiError()` by mocking `ElMessage.error` and verifying it receives the normalized message.

---

## Task 1: Add notifyApiError utility (TDD)

**Files:**
- Create: `frontend/src/utils/notify.ts`
- Create: `frontend/src/utils/notify.test.ts`

- [ ] **Step 1: Write failing test for notifyApiError()**

```ts
import { describe, expect, it, vi } from "vitest";

vi.mock("element-plus", () => ({
  ElMessage: {
    error: vi.fn(),
  },
}));

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return {
    ...actual,
    getApiErrorMessage: () => "normalized message",
  };
});

describe("notifyApiError", () => {
  it("shows normalized error message", async () => {
    const { ElMessage } = await import("element-plus");
    const { notifyApiError } = await import("./notify");

    notifyApiError(new Error("boom"));
    expect(ElMessage.error).toHaveBeenCalledWith("normalized message");
  });
});
```

- [ ] **Step 2: Run the test to confirm failure**

Run: `npx --prefix frontend vitest run frontend/src/utils/notify.test.ts`

Expected: FAIL (module `./notify` not found).

- [ ] **Step 3: Implement notifyApiError()**

```ts
import { ElMessage } from "element-plus";

import { getApiErrorMessage } from "../api/client";

export function notifyApiError(err: unknown, options?: { prefix?: string }): void {
  const message = getApiErrorMessage(err);
  const full = options?.prefix ? `${options.prefix}: ${message}` : message;
  ElMessage.error(full);
}
```

- [ ] **Step 4: Re-run the test and confirm pass**

Run: `npx --prefix frontend vitest run frontend/src/utils/notify.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/notify.ts frontend/src/utils/notify.test.ts
git commit -m "feat(frontend): add notifyApiError helper"
```

---

## Task 2: Make authStore.loadCurrentUser errors visible

**Files:**
- Modify: `frontend/src/stores/authStore.ts`

- [ ] **Step 1: Add failing test (if feasible) OR verify with typecheck/build**

If no existing auth store tests, skip unit test and rely on typecheck/build.

- [ ] **Step 2: Implement try/catch in loadCurrentUser()**

```ts
async loadCurrentUser() {
  if (!this.token) {
    this.currentUser = null;
    return;
  }

  try {
    this.error = null;
    this.currentUser = await fetchCurrentUser<UserItem>();
  } catch (error) {
    this.error = getApiErrorMessage(error);
    this.currentUser = null;
    throw error;
  }
}
```

- [ ] **Step 3: Run frontend typecheck**

Run: `npm --prefix frontend run typecheck`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/stores/authStore.ts
git commit -m "fix(frontend): surface loadCurrentUser errors"
```

---

## Task 3: Update views to use notifyApiError()

### Task 3.1: TasksView

**Files:**
- Modify: `frontend/src/views/TasksView.vue`

- [ ] Replace `ElMessage.error(getApiErrorMessage(err))` with `notifyApiError(err)` in `changeStatus`.
- [ ] Remove unused imports if any.
- [ ] Run: `npm --prefix frontend run typecheck`
- [ ] Commit:

```bash
git add frontend/src/views/TasksView.vue
git commit -m "refactor(frontend): unify task error toast"
```

### Task 3.2: UsersView

**Files:**
- Modify: `frontend/src/views/UsersView.vue`

- [ ] Replace `ElMessage.error(getApiErrorMessage(err))` with `notifyApiError(err)`.
- [ ] Run: `npm --prefix frontend run typecheck`
- [ ] Commit:

```bash
git add frontend/src/views/UsersView.vue
git commit -m "refactor(frontend): unify user error toast"
```

### Task 3.3: MeetingDetailView

**Files:**
- Modify: `frontend/src/views/MeetingDetailView.vue`

- [ ] Replace repeated `ElMessage.error(getApiErrorMessage(err))` with `notifyApiError(err)` in action handlers.
- [ ] Ensure no behavior change for non-API errors (e.g. invalid meeting id).
- [ ] Run: `npm --prefix frontend run typecheck`
- [ ] Commit:

```bash
git add frontend/src/views/MeetingDetailView.vue
git commit -m "refactor(frontend): unify meeting detail error toast"
```

### Task 3.4: MeetingListView

**Files:**
- Modify: `frontend/src/views/MeetingListView.vue`

- [ ] Change `catch { ... }` to `catch (err) { notifyApiError(err); }` for create/delete flows.
- [ ] Keep `AppErrorAlert` behavior unchanged.
- [ ] Run: `npm --prefix frontend run typecheck`
- [ ] Commit:

```bash
git add frontend/src/views/MeetingListView.vue
git commit -m "refactor(frontend): unify meeting list error toast"
```

---

## Task 4: Full verification

- [ ] Run frontend build

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] Run full project QA

Run: `python scripts/dev/qa.py`
Expected: PASS

---

## Task 5: PR + merge

- [ ] Push branch to origin
- [ ] Create PR titled "Phase A-3: frontend error visibility" with summary and verification evidence
- [ ] Ensure CI checks are all green
- [ ] Merge PR and delete branch
