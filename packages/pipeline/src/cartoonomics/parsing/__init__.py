"""Document parsing layer (§7.1, FR-1.5 raw-then-parsed).

Turns a raw artifact (PDF / delimited text) into a canonical
``ParsedFinancials`` intermediate, decoupled from any specific source layout.
"""

from cartoonomics.parsing.documents import (
    LineItem,
    ParsedFinancials,
    parse_delimited,
    parse_financials,
    parse_pdf,
)
from cartoonomics.parsing.amfi import NavFile, NavRecord, parse_nav_file
from cartoonomics.parsing.sebi_pms import (
    PerformanceRow,
    PmsMonthlyReport,
    parse_pms_report,
)

__all__ = [
    "LineItem",
    "ParsedFinancials",
    "parse_delimited",
    "parse_financials",
    "parse_pdf",
    "parse_pms_report",
    "PmsMonthlyReport",
    "PerformanceRow",
    "parse_nav_file",
    "NavFile",
    "NavRecord",
]
