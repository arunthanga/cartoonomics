"""Cross-cutting building blocks for the canonical data model.

* :class:`SourceRef` — provenance carried by every data-bearing record so the
  §13 invariant ("every Financials/Holding/Metric row references its source")
  holds by construction (FR-1.3, UX-4).
* :class:`ReportingPeriod` — the period a column of data belongs to (an annual
  year, a quarter, or a trailing-twelve-months figure).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from cartoonomics.canonical.enums import PeriodType

UNIT_INR_CRORE = "INR_CRORE"


class SourceRef(BaseModel):
    """Where a record came from (provenance, FR-1.3)."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., description="Source-of-record, e.g. 'BSE', 'NSE', 'screener.in'.")
    source_url: str = Field(..., description="Link back to the original filing/page.")
    fetched_at: datetime = Field(..., description="UTC fetch timestamp.")
    source_hash: str | None = Field(default=None, description="Hash of the raw artifact.")
    filing_period: str | None = Field(default=None, description="Reporting period, e.g. 'FY2024'.")


class ReportingPeriod(BaseModel):
    """A single period column (screener.in shows one column per period)."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., description="Human label, e.g. 'FY2024', 'Q1 FY2025', 'TTM'.")
    period_type: PeriodType = PeriodType.ANNUAL
    end_date: date | None = Field(default=None, description="Period end date, if known.")
    fiscal_year: int | None = Field(default=None, description="Fiscal year, e.g. 2024.")
