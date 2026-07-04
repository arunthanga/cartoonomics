"""The three financial statements + ratios + compounded-growth tables.

Each ``*Row`` is one period column of a screener.in statement, strongly typed to
the exact line items those pages expose. Values are ``float | None`` so a missing
cell degrades to ``None`` rather than a misleading zero (FR-2.7). Amounts are in
the statement's ``unit`` (INR crore by default); ratios/percentages are plain
numbers (e.g. ``opm_pct == 21.5`` means 21.5%). Losses/outflows are negative.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from cartoonomics.canonical.common import UNIT_INR_CRORE, ReportingPeriod, SourceRef
from cartoonomics.canonical.enums import GrowthMetricName, StatementBasis


class ProfitLossRow(BaseModel):
    """One Profit & Loss column (screener.in "Quarterly Results" / "Profit & Loss").

    ``dividend_payout_pct`` is only populated for annual rows.
    """

    model_config = ConfigDict(extra="forbid")

    period: ReportingPeriod
    sales: float | None = None
    expenses: float | None = None
    operating_profit: float | None = None
    opm_pct: float | None = Field(default=None, description="Operating profit margin (%).")
    other_income: float | None = None
    interest: float | None = None
    depreciation: float | None = None
    profit_before_tax: float | None = None
    tax_pct: float | None = None
    net_profit: float | None = None
    eps: float | None = Field(default=None, description="Earnings per share (₹).")
    dividend_payout_pct: float | None = None


class BalanceSheetRow(BaseModel):
    """One Balance Sheet column (screener.in "Balance Sheet")."""

    model_config = ConfigDict(extra="forbid")

    period: ReportingPeriod
    equity_capital: float | None = None
    reserves: float | None = None
    borrowings: float | None = None
    other_liabilities: float | None = None
    total_liabilities: float | None = None
    fixed_assets: float | None = None
    cwip: float | None = Field(default=None, description="Capital work in progress.")
    investments: float | None = None
    other_assets: float | None = None
    total_assets: float | None = None


class CashFlowRow(BaseModel):
    """One Cash Flow column (screener.in "Cash Flows")."""

    model_config = ConfigDict(extra="forbid")

    period: ReportingPeriod
    operating_activity: float | None = Field(default=None, description="Cash from operating activity.")
    investing_activity: float | None = Field(default=None, description="Cash from investing activity.")
    financing_activity: float | None = Field(default=None, description="Cash from financing activity.")
    net_cash_flow: float | None = None


class RatiosRow(BaseModel):
    """One column of screener.in's "Ratios" (efficiency + returns) table."""

    model_config = ConfigDict(extra="forbid")

    period: ReportingPeriod
    debtor_days: float | None = None
    inventory_days: float | None = None
    days_payable: float | None = None
    cash_conversion_cycle: float | None = None
    working_capital_days: float | None = None
    roce_pct: float | None = None


class CompoundedGrowth(BaseModel):
    """One row of screener.in's compounded-growth summary.

    screener.in shows growth across 10y / 5y / 3y / 1y (or TTM) horizons for
    Sales, Profit, Stock Price CAGR, and Return on Equity. Each value is a
    percentage.
    """

    model_config = ConfigDict(extra="forbid")

    metric: GrowthMetricName
    ten_year_pct: float | None = None
    five_year_pct: float | None = None
    three_year_pct: float | None = None
    one_year_pct: float | None = None


class FinancialStatements(BaseModel):
    """All period series for a single reporting basis (standalone or consolidated)."""

    model_config = ConfigDict(extra="forbid")

    basis: StatementBasis
    currency: str = Field(default="INR")
    unit: str = Field(default=UNIT_INR_CRORE, description="Magnitude unit for all amounts.")

    quarterly_results: list[ProfitLossRow] = Field(default_factory=list)
    profit_loss: list[ProfitLossRow] = Field(default_factory=list)
    balance_sheet: list[BalanceSheetRow] = Field(default_factory=list)
    cash_flow: list[CashFlowRow] = Field(default_factory=list)
    ratios: list[RatiosRow] = Field(default_factory=list)
    growth: list[CompoundedGrowth] = Field(default_factory=list)

    source: SourceRef | None = Field(default=None, description="Provenance for these statements.")
