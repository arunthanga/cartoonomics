"""Parse a SEBI Portfolio Manager Monthly Report (HTML) into structured data.

The report served by :class:`~cartoonomics.connectors.sebi_pms.SebiPmsConnector`
is a set of labelled HTML tables. This module turns it into a
:class:`PmsMonthlyReport` carrying the headline figures users ask for — AUM,
client count and TWRR performance per strategy — while retaining *every* table
verbatim in :attr:`PmsMonthlyReport.tables` so nothing is silently dropped
(FR-1.6, raw-then-parsed FR-1.5).

Parsing is content-driven, not layout-driven: the General Information block is
found by its ``Name of the Portfolio Manager`` label and the performance blocks
by their ``Since Inception`` column, so the parser tolerates the surrounding
page markup changing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

# Cells rendered as a table; each row is a list of plain-text cell strings.
Table = list[list[str]]

_NAME_LABEL = "name of the portfolio manager"
_SINCE_INCEPTION = "since inception"


class _TableExtractor(HTMLParser):
    """Collect every ``<table>`` as a list of rows of plain-text cells."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[Table] = []
        self._table: Table | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._depth = 0  # nested-table depth for the current cell

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "table":
            if self._table is None:
                self._table = []
            self._depth += 1
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            self._row.append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self._depth -= 1
            if self._depth == 0:
                self.tables.append(self._table)
                self._table = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


@dataclass
class PerformanceRow:
    """One strategy (or its benchmark) row from a TWRR performance table."""

    strategy_group: str
    investment_approach: str
    aum_inr_crore: float | None
    returns: dict[str, float | None]
    is_benchmark: bool = False


@dataclass
class PmsMonthlyReport:
    """Structured view of a single Portfolio Manager's monthly report."""

    registration_number: str | None = None
    name: str | None = None
    registration_date: str | None = None
    registered_address: str | None = None
    principal_officer: str | None = None
    num_clients: int | None = None
    total_aum_inr_crore: float | None = None
    general_information: dict[str, str] = field(default_factory=dict)
    performance: list[PerformanceRow] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)

    # Provenance / selection context (filled by the caller/orchestrator).
    year: int | None = None
    month: int | None = None
    source_url: str | None = None
    source_hash: str | None = None


def _to_number(token: str) -> float | None:
    """Parse an Indian-formatted number; blanks / dashes become ``None``."""
    token = (token or "").strip().replace(",", "")
    if token in ("", "-", "--", "NA", "N/A"):
        return None
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()")
    try:
        value = float(token)
    except ValueError:
        return None
    return -value if negative else value


def _to_int(token: str) -> int | None:
    number = _to_number(token)
    return int(number) if number is not None else None


def _find_general_information(tables: list[Table]) -> dict[str, str]:
    """Return the label -> value map from the General Information table."""
    for table in tables:
        labels = {row[0].strip().lower() for row in table if len(row) >= 2}
        if _NAME_LABEL in labels:
            info: dict[str, str] = {}
            for row in table:
                if len(row) >= 2 and row[0].strip():
                    info[row[0].strip()] = row[1].strip()
            return info
    return {}


def _lookup(info: dict[str, str], needle: str) -> str | None:
    needle = needle.lower()
    for label, value in info.items():
        if needle in label.lower():
            return value
    return None


def _parse_performance_table(table: Table) -> list[PerformanceRow]:
    """Parse one TWRR performance table (identified by its 'Since Inception' header)."""
    header_idx = next(
        (i for i, row in enumerate(table) if any(_SINCE_INCEPTION in c.lower() for c in row)),
        None,
    )
    if header_idx is None:
        return []
    header = table[header_idx]
    # Header: [Strategy, Investment Approach, AUM (INR Cr.), <horizon>...].
    horizons = [c.strip() for c in header[3:]]
    n = len(horizons)
    if n == 0:
        return []

    rows: list[PerformanceRow] = []
    group = ""
    for row in table[header_idx + 1:]:
        cells = [c.strip() for c in row]
        if len(cells) == 1 and cells[0]:
            group = cells[0]  # rowspan group label, e.g. "EQUITY"
            continue
        if len(cells) < 2 + n:
            continue
        approach = cells[0]
        is_benchmark = approach.lower().startswith("benchmark")
        return_cells = cells[2 : 2 + n]
        rows.append(
            PerformanceRow(
                strategy_group=group,
                investment_approach=approach,
                aum_inr_crore=_to_number(cells[1]),
                returns={h: _to_number(v) for h, v in zip(horizons, return_cells)},
                is_benchmark=is_benchmark,
            )
        )
    return rows


def parse_pms_report(
    html: str,
    *,
    year: int | None = None,
    month: int | None = None,
    source_url: str | None = None,
    source_hash: str | None = None,
) -> PmsMonthlyReport:
    """Parse the SEBI PMR HTML into a :class:`PmsMonthlyReport`."""
    extractor = _TableExtractor()
    extractor.feed(html)
    tables = extractor.tables

    info = _find_general_information(tables)
    performance: list[PerformanceRow] = []
    for table in tables:
        if any(_SINCE_INCEPTION in c.lower() for row in table for c in row):
            performance.extend(_parse_performance_table(table))

    return PmsMonthlyReport(
        registration_number=_lookup(info, "registration number"),
        name=_lookup(info, "name of the portfolio manager"),
        registration_date=_lookup(info, "date of registration"),
        registered_address=_lookup(info, "registered address"),
        principal_officer=_lookup(info, "name of principal officer"),
        num_clients=_to_int(_lookup(info, "no. of clients") or ""),
        total_aum_inr_crore=_to_number(_lookup(info, "total assets under management") or ""),
        general_information=info,
        performance=performance,
        tables=tables,
        year=year,
        month=month,
        source_url=source_url,
        source_hash=source_hash,
    )


__all__ = ["parse_pms_report", "PmsMonthlyReport", "PerformanceRow"]
