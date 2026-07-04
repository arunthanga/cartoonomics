"""Standardized, reproducible metrics (§7.2).

Currently: XIRR (FR-2.2) — annualized return for irregular, dated cashflows.
Implemented in pure Python (Newton-Raphson with a bisection fallback) so the
core has no heavy numerical dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

#: Formula version stored alongside computed metrics for reproducibility (FR-2.6).
XIRR_FORMULA_VERSION = "1.0.0"

_DAYS_PER_YEAR = 365.0


class XIRRError(ValueError):
    """Raised when XIRR cannot be computed for the given cashflows."""


@dataclass(frozen=True)
class Cashflow:
    """A dated cashflow. Negative = outflow (investment), positive = inflow."""

    when: date
    amount: float


def _npv(rate: float, flows: list[Cashflow], t0: date) -> float:
    return sum(
        cf.amount / (1.0 + rate) ** ((cf.when - t0).days / _DAYS_PER_YEAR) for cf in flows
    )


def _npv_derivative(rate: float, flows: list[Cashflow], t0: date) -> float:
    total = 0.0
    for cf in flows:
        years = (cf.when - t0).days / _DAYS_PER_YEAR
        total += -years * cf.amount / (1.0 + rate) ** (years + 1.0)
    return total


def xirr(
    flows: list[Cashflow],
    *,
    guess: float = 0.1,
    tol: float = 1e-7,
    max_iter: int = 100,
) -> float:
    """Compute the XIRR of dated cashflows.

    Raises :class:`XIRRError` if there are not both inflows and outflows, or if
    the solver cannot converge to a valid rate (> -100%).
    """
    if len(flows) < 2:
        raise XIRRError("XIRR needs at least two cashflows")
    if not (any(f.amount > 0 for f in flows) and any(f.amount < 0 for f in flows)):
        raise XIRRError("XIRR needs at least one inflow and one outflow")

    t0 = min(f.when for f in flows)

    # Newton-Raphson.
    rate = guess
    for _ in range(max_iter):
        value = _npv(rate, flows, t0)
        if abs(value) < tol:
            return rate
        derivative = _npv_derivative(rate, flows, t0)
        if derivative == 0:
            break
        step = value / derivative
        new_rate = rate - step
        if new_rate <= -1.0:  # keep the rate in the valid domain (> -100%)
            new_rate = (rate - 1.0) / 2.0
        if abs(new_rate - rate) < tol:
            return new_rate
        rate = new_rate

    # Bisection fallback on a bracketed sign change.
    low, high = -0.999999, 100.0
    f_low, f_high = _npv(low, flows, t0), _npv(high, flows, t0)
    if f_low * f_high > 0:
        raise XIRRError("XIRR did not converge (no sign change in bracket)")
    for _ in range(200):
        mid = (low + high) / 2.0
        f_mid = _npv(mid, flows, t0)
        if abs(f_mid) < tol:
            return mid
        if f_low * f_mid < 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2.0
