# SmartMeeting One-Command Dev Startup Design

> **Goal:** 从仓库根目录用一条命令启动本地开发环境，自动处理依赖准备，并确保前后端使用正确端口。

**Architecture:** 通过根 `package.json` 暴露单一入口 `npm run dev`，该入口调用 `scripts/dev/dev.py` 作为进程编排器。编排器先完成依赖准备，再检测后端 `8000` 和前端 `5173` 是否已可用；缺失的服务才启动，已运行的服务直接复用。后端启动继续使用现有 `backend.main:app`，前端继续使用 Vite；`scripts/dev/bootstrap.py` 需要修正为 Windows 安全的 npm 解析方式，避免再次出现“命令存在但无法调用”的问题。

**Tech Stack:** Python 标准库（`subprocess`、`urllib`、`signal`、`pathlib`）、npm scripts、FastAPI/Uvicorn、Vite。

---

## 1. Background

当前本地启动依赖两步：先装依赖，再分别起后端和前端。对于日常打开项目，这种流程太长，而且之前 `bootstrap.py` 在 Windows 下直接调用 `npm`，会导致命令不存在的启动失败。与此同时，前端开发代理已经对齐到后端默认端口 `8000`，因此现在最需要优化的是“入口数量”和“默认启动体验”，而不是再引入新的开发框架。

## 2. Goals

1. 只保留一个推荐入口：`npm run dev`。
2. 该入口在启动前自动完成依赖准备，用户不需要先手动执行 bootstrap。
3. 该入口启动后端 `8000` 和前端 `5173`，并保持两个进程持续运行。
4. 如果已有服务正在运行，脚本应识别并复用，不重复拉起相同端口。
5. 保留现有手工入口（`npm run dev:backend`、`npm run dev:frontend`）供调试使用。

## 3. Non-goals

- 不引入 Docker 或新的容器编排。
- 不改造后端业务逻辑或 API 行为。
- 不新增第三方进程管理依赖（如 `concurrently`）。
- 不改变生产部署方式。

## 4. Proposed approaches

### Approach A: Root npm script + Python orchestrator (Recommended)

新增根 `npm run dev`，由 `scripts/dev/dev.py` 完成依赖准备、端口探测、进程拉起、退出清理。该脚本直接复用现有 Python 和 npm 入口，不需要额外依赖。

**Pros**

- 单命令，符合日常打开项目的诉求。
- Windows 兼容性最好，依赖最少。
- 可以明确处理“已启动服务复用”和“启动失败回收”。

**Cons**

- 需要新增一个 Python 编排脚本。

### Approach B: npm-only task runner

使用 npm 生态中的并发工具统一启动前后端。

**Pros**

- 入口看起来更“纯前端工程化”。

**Cons**

- 需要引入额外依赖。
- Windows 下的命令解析和信号处理更容易出问题。

### Approach C: 继续保留多命令，但提供快捷批处理

用一个 `.bat`/`.ps1` 解决“少敲命令”的问题。

**Pros**

- 实现简单。

**Cons**

- 入口不统一。
- 维护两套启动方式，容易再次漂移。

**Decision:** 采用 Approach A。

## 5. Design details

### 5.1 Root entry point

Modify `package.json`:

- Add `"dev": "python scripts/dev/dev.py"`.
- Keep existing `dev:backend` and `dev:frontend` unchanged.

This makes `npm run dev` the default developer entry, while preserving explicit control for debugging.

### 5.2 Dependency preparation

`scripts/dev/dev.py` should prepare dependencies before launching services.

- It may reuse `scripts/dev/bootstrap.py` directly.
- `bootstrap.py` must resolve `npm.cmd` on Windows, the same way `scripts/dev/qa.py` already does for npm-based commands.
- If dependency installation fails, the orchestrator exits immediately with a non-zero code.

### 5.3 Service orchestration

`scripts/dev/dev.py` is responsible for the runtime lifecycle:

1. Check whether backend health endpoint responds on `http://127.0.0.1:8000/health`.
2. Check whether frontend root responds on `http://127.0.0.1:5173`.
3. Start any missing service(s) using existing commands:
   - Backend: `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`
   - Frontend: `npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173`
4. Keep the parent process alive and forward Ctrl+C / termination signals to children.
5. If a child exits unexpectedly, terminate the sibling process and surface the failure.

The script should print the local URLs once startup succeeds.

### 5.4 Error handling

- If a service port is occupied but the expected health/root check fails, treat it as a conflict and print a clear error.
- If backend startup fails, stop the frontend child process.
- If frontend startup fails, stop the backend child process.
- If the user interrupts the process, the script should shut down both children cleanly.

### 5.5 Documentation updates

Update the docs that explain local startup so they reflect the new primary path:

- `README.md`: recommend `npm run dev` as the first local start command.
- `docs/frontend-runbook.md`: replace the two-step startup instructions with the one-command path, and keep the environment variable override note only as fallback.
- Keep the current `backend` / `frontend` manual commands listed as alternate entry points, not the main path.

## 6. Acceptance criteria

- `npm run dev` from repo root starts or reuses both services without extra manual steps.
- Frontend opens at `http://127.0.0.1:5173`.
- Backend health check succeeds at `http://127.0.0.1:8000/health`.
- Re-running `npm run dev` while services are already up does not create duplicate listeners.
- Windows no longer fails on npm command resolution during bootstrap.

## 7. Verification

Manual QA required after implementation:

1. Stop any existing SmartMeeting dev processes.
2. Run `npm run dev` once from the repo root.
3. Verify backend health with `Invoke-WebRequest http://127.0.0.1:8000/health`.
4. Verify frontend root with `Invoke-WebRequest http://127.0.0.1:5173`.
5. Run `npm run dev` a second time and confirm it exits or reports already-running services instead of spawning duplicates.

Automated checks:

- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`
- `python -m pytest backend/tests/test_api.py::test_health_check -q`
