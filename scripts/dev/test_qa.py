from __future__ import annotations

from unittest.mock import patch

from scripts.dev import qa


def test_run_step_returns_zero_on_success() -> None:
    with patch("scripts.dev.qa.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        assert qa.run_step("demo", ["echo", "ok"]) == 0


def test_run_step_returns_nonzero_on_failure() -> None:
    with patch("scripts.dev.qa.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 2
        assert qa.run_step("demo", ["echo", "fail"]) == 2
