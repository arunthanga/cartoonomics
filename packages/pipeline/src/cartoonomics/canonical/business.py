"""Business breakdowns unique to tijorifinance.com.

* :class:`RevenueSegment` — the "Revenue mix" / segment break-up (product,
  geography, or business line).
* :class:`OperationalMetric` — industry-specific KPIs from tijori's
  "Operational Metrics" (e.g. installed MW for a power producer, monthly
  transacting users for a marketplace, bed occupancy for a hospital).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from cartoonomics.canonical.common import UNIT_INR_CRORE, ReportingPeriod
from cartoonomics.canonical.enums import SegmentKind


class RevenueSegment(BaseModel):
    """One slice of the revenue mix for a given period."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Segment label, e.g. 'India' or 'Cloud'.")
    kind: SegmentKind = SegmentKind.BUSINESS
    period: ReportingPeriod
    value: float | None = Field(default=None, description="Segment revenue in ``unit``.")
    pct_of_total: float | None = Field(default=None, ge=0, le=100)
    unit: str = Field(default=UNIT_INR_CRORE)


class OperationalMetric(BaseModel):
    """A free-form, industry-specific KPI (tijori tracks 1000s of these)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Metric label, e.g. 'Installed Capacity'.")
    period: ReportingPeriod
    value: float | None = None
    unit: str = Field(default="", description="Metric unit, e.g. 'MW', 'users', 'Rs Cr'.")
