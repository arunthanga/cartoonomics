"""Company identity + the "top of the page" snapshot.

Mirrors the header and the customisable "Key Ratios at a glance" grid shown on a
screener.in / tijorifinance.com company page, plus the Pros & Cons summary.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from cartoonomics.canonical.enums import InstrumentType


class CompanyIdentifiers(BaseModel):
    """Stable identifiers and outbound links for a listed company."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Registered company name.")
    isin: str | None = Field(default=None, description="ISIN, e.g. 'INE002A01018'.")
    nse_code: str | None = Field(default=None, description="NSE symbol.")
    bse_code: str | None = Field(default=None, description="BSE scrip code.")
    website: str | None = None


class CompanyProfile(BaseModel):
    """Company header: who they are and what they do."""

    model_config = ConfigDict(extra="forbid")

    identifiers: CompanyIdentifiers
    instrument_type: InstrumentType = InstrumentType.EQUITY
    sector: str | None = None
    industry: str | None = None
    about: str | None = Field(default=None, description="Short business description.")


class KeyRatiosSnapshot(BaseModel):
    """The "Key Ratios" grid at the top of a company page.

    All fields are optional because screener.in lets the grid be customised and
    not every ratio is available for every company (FR-2.7 graceful degradation).
    Values are in INR crore where a currency amount is implied.
    """

    model_config = ConfigDict(extra="forbid")

    market_cap: float | None = None
    current_price: float | None = None
    high_52w: float | None = Field(default=None, description="52-week high price.")
    low_52w: float | None = Field(default=None, description="52-week low price.")
    stock_pe: float | None = Field(default=None, description="Trailing price/earnings.")
    book_value: float | None = None
    dividend_yield_pct: float | None = None
    roce_pct: float | None = Field(default=None, description="Return on capital employed (%).")
    roe_pct: float | None = Field(default=None, description="Return on equity (%).")
    face_value: float | None = None
    debt_to_equity: float | None = None
    no_of_shareholders: int | None = None
    as_of: date | None = None


class ProsAndCons(BaseModel):
    """screener.in's algorithmic Pros & Cons bullet lists."""

    model_config = ConfigDict(extra="forbid")

    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
