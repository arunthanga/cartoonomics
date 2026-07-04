import json
from urllib.parse import parse_qs

import pytest

from cartoonomics.connectors.sebi_pms import (
    PMR_LANDING_URL,
    PortfolioManager,
    SebiPmsConnector,
)
from cartoonomics.parsing.sebi_pms import parse_pms_report
from cartoonomics.sebi_pms import scrape_reports

# --- Synthetic fixtures that mirror the real SEBI markup (kept tiny) -----------

LANDING_HTML = """
<form name="otherForm">
  <select name="pmrId" class="f_control">
    <option value="">-- Select the Portfolio Manager Name --</option>
    <option value="INP000006457@@INP000006457@@ABAKKUS ASSET MANAGER LLP">ABAKKUS ASSET MANAGER LLP</option>
    <option value="INP000000365@@INP000000365@@ALCHEMY CAPITAL MANAGEMENT PRIVATE LTD">ALCHEMY CAPITAL MANAGEMENT PRIVATE LTD</option>
  </select>
  <select name="year">
    <option value="">-- Select year --</option>
    <option value="2025">2025</option>
    <option value="2024">2024</option>
  </select>
  <select name="month">
    <option value="">-- Select month --</option>
    <option value="3">March</option>
  </select>
</form>
"""

REPORT_HTML = """
<div class="org-strong"><h3><strong><u>General Information</u></strong></h3></div>
<table class="statistics-table"><thead>
  <tr><th>Name of the Portfolio Manager</th><td>Abakkus Asset Manager Private Limited</td></tr>
  <tr><th>Registration Number</th><td>INP000006457</td></tr>
  <tr><th>Date of Registration</th><td>2019-03-14</td></tr>
  <tr><th>Registered Address of the Portfolio Manager</th><td>MUMBAI, MAHARASHTRA, INDIA</td></tr>
  <tr><th>Name of Principal Officer</th><td>Mr.Aman Chowhan</td></tr>
  <tr><th>No. of clients as on last day of the month</th><td>11258</td></tr>
  <tr><th>Total Assets under Management (AUM) as on last day of the month (Amount in INR crores)</th><td>18417.22000</td></tr>
</thead></table>

<div class="org-strong"><h3><strong>E. <u>Performance Data</u></strong></h3></div>
<table class="statistics-table">
  <thead>
    <tr><th colspan="3">Abakkus</th><th colspan="4">TWRR Returns (%)</th></tr>
    <tr><th>Strategy</th><th>Investment Approach</th><th>AUM (INR Cr.)</th>
        <th>1 Month</th><th>1 Year</th><th>3 Year</th><th>Since Inception</th></tr>
  </thead>
  <tbody>
    <tr><td rowspan="2">EQUITY</td></tr>
    <tr><td>Abakkus All Cap Approach</td><td>6,756.40</td><td>7.98</td><td>1.83</td><td>10.74</td><td>25.18</td></tr>
    <tr><td style="text-align: right;">Benchmark: BSE500TRI</td><td></td><td>7.32</td><td>5.96</td><td>13.74</td><td>13.2</td></tr>
  </tbody>
</table>
"""


# --- Connector: option enumeration --------------------------------------------

@pytest.mark.unit
def test_portfolio_manager_parses_registration_and_name():
    pm = PortfolioManager.from_option(
        "INP000006457@@INP000006457@@ABAKKUS ASSET MANAGER LLP", "ABAKKUS ASSET MANAGER LLP"
    )
    assert pm.registration_number == "INP000006457"
    assert pm.name == "ABAKKUS ASSET MANAGER LLP"
    assert pm.option_value.endswith("ABAKKUS ASSET MANAGER LLP")


@pytest.mark.unit
def test_list_portfolio_managers_skips_placeholder():
    conn = SebiPmsConnector()
    managers = conn.list_portfolio_managers(landing_html=LANDING_HTML)
    assert [m.registration_number for m in managers] == ["INP000006457", "INP000000365"]


@pytest.mark.unit
def test_available_years_parsed_newest_first():
    conn = SebiPmsConnector()
    assert conn.available_years(landing_html=LANDING_HTML) == [2025, 2024]


# --- Connector: report POST recipe --------------------------------------------

class _RecordingSebiConnector(SebiPmsConnector):
    """Capture the URL/data/headers of the POST instead of hitting the network."""

    def __init__(self, **kwargs):
        kwargs.setdefault("min_interval_s", 0)
        super().__init__(**kwargs)
        self.calls: list[dict] = []

    def _fetch_bytes(self, url, *, data=None, headers=None):
        self.calls.append({"url": url, "data": data, "headers": headers})
        return REPORT_HTML.encode("utf-8"), "text/html"


@pytest.mark.unit
def test_fetch_report_posts_form_with_waf_headers():
    conn = _RecordingSebiConnector()
    pm = PortfolioManager.from_option("INP000006457@@INP000006457@@ABAKKUS", "ABAKKUS")
    artifact = conn.fetch_report(pm, 2025, 3, sleep=lambda s: None, now=lambda: 0.0)

    call = conn.calls[0]
    assert call["url"] == PMR_LANDING_URL
    form = parse_qs(call["data"].decode())
    assert form["pmrId"] == ["INP000006457@@INP000006457@@ABAKKUS"]
    assert form["year"] == ["2025"] and form["month"] == ["3"]
    # SEBI's WAF blocks POSTs missing these headers.
    assert call["headers"]["Origin"] == "https://www.sebi.gov.in"
    assert call["headers"]["Referer"] == PMR_LANDING_URL
    assert call["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    assert artifact.source == "SEBI_PMS"
    assert artifact.source_hash  # provenance captured


@pytest.mark.unit
def test_fetch_report_rejects_bad_month():
    conn = _RecordingSebiConnector()
    pm = PortfolioManager.from_option("INP@@INP@@X", "X")
    with pytest.raises(ValueError):
        conn.fetch_report(pm, 2025, 13, sleep=lambda s: None, now=lambda: 0.0)


@pytest.mark.unit
def test_base_fetch_get_path_unchanged_when_no_data():
    """A GET (no data/headers) must not forward extra kwargs to _fetch_bytes."""
    seen: list[dict] = []

    class _GetOnly(SebiPmsConnector):
        def _fetch_bytes(self, url):  # legacy GET-only signature
            seen.append({"url": url})
            return b"<html></html>", "text/html"

    conn = _GetOnly(min_interval_s=0)
    conn.fetch(PMR_LANDING_URL, sleep=lambda s: None, now=lambda: 0.0)
    assert seen == [{"url": PMR_LANDING_URL}]


# --- Parser -------------------------------------------------------------------

@pytest.mark.unit
def test_parse_report_extracts_general_information():
    report = parse_pms_report(REPORT_HTML, year=2025, month=3, source_hash="deadbeef")
    assert report.name == "Abakkus Asset Manager Private Limited"
    assert report.registration_number == "INP000006457"
    assert report.registration_date == "2019-03-14"
    assert report.num_clients == 11258
    assert report.total_aum_inr_crore == pytest.approx(18417.22)
    assert report.year == 2025 and report.month == 3
    assert report.source_hash == "deadbeef"
    assert len(report.tables) == 2  # every table retained (FR-1.6)


@pytest.mark.unit
def test_parse_report_extracts_performance_rows_and_benchmark():
    report = parse_pms_report(REPORT_HTML)
    approaches = [(p.investment_approach, p.is_benchmark) for p in report.performance]
    assert ("Abakkus All Cap Approach", False) in approaches
    assert ("Benchmark: BSE500TRI", True) in approaches

    strategy = next(p for p in report.performance if not p.is_benchmark)
    assert strategy.strategy_group == "EQUITY"
    assert strategy.aum_inr_crore == pytest.approx(6756.40)  # comma stripped
    assert strategy.returns["1 Month"] == pytest.approx(7.98)
    assert strategy.returns["Since Inception"] == pytest.approx(25.18)

    benchmark = next(p for p in report.performance if p.is_benchmark)
    assert benchmark.aum_inr_crore is None  # blank cell -> None


@pytest.mark.unit
def test_parse_report_handles_missing_sections_gracefully():
    report = parse_pms_report("<html><body>no tables here</body></html>")
    assert report.name is None
    assert report.total_aum_inr_crore is None
    assert report.performance == []


# --- Orchestration ------------------------------------------------------------

class _StubConnector(SebiPmsConnector):
    """Serve a canned report without any network access."""

    def __init__(self, **kwargs):
        kwargs.setdefault("min_interval_s", 0)
        super().__init__(**kwargs)
        self.report_calls = 0

    def fetch_report(self, manager, year, month, **kwargs):
        from datetime import datetime, timezone

        from cartoonomics.connectors.base import RawArtifact

        self.report_calls += 1
        content = REPORT_HTML.encode("utf-8")
        return RawArtifact(
            source="SEBI_PMS",
            source_url=PMR_LANDING_URL,
            content=content,
            media_type="text/html",
            fetched_at=datetime.now(timezone.utc),
            source_hash=RawArtifact.hash_content(content),
        )


def _managers():
    return [
        PortfolioManager.from_option("INP000006457@@INP000006457@@ABAKKUS", "ABAKKUS"),
        PortfolioManager.from_option("INP000000365@@INP000000365@@ALCHEMY", "ALCHEMY"),
    ]


@pytest.mark.unit
def test_scrape_reports_writes_raw_parsed_and_manifest(tmp_path):
    conn = _StubConnector()
    results = scrape_reports(
        conn, out_dir=tmp_path, years=[2025], months=[3], managers=_managers(),
    )
    assert [r.status for r in results] == ["fetched", "fetched"]

    raw = tmp_path / "raw" / "INP000006457" / "2025-03.html"
    parsed = tmp_path / "parsed" / "INP000006457" / "2025-03.json"
    assert raw.exists() and parsed.exists()
    data = json.loads(parsed.read_text())
    assert data["name"] == "Abakkus Asset Manager Private Limited"

    manifest_lines = (tmp_path / "manifest.jsonl").read_text().strip().splitlines()
    assert len(manifest_lines) == 2
    assert json.loads(manifest_lines[0])["registration_number"] == "INP000006457"


@pytest.mark.unit
def test_scrape_reports_is_idempotent(tmp_path):
    conn = _StubConnector()
    scrape_reports(conn, out_dir=tmp_path, years=[2025], months=[3], managers=_managers())
    first_calls = conn.report_calls

    results = scrape_reports(conn, out_dir=tmp_path, years=[2025], months=[3], managers=_managers())
    assert conn.report_calls == first_calls  # nothing re-fetched
    assert all(r.status == "skipped" for r in results)


@pytest.mark.unit
def test_scrape_reports_honours_max_reports_cap(tmp_path):
    conn = _StubConnector()
    results = scrape_reports(
        conn, out_dir=tmp_path, years=[2025], months=[1, 2, 3], managers=_managers(),
        max_reports=2,
    )
    assert sum(1 for r in results if r.status == "fetched") == 2


@pytest.mark.unit
def test_scrape_reports_surfaces_errors_without_stopping(tmp_path):
    class _Boom(_StubConnector):
        def fetch_report(self, manager, year, month, **kwargs):
            raise ConnectionError("boom")

    results = scrape_reports(
        _Boom(), out_dir=tmp_path, years=[2025], months=[3], managers=_managers(),
    )
    assert all(r.status == "error" for r in results)
    assert "ConnectionError" in results[0].error
