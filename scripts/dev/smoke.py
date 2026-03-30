from __future__ import annotations

import subprocess


STEPS = [
    ["python", "-m", "pytest", "backend/tests/test_api.py", "-q"],
    ["python", "-m", "pytest", "backend/tests/test_hotwords.py", "-q"],
]


def main() -> int:
    for command in STEPS:
        print(f"[smoke] running: {' '.join(command)}")
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            print(f"[smoke] failed: {' '.join(command)}")
            return result.returncode
    print("[smoke] all steps passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
