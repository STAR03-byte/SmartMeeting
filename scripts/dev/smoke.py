from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[2]


STEPS: Final[list[tuple[list[str], str]]] = [
    (
        [
            "python",
            "-m",
            "pytest",
            "backend/tests/test_api.py::test_meeting_crud_flow",
            "-v",
            "-s",
        ],
        "Create meeting",
    ),
    (
        [
            "python",
            "-m",
            "pytest",
            "backend/tests/test_api.py::test_audio_upload_for_meeting",
            "-v",
            "-s",
        ],
        "Upload audio to meeting",
    ),
    (
        [
            "python",
            "-m",
            "pytest",
            "backend/tests/test_api.py::test_transcribe_latest_audio_generates_transcript",
            "-v",
            "-s",
        ],
        "Transcribe audio",
    ),
    (
        [
            "python",
            "-m",
            "pytest",
            "backend/tests/test_api.py::test_meeting_postprocess_generates_summary_and_tasks",
            "-v",
            "-s",
        ],
        "Postprocess meeting",
    ),
    (
        [
            "python",
            "-m",
            "pytest",
            "backend/tests/test_api.py::test_task_status_transition_and_completed_at",
            "-v",
            "-s",
        ],
        "Verify task status flow",
    ),
    (
        [
            "python",
            "-m",
            "pytest",
            "backend/tests/test_api.py::test_meeting_export_flow",
            "-v",
            "-s",
        ],
        "Test meeting export",
    ),
    (
        [
            "python",
            "-m",
            "pytest",
            "backend/tests/test_api.py::test_meeting_share_is_idempotent",
            "-v",
            "-s",
        ],
        "Test meeting share",
    ),
]


def run_command(command: list[str], description: str) -> bool:
    print(f"[smoke] {description}")
    print(f"[smoke] running: {' '.join(command)}")
    start_time = datetime.now()
    result = subprocess.run(
        command,
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    duration = (datetime.now() - start_time).total_seconds()

    if result.returncode != 0:
        print(f"[smoke] FAILED: {' '.join(command)} (took {duration:.2f}s)")
        if result.stdout:
            print(f"[smoke] STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"[smoke] STDERR:\n{result.stderr}")
        return False

    print(f"[smoke] PASSED: {' '.join(command)} (took {duration:.2f}s)")
    return True


def main() -> int:
    print("[smoke] Starting full meeting lifecycle test")
    start_time = datetime.now()

    tests_total = len(STEPS)
    tests_passed = 0
    for command, description in STEPS:
        if not run_command(command, description):
            return 1
        tests_passed += 1

    total_duration = (datetime.now() - start_time).total_seconds()
    print(f"[smoke] {tests_passed}/{tests_total} tests passed!")
    print(f"[smoke] Total execution time: {total_duration:.2f}s")
    print("[smoke] All full lifecycle tests passed!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
