from __future__ import annotations

import contextlib
import importlib
import os
import socket
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
BACKEND_URL = "http://127.0.0.1:8000/health"


def _resolve_npm() -> str:
    npm_cmd = shutil.which("npm.cmd") if os.name == "nt" else None
    npm_bin = npm_cmd or shutil.which("npm")
    if npm_bin is None:
        raise RuntimeError("npm command not found")
    return npm_bin


def _url_ready(url: str, timeout: float = 1.0) -> bool:
    try:
        with urlopen(url, timeout=timeout):
            return True
    except URLError:
        return False


def _port_bindable(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        with contextlib.suppress(Exception):
            sock.close()


def _choose_frontend_port() -> int:
    raw = os.environ.get("SMARTMEETING_FRONTEND_PORT", "5173").strip()
    preferred = 5173
    if raw.isdigit():
        preferred = int(raw)

    candidates = [preferred, 3000, 4173, 6006, 8080]
    seen: set[int] = set()
    for port in candidates:
        if port in seen:
            continue
        seen.add(port)
        if _port_bindable(port):
            return port

    for port in range(3001, 3101):
        if _port_bindable(port):
            return port

    raise RuntimeError("no available frontend port")


def _run_bootstrap() -> None:
    cmd = [sys.executable, "scripts/dev/bootstrap.py"]
    print(f"[dev] Running dependency bootstrap: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"bootstrap failed with exit code {result.returncode}")


def _python_runtime_ready() -> bool:
    required_modules = ["fastapi", "uvicorn", "sqlalchemy", "pymysql"]
    for module in required_modules:
        try:
            importlib.import_module(module)
        except Exception:
            return False
    return True


def _frontend_runtime_ready() -> bool:
    return (ROOT / "frontend" / "node_modules").exists()


def _ensure_runtime_dependencies() -> None:
    pip_ready = _python_runtime_ready()
    npm_ready = _frontend_runtime_ready()

    if pip_ready and npm_ready:
        print("[dev] Runtime dependencies already satisfied; skip bootstrap")
        return

    if not pip_ready and not npm_ready:
        _run_bootstrap()
        return

    cmd = [sys.executable, "scripts/dev/bootstrap.py"]
    if pip_ready:
        cmd.append("--skip-pip")
    if npm_ready:
        cmd.append("--skip-npm")

    print(f"[dev] Running partial bootstrap: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"bootstrap failed with exit code {result.returncode}")


def _spawn_process(command: list[str], name: str) -> subprocess.Popen[str]:
    print(f"[dev] Starting {name}: {' '.join(command)}")
    return subprocess.Popen(command, cwd=ROOT)


def _terminate_process(proc: subprocess.Popen[str] | None, name: str) -> None:
    if proc is None:
        return
    if proc.poll() is not None:
        return
    print(f"[dev] Stopping {name} (pid={proc.pid})")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _wait_until_ready(url: str, name: str, process: subprocess.Popen[str], timeout_sec: int = 30) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{name} exited unexpectedly with code {process.returncode}")
        if _url_ready(url):
            return
        time.sleep(0.5)
    raise RuntimeError(f"{name} did not become ready within {timeout_sec}s")


def main() -> int:
    npm_bin = _resolve_npm()

    frontend_port = _choose_frontend_port()
    frontend_url = f"http://127.0.0.1:{frontend_port}"

    backend_running = _url_ready(BACKEND_URL)
    frontend_running = _url_ready(frontend_url)

    backend_proc: subprocess.Popen[str] | None = None
    frontend_proc: subprocess.Popen[str] | None = None

    def _shutdown(_: int, __: object) -> None:
        _terminate_process(frontend_proc, "frontend")
        _terminate_process(backend_proc, "backend")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        _ensure_runtime_dependencies()

        if not backend_running:
            backend_proc = _spawn_process(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                ],
                "backend",
            )
            _wait_until_ready(BACKEND_URL, "backend", backend_proc)
            print("[dev] Backend ready: http://127.0.0.1:8000")
        else:
            print("[dev] Backend already running: http://127.0.0.1:8000")

        if not frontend_running:
            frontend_proc = _spawn_process(
                [
                    npm_bin,
                    "--prefix",
                    "frontend",
                    "run",
                    "dev",
                    "--",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(frontend_port),
                ],
                "frontend",
            )
            _wait_until_ready(frontend_url, "frontend", frontend_proc)
            print(f"[dev] Frontend ready: {frontend_url}")
        else:
            print(f"[dev] Frontend already running: {frontend_url}")

        if backend_proc is None and frontend_proc is None:
            print("[dev] Both services are already running")
            return 0

        print("[dev] Dev environment ready. Press Ctrl+C to stop managed services.")

        while True:
            if backend_proc is not None and backend_proc.poll() is not None:
                raise RuntimeError(f"backend exited with code {backend_proc.returncode}")
            if frontend_proc is not None and frontend_proc.poll() is not None:
                raise RuntimeError(f"frontend exited with code {frontend_proc.returncode}")
            time.sleep(1)

    except KeyboardInterrupt:
        _terminate_process(frontend_proc, "frontend")
        _terminate_process(backend_proc, "backend")
        return 0
    except Exception as exc:
        print(f"[dev] ERROR: {exc}")
        _terminate_process(frontend_proc, "frontend")
        _terminate_process(backend_proc, "backend")
        return 1
    finally:
        with contextlib.suppress(Exception):
            if frontend_proc is not None and frontend_proc.poll() is None:
                _terminate_process(frontend_proc, "frontend")
        with contextlib.suppress(Exception):
            if backend_proc is not None and backend_proc.poll() is None:
                _terminate_process(backend_proc, "backend")


if __name__ == "__main__":
    raise SystemExit(main())
