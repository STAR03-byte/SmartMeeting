from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_step(name: str, command: list[str]) -> int:
    print(f"[qa] {name}: {' '.join(command)}")
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"[qa] {name} failed with exit code {result.returncode}")
        return result.returncode
    print(f"[qa] {name} passed")
    return 0


def _resolve_command(command: list[str]) -> list[str]:
    if not command:
        return command
    if command[0] == "npm" and os.name == "nt":
        npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
        if npm_cmd:
            return [npm_cmd, *command[1:]]
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SmartMeeting quality gates")
    parser.add_argument("--skip-backend-tests", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="Run the stage A smoke flow")
    args = parser.parse_args()

    steps: list[tuple[str, list[str]]] = []

    if args.smoke:
        steps.append(
            (
                "stage-a-smoke",
                [sys.executable, "scripts/dev/smoke.py"],
            )
        )

    if not args.skip_backend_tests:
        steps.append(
            (
                "backend-tests",
                [sys.executable, "-m", "pytest", "backend/tests", "-v", "--tb=short"],
            )
        )

    if not args.skip_frontend:
        steps.append(
            (
                "frontend-tests",
                ["npm", "--prefix", "frontend", "exec", "--", "vitest", "--root", "frontend", "run", "src"],
            )
        )
        steps.append(("frontend-typecheck", ["npm", "--prefix", "frontend", "run", "typecheck"]))
        steps.append(("frontend-build", ["npm", "--prefix", "frontend", "run", "build"]))

    for step_name, step_command in steps:
        code = run_step(step_name, _resolve_command(step_command))
        if code != 0:
            return code

    print("[qa] all selected checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
