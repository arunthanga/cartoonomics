"""Golden-file regression test for the demo cashflow CartoonSpec.

The committed golden captures the exact payload the renderer expects. The only
volatile field is ``provenance.fetched_at`` (wall-clock at fetch time), which is
normalized before comparison. Regenerate with::

    python tests/regression/_regen_golden.py
"""

import json
from pathlib import Path

import pytest

from cartoonomics.pipeline import run_demo

GOLDEN = Path(__file__).parent / "golden" / "cashflow_demo.json"


def _normalize(payload: dict) -> dict:
    payload["provenance"]["fetched_at"] = "<normalized>"
    return payload


@pytest.mark.regression
def test_demo_spec_matches_golden():
    actual = _normalize(json.loads(run_demo().to_json()))
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert actual == expected
