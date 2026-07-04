"""Shared pytest fixtures and helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cartoonomics.parsing import LineItem, ParsedFinancials

FIXED_TS = datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def fixed_ts() -> datetime:
    return FIXED_TS


@pytest.fixture
def demo_financials() -> ParsedFinancials:
    """A deterministic parsed cashflow statement used across tests."""
    return ParsedFinancials(
        entity_name="Acme Industries Ltd",
        period="FY2024",
        items=[
            LineItem("CF", "Net cash from operating activities", 1850.0),
            LineItem("CF", "Net cash used in investing activities", -1200.0),
            LineItem("CF", "Net cash from financing activities", -300.0),
            LineItem("CF", "Net increase in cash and cash equivalents", 350.0),
        ],
    )


@pytest.fixture
def make_cashflow_pdf(tmp_path: Path):
    """Return a factory that writes a bordered-table cashflow PDF and returns bytes."""

    def _make(rows: list[tuple[str, str, str]] | None = None) -> bytes:
        from fpdf import FPDF

        rows = rows or [
            ("CF", "Net cash from operating activities", "1850"),
            ("CF", "Net cash used in investing activities", "(1200)"),
            ("CF", "Net cash from financing activities", "(300)"),
            ("CF", "Net increase in cash and cash equivalents", "350"),
        ]
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        for stmt, label, value in rows:
            pdf.cell(20, 8, stmt, border=1)
            pdf.cell(130, 8, label, border=1)
            pdf.cell(40, 8, value, border=1, new_x="LMARGIN", new_y="NEXT")
        out = tmp_path / "filing.pdf"
        pdf.output(str(out))
        return out.read_bytes()

    return _make
