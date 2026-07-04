"""Small CLI to switch the TDD development mode on/off and report status.

Usage::

    python -m cartoonomics.tdd status
    python -m cartoonomics.tdd on
    python -m cartoonomics.tdd off

This persists the choice to the ``.tdd-mode`` state file (see ``config.py``).
The ``CARTOONOMICS_TDD_MODE`` environment variable still overrides the file.
"""

from __future__ import annotations

import sys

from cartoonomics.config import COVERAGE_MIN, set_tdd_mode, tdd_mode_enabled


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    command = argv[0] if argv else "status"

    if command == "on":
        path = set_tdd_mode(True)
        print(f"TDD mode: ON (coverage gate >= {COVERAGE_MIN}%). Wrote {path}.")
    elif command == "off":
        path = set_tdd_mode(False)
        print(f"TDD mode: OFF (tests run but do not gate). Wrote {path}.")
    elif command == "status":
        state = "ON" if tdd_mode_enabled() else "OFF"
        print(f"TDD mode: {state}")
    else:
        print(f"unknown command: {command!r} (use on|off|status)", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
