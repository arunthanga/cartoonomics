from datetime import datetime, timezone

import pytest

from cartoonomics.connectors.base import RawArtifact
from cartoonomics.parsing import parse_delimited, parse_financials, parse_pdf


@pytest.mark.unit
def test_parse_delimited_reads_rows_and_negatives():
    text = "CF,Net cash from operating activities,1850\nCF,Investing,(1200)\n"
    parsed = parse_delimited(text, entity_name="Acme", period="FY2024")
    assert parsed.by_label("Investing") == -1200.0
    assert parsed.by_label("Net cash from operating activities") == 1850.0


@pytest.mark.unit
def test_parse_delimited_skips_junk_and_unknown_statements():
    text = "CF,Good,10\nXX,Ignored,5\nCF,NotANumber,abc\n\n"
    parsed = parse_delimited(text, entity_name="Acme", period="FY2024")
    labels = [i.label for i in parsed.items]
    assert labels == ["Good"]


@pytest.mark.unit
def test_by_label_missing_raises():
    parsed = parse_delimited("CF,Only,1", entity_name="Acme", period="FY2024")
    with pytest.raises(KeyError):
        parsed.by_label("Absent")


@pytest.mark.unit
def test_parse_pdf_reads_bordered_table(make_cashflow_pdf):
    data = make_cashflow_pdf()
    parsed = parse_pdf(data, entity_name="Acme", period="FY2024")
    assert parsed.by_label("Net cash from operating activities") == 1850.0
    assert parsed.by_label("Net cash used in investing activities") == -1200.0


@pytest.mark.unit
def test_parse_financials_dispatches_on_media_type(make_cashflow_pdf):
    pdf_artifact = RawArtifact(
        source="BSE",
        source_url="x.pdf",
        content=make_cashflow_pdf(),
        media_type="application/pdf",
        fetched_at=datetime.now(timezone.utc),
        source_hash="h",
    )
    parsed = parse_financials(pdf_artifact, entity_name="Acme", period="FY2024")
    assert len(parsed.items) == 4

    csv_artifact = RawArtifact(
        source="BSE",
        source_url="x.csv",
        content=b"CF,Operating,1850",
        media_type="text/csv",
        fetched_at=datetime.now(timezone.utc),
        source_hash="h",
    )
    parsed_csv = parse_financials(csv_artifact, entity_name="Acme", period="FY2024")
    assert parsed_csv.by_label("Operating") == 1850.0
