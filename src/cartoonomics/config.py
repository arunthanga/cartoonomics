"""Runtime configuration, including the switchable TDD mode.

The TDD mode toggle (§ user request) can be switched on/off through, in order of
precedence:

1. The ``CARTOONOMICS_TDD_MODE`` environment variable ("on"/"off", "1"/"0", ...).
2. A ``.tdd-mode`` state file at the repository root (written by ``make tdd-on`` /
   ``make tdd-off``).
3. The built-in default (ON — the project is TDD-first by default).

When TDD mode is ON the test harness (``scripts/run_tests.sh`` / ``make test``)
enforces the red-green-refactor gate: the full unit + regression suites must
pass and coverage must meet ``COVERAGE_MIN`` or the command fails. When it is
OFF the same tests can still be run, but they no longer gate development.
"""

from __future__ import annotations

import os
from pathlib import Path

TDD_STATE_FILENAME = ".tdd-mode"
TDD_ENV_VAR = "CARTOONOMICS_TDD_MODE"
COVERAGE_MIN = 85

_TRUTHY = {"1", "true", "yes", "on", "enabled"}
_FALSY = {"0", "false", "no", "off", "disabled"}


def repo_root() -> Path:
    """Return the repository root (two levels up from this file)."""
    return Path(__file__).resolve().parents[2]


def _parse_bool(value: str) -> bool | None:
    token = value.strip().lower()
    if token in _TRUTHY:
        return True
    if token in _FALSY:
        return False
    return None


def tdd_mode_enabled() -> bool:
    """Return whether TDD mode is currently switched on."""
    env_value = os.environ.get(TDD_ENV_VAR)
    if env_value is not None:
        parsed = _parse_bool(env_value)
        if parsed is not None:
            return parsed

    state_file = repo_root() / TDD_STATE_FILENAME
    if state_file.exists():
        parsed = _parse_bool(state_file.read_text(encoding="utf-8"))
        if parsed is not None:
            return parsed

    return True  # TDD-first by default


def set_tdd_mode(enabled: bool) -> Path:
    """Persist the TDD mode toggle to the state file. Returns the file path."""
    state_file = repo_root() / TDD_STATE_FILENAME
    state_file.write_text("on" if enabled else "off", encoding="utf-8")
    return state_file
