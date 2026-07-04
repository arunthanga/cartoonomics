import pytest

from cartoonomics.connectors.base import USER_AGENT, BaseConnector, RawArtifact
from cartoonomics.connectors.exchanges import BSEConnector, NSEConnector
from cartoonomics.connectors.fixture import FixtureConnector
from cartoonomics.connectors.robots import RobotsDisallowed, RobotsPolicy
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


class _RobotsConnector(BaseConnector):
    """Serves a canned robots.txt for the origin and a document otherwise."""

    source = "robots-stub"

    def __init__(self, robots_txt: str | bytes | None = "", **kwargs):
        super().__init__(**kwargs)
        self.robots_txt = robots_txt
        self.robots_fetches = 0
        self.doc_fetches = 0

    def _fetch_bytes(self, url):
        if url.endswith("/robots.txt"):
            self.robots_fetches += 1
            if self.robots_txt is None:
                raise ConnectionError("no robots.txt")
            body = self.robots_txt
            return (body.encode() if isinstance(body, str) else body), "text/plain"
        self.doc_fetches += 1
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


@pytest.mark.unit
def test_exchange_connectors_respect_robots_by_default():
    assert NSEConnector().respect_robots is True
    assert BSEConnector().respect_robots is True


@pytest.mark.unit
def test_robots_policy_parses_allow_deny_and_crawl_delay():
    policy = RobotsPolicy.from_text(
        "User-agent: cartoonomics-bot\n"
        "Disallow: /app/\n"
        "Crawl-delay: 5\n",
        user_agent=USER_AGENT,
    )
    assert policy.can_fetch("https://x.example/filings/report.pdf") is True
    assert policy.can_fetch("https://x.example/app/secret") is False
    assert policy.crawl_delay() == 5.0


@pytest.mark.unit
def test_robots_url_is_derived_from_origin():
    assert (
        RobotsPolicy.robots_url_for("https://x.example/a/b?c=1")
        == "https://x.example/robots.txt"
    )


@pytest.mark.unit
def test_fetch_blocked_by_robots_raises():
    conn = _RobotsConnector(
        robots_txt="User-agent: *\nDisallow: /app/\n",
        respect_robots=True,
        min_interval_s=0,
    )
    with pytest.raises(RobotsDisallowed):
        conn.fetch("https://x.example/app/secret", sleep=lambda s: None, now=lambda: 0.0)
    assert conn.doc_fetches == 0  # never touched the disallowed document


@pytest.mark.unit
def test_fetch_allowed_by_robots_succeeds_and_caches_robots():
    conn = _RobotsConnector(
        robots_txt="User-agent: *\nDisallow: /app/\n",
        respect_robots=True,
        min_interval_s=0,
    )
    a1 = conn.fetch("https://x.example/filings/1.csv", sleep=lambda s: None, now=lambda: 0.0)
    a2 = conn.fetch("https://x.example/filings/2.csv", sleep=lambda s: None, now=lambda: 0.0)
    assert a1.content == a2.content == b"CF,Operating,1"
    assert conn.doc_fetches == 2
    assert conn.robots_fetches == 1  # robots.txt fetched once per origin, then cached


@pytest.mark.unit
def test_crawl_delay_raises_effective_rate_limit():
    conn = _RobotsConnector(
        robots_txt="User-agent: *\nCrawl-delay: 10\n",
        respect_robots=True,
        min_interval_s=1.0,
    )
    sleeps: list[float] = []
    conn._last_fetch_ts = 100.0
    conn.fetch("https://x.example/filings/1.csv", sleep=lambda s: sleeps.append(s), now=lambda: 100.0)
    assert sleeps and sleeps[-1] == pytest.approx(10.0)  # crawl-delay > min_interval_s


@pytest.mark.unit
def test_missing_robots_is_permissive():
    conn = _RobotsConnector(robots_txt=None, respect_robots=True, min_interval_s=0)
    artifact = conn.fetch("https://x.example/anything", sleep=lambda s: None, now=lambda: 0.0)
    assert artifact.content == b"CF,Operating,1"
