"""Enumerations for the canonical financial data model (§13).

These enums fix the vocabulary shared across the screener.in / tijorifinance.com
style data model so connectors, parsers, and the API never invent ad-hoc string
values for the same concept.
"""

from __future__ import annotations

from enum import Enum


class InstrumentType(str, Enum):
    """Asset class of a canonical instrument (requirements §13)."""

    EQUITY = "equity"
    MF = "mf"
    PMS = "pms"
    AIF = "aif"
    NPS = "nps"
    GOLD = "gold"
    REAL_ESTATE = "real_estate"


class StatementBasis(str, Enum):
    """Whether financials are the parent-only or group view.

    screener.in and tijorifinance.com both expose a Standalone/Consolidated
    toggle; every statement therefore records which basis it was reported on.
    """

    STANDALONE = "standalone"
    CONSOLIDATED = "consolidated"


class PeriodType(str, Enum):
    """Reporting cadence of a period column."""

    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    TTM = "ttm"  # trailing twelve months


class GrowthMetricName(str, Enum):
    """The rows of screener.in's compounded-growth table (§7.4 trends)."""

    SALES = "sales"
    PROFIT = "profit"
    STOCK_PRICE = "stock_price"
    RETURN_ON_EQUITY = "return_on_equity"


class SegmentKind(str, Enum):
    """How a revenue-mix segment is cut (tijorifinance.com "Revenue mix")."""

    PRODUCT = "product"
    GEOGRAPHY = "geography"
    BUSINESS = "business"
    OTHER = "other"


class DocumentType(str, Enum):
    """Filing/document kinds listed under screener.in / tijori "Documents"."""

    ANNOUNCEMENT = "announcement"
    ANNUAL_REPORT = "annual_report"
    CREDIT_RATING = "credit_rating"
    CONCALL_TRANSCRIPT = "concall_transcript"
    CONCALL_NOTES = "concall_notes"
    INVESTOR_PRESENTATION = "investor_presentation"
    EARNINGS_RELEASE = "earnings_release"


class CorporateActionType(str, Enum):
    """Corporate actions (tijorifinance.com "Corporate Actions")."""

    DIVIDEND = "dividend"
    SPLIT = "split"
    BONUS = "bonus"
    BUYBACK = "buyback"
    RIGHTS = "rights"
    AGM = "agm"


class MetricName(str, Enum):
    """Derived, comparison metrics (requirements §13 ``Metric``, §7.2)."""

    XIRR = "xirr"
    LIQUIDITY = "liquidity"
    TRANSFERABILITY = "transferability"
    COST = "cost"
    RISK = "risk"
    TAX = "tax"
