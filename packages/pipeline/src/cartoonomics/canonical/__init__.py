"""The canonical financial data model (requirements §13).

This package is the structured, validated schema for the data cartoonomics shows
users — modelled on what screener.in and tijorifinance.com expose on a company
page: profile + key ratios, the three financial statements (standalone and
consolidated) with ratios and compounded-growth tables, shareholding pattern,
peer comparison, revenue mix, operational metrics, documents, corporate actions,
and derived comparison metrics.

It is deliberately separate from :mod:`cartoonomics.format` (the ``CartoonSpec``
*rendering* contract): connectors/parsers populate a :class:`CompanyDataset`, and
analysis builders turn that into a ``CartoonSpec`` for the frontend.
"""

from cartoonomics.canonical.business import OperationalMetric, RevenueSegment
from cartoonomics.canonical.common import (
    UNIT_INR_CRORE,
    ReportingPeriod,
    SourceRef,
)
from cartoonomics.canonical.company import (
    CompanyIdentifiers,
    CompanyProfile,
    KeyRatiosSnapshot,
    ProsAndCons,
)
from cartoonomics.canonical.dataset import (
    CANONICAL_SCHEMA_VERSION,
    CompanyDataset,
)
from cartoonomics.canonical.documents import CorporateAction, Document
from cartoonomics.canonical.enums import (
    CorporateActionType,
    DocumentType,
    GrowthMetricName,
    InstrumentType,
    MetricName,
    PeriodType,
    SegmentKind,
    StatementBasis,
)
from cartoonomics.canonical.financials import (
    BalanceSheetRow,
    CashFlowRow,
    CompoundedGrowth,
    FinancialStatements,
    ProfitLossRow,
    RatiosRow,
)
from cartoonomics.canonical.metrics import ComputedMetric
from cartoonomics.canonical.peers import PeerComparison, PeerRow
from cartoonomics.canonical.shareholding import ShareholdingRow

__all__ = [
    "CANONICAL_SCHEMA_VERSION",
    "UNIT_INR_CRORE",
    # common
    "ReportingPeriod",
    "SourceRef",
    # enums
    "CorporateActionType",
    "DocumentType",
    "GrowthMetricName",
    "InstrumentType",
    "MetricName",
    "PeriodType",
    "SegmentKind",
    "StatementBasis",
    # company
    "CompanyIdentifiers",
    "CompanyProfile",
    "KeyRatiosSnapshot",
    "ProsAndCons",
    # financials
    "BalanceSheetRow",
    "CashFlowRow",
    "CompoundedGrowth",
    "FinancialStatements",
    "ProfitLossRow",
    "RatiosRow",
    # ownership / business
    "ShareholdingRow",
    "PeerComparison",
    "PeerRow",
    "RevenueSegment",
    "OperationalMetric",
    # documents & metrics
    "CorporateAction",
    "Document",
    "ComputedMetric",
    # top-level
    "CompanyDataset",
]
