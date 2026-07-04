import json
from datetime import date

import pytest

from cartoonomics.amfi import scrape_nav_all, scrape_nav_history
from cartoonomics.connectors.amfi import (
    NAV_ALL_URL,
    NAV_HISTORY_URL,
    AmfiConnector,
    _fmt_date,
)
from cartoonomics.connectors.base import RawArtifact
from cartoonomics.parsing.amfi import parse_nav_file

# --- Synthetic fixtures mirroring the two AMFI feed layouts -------------------

# Daily NAVAll.txt: ISIN columns come *before* the scheme name; 6 columns.
DAILY_FEED = """Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
 
Open Ended Schemes(Debt Scheme - Banking and PSU Fund)
 
Aditya Birla Sun Life Mutual Fund
 
119551;INF209KA12Z1;INF209KA13Z9;Aditya Birla Sun Life Banking & PSU Debt Fund - DIRECT - IDCW;106.8042;03-Jul-2026
108273;INF209K01LV0;-;Aditya Birla Sun Life Banking & PSU Debt Fund - Regular Growth;387.3186;03-Jul-2026
 
Open Ended Schemes(Equity Scheme - Large Cap Fund)
 
Axis Mutual Fund
 
120465;INF846K01131;-;Axis Bluechip Fund - Direct Plan - Growth;N.A.;03-Jul-2026
"""

# History report: scheme name comes *before* ISINs; 8 columns incl. repurchase/sale.
HISTORY_FEED = """Scheme Code;Scheme Name;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Net Asset Value;Repurchase Price;Sale Price;Date

Open Ended Schemes ( Equity Scheme - Multi Cap Fund )


Axis Mutual Fund
149383;Axis Multicap Fund - Direct Growth;INF846K013E0;;18.79;;;01-Jun-2026
149383;Axis Multicap Fund - Direct Growth;INF846K013E0;;18.90;;;02-Jun-2026
"""


# --- Connector: URL building --------------------------------------------------

@pytest.mark.unit
def test_fmt_date_accepts_date_and_string():
    assert _fmt_date(date(2026, 7, 3)) == "03-Jul-2026"
    assert _fmt_date("05-Jun-2026") == "05-Jun-2026"


@pytest.mark.unit
def test_connector_defaults_are_polite():
    conn = AmfiConnector()
    assert conn.source == "AMFI"
    assert conn.respect_robots is True
    assert conn.min_interval_s == 2.0


class _RecordingAmfiConnector(AmfiConnector):
    """Serve canned feeds and record the fetched URLs (no network)."""

    def __init__(self, payload=DAILY_FEED, **kwargs):
        kwargs.setdefault("min_interval_s", 0)
        kwargs.setdefault("respect_robots", False)
        super().__init__(**kwargs)
        self.payload = payload
        self.urls: list[str] = []

    def _fetch_bytes(self, url):
        self.urls.append(url)
        return self.payload.encode("utf-8"), "text/plain"


@pytest.mark.unit
def test_fetch_nav_all_hits_official_url_and_captures_provenance():
    conn = _RecordingAmfiConnector()
    artifact = conn.fetch_nav_all(sleep=lambda s: None, now=lambda: 0.0)
    assert conn.urls == [NAV_ALL_URL]
    assert artifact.source == "AMFI"
    assert artifact.source_hash == RawArtifact.hash_content(DAILY_FEED.encode("utf-8"))


@pytest.mark.unit
def test_fetch_nav_history_builds_report_url_with_dates_and_mf():
    conn = _RecordingAmfiConnector(payload=HISTORY_FEED)
    conn.fetch_nav_history(
        date(2026, 6, 1), date(2026, 6, 5), mf_code=53, sleep=lambda s: None, now=lambda: 0.0
    )
    url = conn.urls[0]
    assert url.startswith(NAV_HISTORY_URL + "?")
    assert "frmdt=01-Jun-2026" in url
    assert "todt=05-Jun-2026" in url
    assert "mf=53" in url


# --- Parser: both layouts -----------------------------------------------------

@pytest.mark.unit
def test_parse_daily_feed_attaches_amc_and_category_context():
    nav = parse_nav_file(DAILY_FEED, source_hash="abc")
    assert len(nav.records) == 3
    assert nav.as_of == "03-Jul-2026"
    assert nav.source_hash == "abc"
    assert "Aditya Birla Sun Life Mutual Fund" in nav.amcs
    assert any("Large Cap" in c for c in nav.categories)

    first = nav.records[0]
    assert first.amc == "Aditya Birla Sun Life Mutual Fund"
    assert "Banking and PSU" in first.category
    assert first.scheme_code == "119551"
    assert first.isin_growth == "INF209KA12Z1"
    assert first.isin_reinvestment == "INF209KA13Z9"
    assert first.nav == pytest.approx(106.8042)

    # "-" ISIN becomes None; "N.A." NAV becomes None; context switches to Axis.
    axis = nav.records[-1]
    assert axis.amc == "Axis Mutual Fund"
    assert axis.isin_reinvestment is None
    assert axis.nav is None


@pytest.mark.unit
def test_parse_history_feed_uses_header_order_and_reads_all_dates():
    nav = parse_nav_file(HISTORY_FEED)
    assert len(nav.records) == 2
    assert {r.date for r in nav.records} == {"01-Jun-2026", "02-Jun-2026"}
    row = nav.records[0]
    assert row.scheme_code == "149383"
    assert row.scheme_name == "Axis Multicap Fund - Direct Growth"
    assert row.isin_growth == "INF846K013E0"
    assert row.nav == pytest.approx(18.79)


@pytest.mark.unit
def test_parse_ignores_junk_and_missing_header():
    nav = parse_nav_file("just some text\nwith no header\n")
    assert nav.records == []
    assert nav.as_of is None


# --- Orchestration ------------------------------------------------------------

@pytest.mark.unit
def test_scrape_nav_all_writes_raw_parsed_and_manifest(tmp_path):
    conn = _RecordingAmfiConnector()
    result = scrape_nav_all(conn, out_dir=tmp_path, sleep=lambda s: None, now=lambda: 0.0)
    assert result.status == "fetched"
    assert result.records == 3

    raw = tmp_path / "raw" / "nav_all_03_Jul_2026.txt"
    parsed = tmp_path / "parsed" / "nav_all_03_Jul_2026.json"
    assert raw.exists() and parsed.exists()
    data = json.loads(parsed.read_text())
    assert data["as_of"] == "03-Jul-2026"
    assert len(data["records"]) == 3

    manifest = (tmp_path / "manifest.jsonl").read_text().strip().splitlines()
    assert len(manifest) == 1
    assert json.loads(manifest[0])["feed"] == "nav_all"


@pytest.mark.unit
def test_scrape_nav_all_is_idempotent_by_date(tmp_path):
    conn = _RecordingAmfiConnector()
    scrape_nav_all(conn, out_dir=tmp_path, sleep=lambda s: None, now=lambda: 0.0)
    result = scrape_nav_all(conn, out_dir=tmp_path, sleep=lambda s: None, now=lambda: 0.0)
    assert result.status == "skipped"
    # manifest not appended a second time
    assert len((tmp_path / "manifest.jsonl").read_text().strip().splitlines()) == 1


@pytest.mark.unit
def test_scrape_nav_history_persists_named_by_range(tmp_path):
    conn = _RecordingAmfiConnector(payload=HISTORY_FEED)
    result = scrape_nav_history(
        conn, out_dir=tmp_path, from_date="01-Jun-2026", to_date="05-Jun-2026", mf_code=53,
        sleep=lambda s: None, now=lambda: 0.0,
    )
    assert result.feed == "nav_history"
    assert (tmp_path / "parsed" / "nav_history_01_Jun_2026_05_Jun_2026_mf53.json").exists()
