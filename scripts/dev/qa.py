from __future__ import annotations

import argparse
import subprocess


def run_step(name: str, command: list[str]) -> int:
    print(f"[qa] {name}: {' '.join(command)}")
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"[qa] {name} failed with exit code {result.returncode}")
        return result.returncode
    print(f"[qa] {name} passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SmartMeeting quality gates")
    parser.add_argument("--skip-backend-tests", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    args = parser.parse_args()

    steps: list[tuple[str, list[str]]] = []

    if not args.skip_backend_tests:
        steps.append(
            (
                "backend-tests",
                ["python", "-m", "pytest", "backend/tests", "-v", "--tb=short"],
            )
        )

    if not args.skip_frontend:
        steps.append(("frontend-typecheck", ["npm", "--prefix", "frontend", "run", "typecheck"]))
        steps.append(("frontend-build", ["npm", "--prefix", "frontend", "run", "build"]))

    for step_name, step_command in steps:
        code = run_step(step_name, step_command)
        if code != 0:
            return code

    print("[qa] all selected checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
