"""Extract structured financial line items from raw documents.

Two extractors are provided:

* :func:`parse_pdf` — reads a real PDF using ``pdfplumber`` (optional import).
* :func:`parse_delimited` — reads pipe/comma/tab delimited text.

Both produce the same :class:`ParsedFinancials` intermediate so downstream
analysis is independent of the source format. :func:`parse_financials`
dispatches on the artifact's media type.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from cartoonomics.connectors.base import RawArtifact

# Statement classifier: which financial statement a line item belongs to.
STATEMENT_PL = "PL"
STATEMENT_BS = "BS"
STATEMENT_CF = "CF"

_NUMBER_RE = re.compile(r"^-?\(?\d[\d,]*\.?\d*\)?$")


@dataclass(frozen=True)
class LineItem:
    """A single parsed financial line (canonical model §13 ``Financials``)."""

    statement: str
    label: str
    value: float
    unit: str = "INR_CRORE"


@dataclass
class ParsedFinancials:
    """Structured output of parsing one filing."""

    entity_name: str
    period: str
    items: list[LineItem] = field(default_factory=list)

    def by_label(self, label: str) -> float:
        """Return the value for ``label`` (case-insensitive), or raise ``KeyError``."""
        target = label.strip().lower()
        for item in self.items:
            if item.label.strip().lower() == target:
                return item.value
        raise KeyError(label)


def _to_float(token: str) -> float:
    """Parse an accounting-formatted number. Parentheses denote negatives."""
    token = token.strip()
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()").replace(",", "")
    value = float(token)
    return -value if negative else value


def _rows_to_financials(
    rows: list[list[str]],
    *,
    entity_name: str,
    period: str,
) -> ParsedFinancials:
    """Convert extracted ``[statement, label, value]`` rows to ParsedFinancials."""
    items: list[LineItem] = []
    for row in rows:
        cells = [c.strip() for c in row if c is not None and c.strip() != ""]
        if len(cells) < 3:
            continue
        statement, label, raw_value = cells[0], cells[1], cells[2]
        if statement.upper() not in {STATEMENT_PL, STATEMENT_BS, STATEMENT_CF}:
            continue
        if not _NUMBER_RE.match(raw_value):
            continue
        items.append(
            LineItem(statement=statement.upper(), label=label, value=_to_float(raw_value))
        )
    return ParsedFinancials(entity_name=entity_name, period=period, items=items)


def parse_delimited(
    text: str,
    *,
    entity_name: str,
    period: str,
    delimiter: str = ",",
) -> ParsedFinancials:
    """Parse delimited text of ``statement<delim>label<delim>value`` rows."""
    rows = [line.split(delimiter) for line in text.splitlines() if line.strip()]
    return _rows_to_financials(rows, entity_name=entity_name, period=period)


def parse_pdf(data: bytes, *, entity_name: str, period: str) -> ParsedFinancials:
    """Parse a PDF's tables into ParsedFinancials using pdfplumber.

    The PDF is expected to contain a table whose columns are
    ``statement | label | value``. Falls back to line-based extraction when no
    ruled table is detected.
    """
    try:
        import pdfplumber  # noqa: PLC0415  (optional heavy dependency)
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "parse_pdf requires pdfplumber; install it or use parse_delimited"
        ) from exc

    import io

    rows: list[list[str]] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                rows.extend(table)
            if not rows:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    rows.append(line.split())
    return _rows_to_financials(rows, entity_name=entity_name, period=period)


def parse_financials(artifact: RawArtifact, *, entity_name: str, period: str) -> ParsedFinancials:
    """Dispatch parsing based on the artifact's media type."""
    if artifact.media_type == "application/pdf":
        return parse_pdf(artifact.content, entity_name=entity_name, period=period)
    text = artifact.content.decode("utf-8")
    delimiter = "\t" if "\t" in text else ","
    return parse_delimited(text, entity_name=entity_name, period=period, delimiter=delimiter)
