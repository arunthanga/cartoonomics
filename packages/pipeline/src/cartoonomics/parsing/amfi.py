"""Parse AMFI NAV feeds (daily NAVAll + historical report) into structured rows.

Both feeds are semicolon-delimited text that interleaves three kinds of line:

* a **header** row naming the columns (column *order differs* between the daily
  and historical feeds, so parsing is header-driven, not positional);
* **grouping** lines — a scheme *category* (``... Schemes(Equity Scheme - ...)``)
  or an *AMC* name (``HDFC Mutual Fund``);
* **data** rows — one NAV record per scheme/plan.

The parser tracks the current category/AMC as context and attaches it to each
:class:`NavRecord`, so every record is self-describing. Blank/garbled lines are
skipped rather than dropped silently into wrong records (FR-1.6).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# A grouping line that names a scheme category, e.g.
# "Open Ended Schemes(Equity Scheme - Large Cap Fund)".
_CATEGORY_RE = re.compile(r"schemes?\s*\(", re.IGNORECASE)

# Column-name -> canonical field. Matched as case-insensitive substrings so both
# "ISIN Div Payout/ ISIN Growth" and "ISIN Div Payout/ISIN Growth" resolve.
_COLUMN_MATCHERS: list[tuple[str, str]] = [
    ("scheme_code", "scheme code"),
    ("scheme_name", "scheme name"),
    ("isin_reinvestment", "reinvestment"),
    ("isin_growth", "growth"),
    ("nav", "net asset value"),
    ("repurchase_price", "repurchase"),
    ("sale_price", "sale price"),
    ("date", "date"),
]


@dataclass(frozen=True)
class NavRecord:
    """One scheme/plan NAV observation with its AMC + category context."""

    amc: str | None
    category: str | None
    scheme_code: str
    scheme_name: str
    isin_growth: str | None
    isin_reinvestment: str | None
    nav: float | None
    date: str | None
    repurchase_price: float | None = None
    sale_price: float | None = None


@dataclass
class NavFile:
    """Structured view of an AMFI NAV feed."""

    records: list[NavRecord] = field(default_factory=list)
    amcs: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    as_of: str | None = None

    # Provenance (filled by the caller/orchestrator).
    source_url: str | None = None
    source_hash: str | None = None


def _to_number(token: str | None) -> float | None:
    token = (token or "").strip().replace(",", "")
    if token in ("", "-", "N.A.", "NA", "N/A"):
        return None
    try:
        return float(token)
    except ValueError:
        return None


def _clean_isin(token: str) -> str | None:
    token = token.strip()
    return token if token and token != "-" else None


def _map_columns(header: list[str]) -> dict[str, int]:
    """Map canonical field names to column indices for this feed's header."""
    columns: dict[str, int] = {}
    for index, name in enumerate(header):
        lowered = name.strip().lower()
        for field_name, needle in _COLUMN_MATCHERS:
            if field_name in columns:
                continue
            if needle in lowered:
                columns[field_name] = index
    return columns


def _get(cells: list[str], columns: dict[str, int], field_name: str) -> str | None:
    index = columns.get(field_name)
    if index is None or index >= len(cells):
        return None
    return cells[index].strip()


def parse_nav_file(
    text: str,
    *,
    source_url: str | None = None,
    source_hash: str | None = None,
) -> NavFile:
    """Parse an AMFI NAV feed (daily or historical) into a :class:`NavFile`."""
    header: list[str] | None = None
    columns: dict[str, int] = {}
    category: str | None = None
    amc: str | None = None

    records: list[NavRecord] = []
    amcs: list[str] = []
    categories: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if ";" in line:
            cells = line.split(";")
            if header is None and "scheme code" in line.lower():
                header = [c.strip() for c in cells]
                columns = _map_columns(header)
                continue
            if header is not None and len(cells) == len(header):
                code = _get(cells, columns, "scheme_code") or ""
                if code.isdigit():
                    records.append(
                        NavRecord(
                            amc=amc,
                            category=category,
                            scheme_code=code,
                            scheme_name=_get(cells, columns, "scheme_name") or "",
                            isin_growth=_clean_isin(_get(cells, columns, "isin_growth") or ""),
                            isin_reinvestment=_clean_isin(
                                _get(cells, columns, "isin_reinvestment") or ""
                            ),
                            nav=_to_number(_get(cells, columns, "nav")),
                            date=_get(cells, columns, "date"),
                            repurchase_price=_to_number(_get(cells, columns, "repurchase_price")),
                            sale_price=_to_number(_get(cells, columns, "sale_price")),
                        )
                    )
            continue

        # Grouping line: a scheme category or an AMC name.
        if _CATEGORY_RE.search(line):
            category = line
            if line not in categories:
                categories.append(line)
        else:
            amc = line
            if line not in amcs:
                amcs.append(line)

    as_of = records[0].date if records else None
    return NavFile(
        records=records,
        amcs=amcs,
        categories=categories,
        as_of=as_of,
        source_url=source_url,
        source_hash=source_hash,
    )


__all__ = ["parse_nav_file", "NavFile", "NavRecord"]
