"""Peer comparison table (screener.in "Peers" / tijori "Peer Comparison").

Columns mirror screener.in's peer grid: current price, valuation, size, yield,
latest-quarter performance and its variation, and ROCE.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PeerRow(BaseModel):
    """A single peer company row in the comparison grid."""

    model_config = ConfigDict(extra="forbid")

    name: str
    nse_code: str | None = None
    bse_code: str | None = None
    cmp: float | None = Field(default=None, description="Current market price (₹).")
    pe: float | None = Field(default=None, description="Price/earnings ratio.")
    market_cap: float | None = None
    dividend_yield_pct: float | None = None
    net_profit_qtr: float | None = Field(default=None, description="Latest-quarter net profit.")
    qtr_profit_var_pct: float | None = Field(default=None, description="QoQ/YoY profit variation (%).")
    sales_qtr: float | None = Field(default=None, description="Latest-quarter sales.")
    qtr_sales_var_pct: float | None = None
    roce_pct: float | None = None


class PeerComparison(BaseModel):
    """The peer set for a company, with the industry median for context."""

    model_config = ConfigDict(extra="forbid")

    industry: str | None = None
    median_pe: float | None = None
    median_market_cap: float | None = None
    peers: list[PeerRow] = Field(default_factory=list)
