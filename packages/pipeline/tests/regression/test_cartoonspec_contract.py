"""Regression guards on the CartoonSpec contract consumed by the renderer.

If any of these change, the frontend renderer and any downstream consumer of the
predefined format may break — so they are guarded explicitly.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cartoonomics.analysis import build_cashflow_cartoon
from cartoonomics.format import CARTOON_SPEC_VERSION, FlowDirection
from cartoonomics.parsing import LineItem, ParsedFinancials
from cartoonomics.pipeline import run_demo
from tests.conftest import FIXED_TS


@pytest.mark.regression
def test_demo_spec_honours_contract():
    spec = run_demo()
    assert spec.spec_version == CARTOON_SPEC_VERSION
    assert spec.accessibility.alt_text  # A11Y-2
    assert spec.accessibility.table_caption
    assert spec.animation.reduced_motion_ok is True  # A11Y-5
    assert spec.provenance.source and spec.provenance.source_hash  # FR-1.3
    known = {n.id for n in spec.nodes}
    assert all({f.source, f.target} <= known for f in spec.flows)
    assert spec.table, "every cartoon must carry a 'Show the numbers' table (FR-6.2)"


@pytest.mark.regression
@given(
    operating=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False),
    investing=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False),
    financing=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False),
)
@settings(max_examples=100, deadline=None)
def test_net_change_equals_activity_sum(operating, investing, financing):
    """Invariant: with no explicit net line, net == sum of activity totals."""
    parsed = ParsedFinancials(
        entity_name="Acme",
        period="FY2024",
        items=[
            LineItem("CF", "Net cash from operating activities", operating),
            LineItem("CF", "Net cash used in investing activities", investing),
            LineItem("CF", "Net cash from financing activities", financing),
        ],
    )
    spec = build_cashflow_cartoon(
        parsed,
        source="BSE",
        source_url="https://example.test/f",
        source_hash="h",
        fetched_at=FIXED_TS,
    )
    net = next(n for n in spec.nodes if n.id == "net")
    expected = operating + investing + financing
    assert net.value == pytest.approx(abs(expected))
    if expected > 0:
        assert net.role == FlowDirection.INFLOW
    elif expected < 0:
        assert net.role == FlowDirection.OUTFLOW
    else:
        assert net.role == FlowDirection.NEUTRAL
