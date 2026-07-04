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

    def __init__(self, *, min_interval_s: float = 1.0, max_retries: int = 3) -> None:
        self.min_interval_s = min_interval_s
        self.max_retries = max_retries
        self._last_fetch_ts: float = 0.0

    @abstractmethod
    def _fetch_bytes(self, url: str) -> tuple[bytes, str]:
        """Return ``(content, media_type)`` for ``url``. Implemented per source."""

    def _respect_rate_limit(self, *, sleep=time.sleep, now=time.monotonic) -> None:
        """Block until at least ``min_interval_s`` has elapsed since last fetch."""
        elapsed = now() - self._last_fetch_ts
        wait = self.min_interval_s - elapsed
        if wait > 0:
            sleep(wait)
        self._last_fetch_ts = now()

    def fetch(self, url: str, *, sleep=time.sleep, now=time.monotonic) -> RawArtifact:
        """Politely fetch ``url`` with retry/backoff and capture provenance."""
        self._respect_rate_limit(sleep=sleep, now=now)

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                content, media_type = self._fetch_bytes(url)
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
