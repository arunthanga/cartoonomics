import pytest

from cartoonomics.analysis import build_cashflow_cartoon
from cartoonomics.format import CartoonType, FlowDirection
from cartoonomics.parsing import LineItem, ParsedFinancials
from tests.conftest import FIXED_TS


def _build(items, **kwargs):
    parsed = ParsedFinancials(entity_name="Acme", period="FY2024", items=items)
    return build_cashflow_cartoon(
        parsed,
        source="BSE",
        source_url="https://example.test/f",
        source_hash="hash",
        fetched_at=FIXED_TS,
        **kwargs,
    )


@pytest.mark.unit
def test_build_cashflow_cartoon_from_demo(demo_financials):
    spec = build_cashflow_cartoon(
        demo_financials,
        source="BSE",
        source_url="https://example.test/f",
        source_hash="hash",
        fetched_at=FIXED_TS,
    )
    assert spec.cartoon_type == CartoonType.CASHFLOW
    node_ids = {n.id for n in spec.nodes}
    assert {"operating", "investing", "financing", "cash", "net"} <= node_ids
    op = next(n for n in spec.nodes if n.id == "operating")
    assert op.role == FlowDirection.INFLOW and op.value == 1850.0
    net = next(n for n in spec.nodes if n.id == "net")
    assert net.role == FlowDirection.INFLOW and net.value == 350.0
    # "Show the numbers" table mirrors every CF line item (FR-6.2).
    assert len(spec.table) == 4


@pytest.mark.unit
def test_net_computed_when_absent():
    spec = _build(
        [
            LineItem("CF", "Net cash from operating activities", 100.0),
            LineItem("CF", "Net cash used in investing activities", -40.0),
            LineItem("CF", "Net cash from financing activities", -10.0),
        ]
    )
    net = next(n for n in spec.nodes if n.id == "net")
    assert net.value == 50.0


@pytest.mark.unit
def test_negative_operating_and_positive_others_narrative():
    spec = _build(
        [
            LineItem("CF", "Net cash from operating activities", -500.0),
            LineItem("CF", "Net cash used in investing activities", 200.0),
            LineItem("CF", "Net cash from financing activities", 100.0),
            LineItem("CF", "Net decrease in cash", -200.0),
        ]
    )
    joined = " ".join(spec.narrative).lower()
    assert "consumed" in joined  # operating outflow branch
    assert "selling investments" in joined  # investing inflow branch
    assert "raised" in joined  # financing inflow branch
    assert "shrank" in joined  # net negative verdict


@pytest.mark.unit
def test_zero_net_holds_steady():
    spec = _build(
        [
            LineItem("CF", "Net cash from operating activities", 0.0),
            LineItem("CF", "Net cash used in investing activities", 0.0),
            LineItem("CF", "Net cash from financing activities", 0.0),
        ]
    )
    assert "held steady" in " ".join(spec.narrative).lower()


@pytest.mark.unit
def test_missing_cf_items_raises():
    with pytest.raises(ValueError, match="no cashflow"):
        _build([LineItem("PL", "Revenue", 100.0)])
