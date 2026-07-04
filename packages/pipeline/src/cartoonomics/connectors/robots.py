"""robots.txt-aware polite fetching (FR-1.2, CMP-1/CMP-2).

Good financial-data scrapers behave as honest citizens of every source they
touch. Document-first research tools such as **alpha-analyst.com** publish a
careful ``robots.txt`` and, in turn, only crawl paths a source has opted to
expose — obeying the site's allow/deny rules for their own user agent and any
advertised crawl delay. This module gives
:class:`~cartoonomics.connectors.base.BaseConnector` the same behaviour so a
connector never fetches a path a source has asked crawlers to leave alone
(FR-1.2: "respect ``robots.txt``, rate limits, and terms of use").

The policy is deliberately transport-agnostic: a connector supplies the fetched
``robots.txt`` bytes, so the rule evaluation is fully unit-testable offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser


class RobotsDisallowed(RuntimeError):
    """Raised when a source's ``robots.txt`` forbids fetching a URL."""

    def __init__(self, url: str, user_agent: str) -> None:
        super().__init__(f"robots.txt disallows user agent {user_agent!r} from fetching {url}")
        self.url = url
        self.user_agent = user_agent


@dataclass(frozen=True)
class RobotsPolicy:
    """The ``robots.txt`` rules for a single origin, scoped to one user agent."""

    user_agent: str
    _parser: RobotFileParser

    @classmethod
    def from_text(cls, text: str, *, user_agent: str) -> "RobotsPolicy":
        """Parse ``robots.txt`` ``text`` into a policy for ``user_agent``."""
        parser = RobotFileParser()
        parser.parse(text.splitlines())
        return cls(user_agent=user_agent, _parser=parser)

    @staticmethod
    def robots_url_for(url: str) -> str:
        """Return the canonical ``robots.txt`` URL for ``url``'s origin."""
        parts = urlsplit(url)
        return f"{parts.scheme}://{parts.netloc}/robots.txt"

    def can_fetch(self, url: str) -> bool:
        """Whether this user agent is allowed to fetch ``url``."""
        return self._parser.can_fetch(self.user_agent, url)

    def crawl_delay(self) -> float | None:
        """The crawl delay (seconds) this source advertises, if any."""
        delay = self._parser.crawl_delay(self.user_agent)
        return float(delay) if delay is not None else None
