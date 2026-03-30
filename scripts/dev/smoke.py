from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return success status with detailed output."""
    print(f"[smoke] {description}")
    print(f"[smoke] running: {' '.join(command)}")
    start_time = datetime.now()
    result = subprocess.run(
        command, 
        check=False, 
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True
    )
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
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
    """Run the full meeting lifecycle smoke test."""
    print("[smoke] Starting full meeting lifecycle test")
    start_time = datetime.now()
    
    # Track test results for summary
    tests_passed = 0
    tests_total = 7
    
    # Step 1: Create meeting
    if run_command([
        "python", "-m", "pytest", 
        "backend/tests/test_api.py::test_meeting_crud_flow", 
        "-v", "-s"
    ], "Create meeting"):
        tests_passed += 1
    else:
        return 1
    
    # Step 2: Upload audio
    if run_command([
        "python", "-m", "pytest", 
        "backend/tests/test_api.py::test_audio_upload_for_meeting", 
        "-v", "-s"
    ], "Upload audio to meeting"):
        tests_passed += 1
    else:
        return 1
    
    # Step 3: Transcribe audio
    if run_command([
        "python", "-m", "pytest", 
        "backend/tests/test_api.py::test_transcribe_latest_audio_generates_transcript", 
        "-v", "-s"
    ], "Transcribe audio"):
        tests_passed += 1
    else:
        return 1
    
    # Step 4: Postprocess meeting (generate summary and tasks)
    if run_command([
        "python", "-m", "pytest", 
        "backend/tests/test_api.py::test_meeting_postprocess_generates_summary_and_tasks", 
        "-v", "-s"
    ], "Postprocess meeting"):
        tests_passed += 1
    else:
        return 1
    
    # Step 5: Verify task extraction and status flow
    if run_command([
        "python", "-m", "pytest", 
        "backend/tests/test_api.py::test_task_status_transition_and_completed_at", 
        "-v", "-s"
    ], "Verify task status flow"):
        tests_passed += 1
    else:
        return 1
    
    # Step 6: Test meeting export (txt format)
    if run_command([
        "python", "-m", "pytest", 
        "backend/tests/test_api.py::test_meeting_export_flow", 
        "-v", "-s"
    ], "Test meeting export"):
        tests_passed += 1
    else:
        return 1
    
    # Step 7: Test meeting share functionality
    if run_command([
        "python", "-m", "pytest", 
        "backend/tests/test_api.py::test_meeting_share_is_idempotent", 
        "-v", "-s"
    ], "Test meeting share"):
        tests_passed += 1
    else:
        return 1
    
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    print(f"[smoke] {tests_passed}/{tests_total} tests passed!")
    print(f"[smoke] Total execution time: {total_duration:.2f}s")
    
    if tests_passed == tests_total:
        print("[smoke] All full lifecycle tests passed!")
        return 0
    else:
        print(f"[smoke] {tests_total - tests_passed} test(s) failed!")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())