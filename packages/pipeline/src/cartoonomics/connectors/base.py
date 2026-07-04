"""Connector base class: polite fetching + provenance capture.

Real network connectors (NSE/BSE) subclass :class:`BaseConnector` and implement
:meth:`_fetch_bytes`. The base class handles the cross-cutting concerns required
by the requirements doc:

* FR-1.2  polite: identifying user agent, rate limiting, retry with backoff.
* FR-1.3  provenance: source url, fetch timestamp, content hash.
* FR-1.5  raw-then-parsed: returns an immutable :class:`RawArtifact`.

Network I/O itself is deliberately behind :meth:`_fetch_bytes` so the polite +
provenance logic can be unit-tested without hitting the network.
"""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from cartoonomics.connectors.robots import RobotsDisallowed, RobotsPolicy

USER_AGENT = "cartoonomics-bot/0.1 (+research; contact: compliance@cartoonomics.example)"


@dataclass(frozen=True)
class RawArtifact:
    """An immutable fetched document plus its provenance (FR-1.3, FR-1.5)."""

    source: str
    source_url: str
    content: bytes
    media_type: str
    fetched_at: datetime
    source_hash: str

    @staticmethod
    def hash_content(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()


class BaseConnector(ABC):
    """Abstract, polite, provenance-capturing source connector."""

    #: Human-readable source-of-record name, e.g. "BSE".
    source: str = "unknown"

    def __init__(
        self,
        *,
        min_interval_s: float = 1.0,
        max_retries: int = 3,
        respect_robots: bool = False,
        user_agent: str = USER_AGENT,
    ) -> None:
        self.min_interval_s = min_interval_s
        self.max_retries = max_retries
        self.respect_robots = respect_robots
        self.user_agent = user_agent
        self._last_fetch_ts: float = 0.0
        self._robots_cache: dict[str, RobotsPolicy | None] = {}

    @abstractmethod
    def _fetch_bytes(self, url: str) -> tuple[bytes, str]:
        """Return ``(content, media_type)`` for ``url``. Implemented per source.

        Connectors that need to POST (e.g. a form-driven disclosure portal) accept
        optional ``data``/``headers`` keyword arguments; :meth:`fetch` only forwards
        them when a caller supplies them, so plain GET connectors keep the simple
        ``(self, url)`` signature.
        """

    def _respect_rate_limit(
        self, *, interval: float | None = None, sleep=time.sleep, now=time.monotonic
    ) -> None:
        """Block until at least ``interval`` (default ``min_interval_s``) has elapsed."""
        if interval is None:
            interval = self.min_interval_s
        elapsed = now() - self._last_fetch_ts
        wait = interval - elapsed
        if wait > 0:
            sleep(wait)
        self._last_fetch_ts = now()

    def _robots_policy_for(self, url: str) -> RobotsPolicy | None:
        """Return (and cache) the ``robots.txt`` policy for ``url``'s origin.

        A source with no reachable ``robots.txt`` imposes no restrictions, so a
        fetch failure is treated as "no policy" (permissive) rather than an error.
        """
        robots_url = RobotsPolicy.robots_url_for(url)
        if robots_url in self._robots_cache:
            return self._robots_cache[robots_url]
        try:
            content, _ = self._fetch_bytes(robots_url)
            policy: RobotsPolicy | None = RobotsPolicy.from_text(
                content.decode("utf-8", errors="replace"), user_agent=self.user_agent
            )
        except Exception:  # noqa: BLE001 - unreachable robots.txt => no restrictions
            policy = None
        self._robots_cache[robots_url] = policy
        return policy

    def fetch(
        self,
        url: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        sleep=time.sleep,
        now=time.monotonic,
    ) -> RawArtifact:
        """Politely fetch ``url`` with retry/backoff and capture provenance.

        When ``respect_robots`` is set, the source's ``robots.txt`` is consulted
        first: a disallowed path raises :class:`RobotsDisallowed`, and an
        advertised crawl delay raises the effective rate-limit interval.

        ``data``/``headers`` are optional: when given (e.g. for a POST form
        submission) they are forwarded to :meth:`_fetch_bytes`. When omitted the
        call is a plain GET, keeping simpler connectors unchanged.
        """
        fetch_kwargs: dict[str, object] = {}
        if data is not None:
            fetch_kwargs["data"] = data
        if headers is not None:
            fetch_kwargs["headers"] = headers

        interval = self.min_interval_s
        if self.respect_robots:
            policy = self._robots_policy_for(url)
            if policy is not None:
                if not policy.can_fetch(url):
                    raise RobotsDisallowed(url, self.user_agent)
                crawl_delay = policy.crawl_delay()
                if crawl_delay is not None:
                    interval = max(interval, crawl_delay)

        self._respect_rate_limit(interval=interval, sleep=sleep, now=now)

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                content, media_type = self._fetch_bytes(url, **fetch_kwargs)
                break
            except Exception as exc:  # noqa: BLE001 - retried and re-raised below
                last_error = exc
                if attempt == self.max_retries - 1:
                    raise
                sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s, ...
        else:  # pragma: no cover - defensive
            raise last_error if last_error else RuntimeError("fetch failed")

        return RawArtifact(
            source=self.source,
            source_url=url,
            content=content,
            media_type=media_type,
            fetched_at=datetime.now(timezone.utc),
            source_hash=RawArtifact.hash_content(content),
        )
