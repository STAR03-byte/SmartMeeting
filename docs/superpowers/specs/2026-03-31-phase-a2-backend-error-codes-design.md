# Phase A-2 — Backend request validation & error code consistency (Design)

Date: 2026-03-31

## 1. Goal

Stabilize and standardize backend API behavior for:

1) request input validation consistency
2) error response shape consistency (especially `error_code`)

This phase is intentionally incremental: **no functional feature expansion** and **no breaking changes** to existing clients.

## 2. Current State (Observed)

- Global exception handlers exist in `backend/app/main.py` for:
  - AI service failures (`LLMServiceError`, `WhisperServiceError`) → `503` with `{"detail":"AI service unavailable","error_code":"AI_SERVICE_UNAVAILABLE"}`
  - `RequestValidationError` → `422` with `detail=exc.errors()` and `error_code="REQUEST_VALIDATION_ERROR"`
  - generic `Exception` → `500` with `error_code="INTERNAL_SERVER_ERROR"`

- Most endpoints raise `HTTPException(status_code=..., detail="...")`.
  - This typically returns JSON `{"detail": "..."}` (no `error_code`).
  - Tests commonly assert `status_code` and `detail` only.

- Input validation patterns are mixed:
  - Some endpoints use `Annotated[Session, Depends(get_db)]`, others use `db: Session = Depends(get_db)`.
  - Most path params are plain `int` with no explicit constraints (e.g. `>= 1`).

## 3. Non-Goals

- Do not redesign business logic or move code across layers.
- Do not change existing `detail` strings.
- Do not require frontend changes for this phase.
- Do not introduce type suppression (`as any`, `@ts-ignore`, etc.).

## 4. Proposed Approach (Recommended)

### 4.1 Standardize error response envelope for `HTTPException`

Add an exception handler for `HTTPException` so that all explicit API errors include an `error_code` field while keeping `detail` intact.

**Response shape** (for all handled errors):

```json
{
  "detail": "...",
  "error_code": "..."
}
```

**Error code rules**:

- If the raised `HTTPException` already includes an `error_code`, keep it (future-compatible).
- Otherwise, derive a generic code from HTTP status:
  - 400 → `BAD_REQUEST`
  - 401 → `UNAUTHORIZED`
  - 403 → `FORBIDDEN`
  - 404 → `NOT_FOUND`
  - 409 → `CONFLICT`
  - 422 → `REQUEST_VALIDATION_ERROR` (even if thrown as HTTPException)
  - default (other 4xx) → `CLIENT_ERROR`

This ensures immediate consistency without touching every raise site.

### 4.2 Normalize path/query validation for common identifiers

For resource identifiers in path params (`meeting_id`, `task_id`, `user_id`, `transcript_id`, `participant_id` etc.), enforce:

- `ge=1` via FastAPI `Path(...)`.

This converts negative/zero ids into consistent `422` request validation errors (already standardized by global handler).

### 4.3 Normalize dependency injection style

Prefer the existing convention used in several endpoints:

- `db: Annotated[Session, Depends(get_db)]`

This is a readability/consistency change only.

## 5. Testing Strategy

### 5.1 Update existing tests minimally

- Keep all existing assertions about `status_code` and `detail` unchanged.
- Add new assertions where appropriate:
  - For endpoints that return `HTTPException` errors: assert `error_code` exists and matches the derived mapping.
  - For `RequestValidationError` responses: already include `error_code`; ensure it remains `REQUEST_VALIDATION_ERROR`.

### 5.2 Add focused unit/integration tests

- Test that unauthenticated access returns `401` with `error_code="UNAUTHORIZED"`.
- Test that a known `404` path returns `error_code="NOT_FOUND"`.
- Test that invalid path param (e.g. `/api/v1/meetings/0`) returns `422` with `error_code="REQUEST_VALIDATION_ERROR"`.

## 6. Documentation Updates

Update `docs/backend-api.md` “错误码约定” to include:

- Standard error response envelope: `detail` + `error_code`
- Generic mapping table for common HTTP errors
- Clarify `422` validation failure response and `detail` structure (list of error objects)

## 7. Rollout / Compatibility

- Backward compatible for clients reading only `detail`.
- Adds a stable `error_code` field for clients that want machine-readable handling.
- If any endpoint currently relies on FastAPI default `HTTPException` body shape, the new handler retains `detail` and adds one new field.

## 8. Definition of Done

- All backend tests pass: `python -m pytest backend/tests -v --tb=short`.
- Error responses across API consistently contain `error_code`.
- Updated `docs/backend-api.md` matches implementation.
