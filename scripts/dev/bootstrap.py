from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str]) -> None:
    print(f"[bootstrap] Running: {' '.join(command)}")
    subprocess.run(_resolve_command(command), check=True)


def _resolve_command(command: list[str]) -> list[str]:
    if not command:
        return command
    if command[0] == "npm" and os.name == "nt":
        npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
        if npm_cmd:
            return [npm_cmd, *command[1:]]
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Install SmartMeeting development dependencies")
    parser.add_argument("--skip-pip", action="store_true", help="Skip backend Python dependencies")
    parser.add_argument("--skip-npm", action="store_true", help="Skip frontend npm dependencies")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    npm_cache = project_root / ".npm-cache"
    npm_cache.mkdir(parents=True, exist_ok=True)

    try:
        if not args.skip_pip:
            run_command([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])

        if not args.skip_npm:
            run_command(
                [
                    "npm",
                    "--prefix",
                    "frontend",
                    "install",
                    "--cache",
                    str(npm_cache),
                ]
            )
    except subprocess.CalledProcessError as exc:
        print(f"[bootstrap] Failed with exit code {exc.returncode}")
        return exc.returncode

    print("[bootstrap] Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
