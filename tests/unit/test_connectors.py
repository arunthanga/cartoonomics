import pytest

from cartoonomics.connectors.base import BaseConnector, RawArtifact
from cartoonomics.connectors.exchanges import BSEConnector, NSEConnector
from cartoonomics.connectors.fixture import FixtureConnector
from cartoonomics.pipeline import DATA_DIR


class _StubConnector(BaseConnector):
    source = "stub"

    def __init__(self, *, fail_times: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.fail_times = fail_times
        self.calls = 0

    def _fetch_bytes(self, url):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ConnectionError("boom")
        return b"CF,Operating,1", "text/csv"


@pytest.mark.unit
def test_raw_artifact_hash_is_sha256():
    assert RawArtifact.hash_content(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


@pytest.mark.unit
def test_fetch_captures_provenance():
    conn = _StubConnector(min_interval_s=0)
    sleeps: list[float] = []
    artifact = conn.fetch("some/url", sleep=lambda s: sleeps.append(s), now=lambda: 100.0)
    assert artifact.source == "stub"
    assert artifact.source_url == "some/url"
    assert artifact.source_hash == RawArtifact.hash_content(b"CF,Operating,1")
    assert artifact.fetched_at.tzinfo is not None


@pytest.mark.unit
def test_rate_limit_sleeps_when_called_too_soon():
    conn = _StubConnector(min_interval_s=2.0)
    conn._last_fetch_ts = 100.0
    sleeps: list[float] = []
    conn._respect_rate_limit(sleep=lambda s: sleeps.append(s), now=lambda: 100.5)
    assert sleeps and sleeps[0] == pytest.approx(1.5)


@pytest.mark.unit
def test_fetch_retries_then_succeeds():
    conn = _StubConnector(fail_times=2, min_interval_s=0, max_retries=3)
    backoffs: list[float] = []
    artifact = conn.fetch("u", sleep=lambda s: backoffs.append(s), now=lambda: 0.0)
    assert conn.calls == 3
    assert artifact.content == b"CF,Operating,1"
    assert backoffs == [1, 2]  # exponential backoff before the two retries


@pytest.mark.unit
def test_fetch_reraises_after_exhausting_retries():
    conn = _StubConnector(fail_times=5, min_interval_s=0, max_retries=2)
    with pytest.raises(ConnectionError):
        conn.fetch("u", sleep=lambda s: None, now=lambda: 0.0)


@pytest.mark.unit
def test_fixture_connector_serves_sample_with_media_type():
    conn = FixtureConnector(base_dir=DATA_DIR, source="BSE")
    artifact = conn.fetch("sample_cashflow.csv", sleep=lambda s: None, now=lambda: 0.0)
    assert artifact.media_type == "text/csv"
    assert b"operating" in artifact.content.lower()


@pytest.mark.unit
def test_exchange_connectors_have_conservative_defaults():
    assert NSEConnector().source == "NSE"
    assert BSEConnector().source == "BSE"
    assert NSEConnector().min_interval_s == 3.0
