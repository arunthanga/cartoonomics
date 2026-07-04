from datetime import date

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cartoonomics.analysis.metrics import Cashflow, XIRRError, xirr


@pytest.mark.unit
def test_xirr_simple_doubling_over_one_year():
    flows = [Cashflow(date(2023, 1, 1), -100.0), Cashflow(date(2024, 1, 1), 110.0)]
    rate = xirr(flows)
    assert rate == pytest.approx(0.10, abs=1e-4)


@pytest.mark.unit
def test_xirr_irregular_cashflows():
    flows = [
        Cashflow(date(2022, 1, 1), -1000.0),
        Cashflow(date(2022, 6, 1), -500.0),
        Cashflow(date(2023, 1, 1), 1650.0),
    ]
    rate = xirr(flows)
    # Reinvest at the solved rate -> NPV ~ 0.
    t0 = min(f.when for f in flows)
    npv = sum(f.amount / (1 + rate) ** ((f.when - t0).days / 365.0) for f in flows)
    assert npv == pytest.approx(0.0, abs=1e-3)


@pytest.mark.unit
def test_xirr_requires_two_flows():
    with pytest.raises(XIRRError):
        xirr([Cashflow(date(2023, 1, 1), -100.0)])


@pytest.mark.unit
def test_xirr_requires_inflow_and_outflow():
    with pytest.raises(XIRRError):
        xirr([Cashflow(date(2023, 1, 1), -100.0), Cashflow(date(2024, 1, 1), -50.0)])


@pytest.mark.unit
@given(rate=st.floats(min_value=-0.5, max_value=2.0))
@settings(max_examples=50, deadline=None)
def test_xirr_recovers_known_rate(rate):
    """Property: a 1-year invest/return pair should recover the implied rate."""
    invest = -1000.0
    payout = -invest * (1 + rate)
    flows = [Cashflow(date(2020, 1, 1), invest), Cashflow(date(2021, 1, 1), payout)]
    # 2020->2021 has 366 days (leap year); solve and check NPV, not the nominal rate.
    solved = xirr(flows)
    t0 = min(f.when for f in flows)
    npv = sum(f.amount / (1 + solved) ** ((f.when - t0).days / 365.0) for f in flows)
    assert npv == pytest.approx(0.0, abs=1e-2)
