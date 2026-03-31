from __future__ import annotations

from unittest.mock import patch

from scripts.dev import smoke


def test_smoke_runs_steps_in_order() -> None:
    calls: list[list[str]] = []

    def _run(command, check=False, **kwargs):
        calls.append(command)
        class Result:
            returncode = 0

        return Result()

    with patch("scripts.dev.smoke.subprocess.run", side_effect=_run):
        assert smoke.main() == 0

    assert calls == [command for command, _description in smoke.STEPS]
