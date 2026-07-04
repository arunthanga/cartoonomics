"""NSE / BSE connectors (reference implementations of the polite pattern).

IMPORTANT (compliance §17 — hard gate): scraping these exchanges is subject to
each site's terms of use and ``robots.txt``. Prefer official APIs, bulk data,
and announcement feeds over HTML scraping (FR-1.2, CMP-1, CMP-6). These classes
implement the *shape* of a compliant connector — a proper user agent, rate
limiting, retry/backoff, and provenance — but no connector ships until it has
cleared the §17 gate and a source-register entry exists (CMP-5).

Network access is confined to :meth:`_fetch_bytes` so the surrounding logic is
testable offline; the demo pipeline uses :class:`FixtureConnector` instead.
"""

from __future__ import annotations

import urllib.request

from cartoonomics.connectors.base import USER_AGENT, BaseConnector


class _HttpConnector(BaseConnector):
    """Shared HTTP fetch via stdlib urllib with an identifying user agent."""

    def _fetch_bytes(self, url: str) -> tuple[bytes, str]:  # pragma: no cover - network
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            content = response.read()
            media_type = response.headers.get_content_type()
        return content, media_type


class NSEConnector(_HttpConnector):
    """National Stock Exchange connector (announcements / corporate filings)."""

    source = "NSE"

    def __init__(self, **kwargs) -> None:
        # NSE is rate-sensitive; be conservative by default.
        kwargs.setdefault("min_interval_s", 3.0)
        super().__init__(**kwargs)


class BSEConnector(_HttpConnector):
    """Bombay Stock Exchange connector (announcements / corporate filings)."""

    source = "BSE"

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("min_interval_s", 3.0)
        super().__init__(**kwargs)
