"""AMFI (Association of Mutual Funds in India) connector.

AMFI is the SEBI-recognised industry body for Indian mutual funds and the
**authentic, machine-readable source of record** for daily NAVs across the whole
industry — no HTML scraping required (FR-1.2, CMP-1/CMP-6). Two feeds are used:

* **NAVAll.txt** — the full daily NAV file for every open/close/interval scheme
  of every AMC (``https://portal.amfiindia.com/spages/NAVAll.txt``).
* **NAV history report** — NAV for a date range, optionally scoped to one AMC
  (``https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx``).

Both are semicolon-delimited text; :mod:`cartoonomics.parsing.amfi` parses them
with a single header-driven parser. Network I/O is confined to
:meth:`_fetch_bytes` so the URL-building logic stays unit-testable offline.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
from datetime import date

from cartoonomics.connectors.base import BaseConnector, RawArtifact

NAV_ALL_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
NAV_HISTORY_URL = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"


def _fmt_date(value: date | str) -> str:
    """Format a date the AMFI report expects, e.g. ``03-Jul-2026``."""
    if isinstance(value, date):
        return value.strftime("%d-%b-%Y")
    return value


class AmfiConnector(BaseConnector):
    """Fetch AMFI's official daily and historical NAV feeds."""

    source = "AMFI"

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("min_interval_s", 2.0)
        kwargs.setdefault("respect_robots", True)
        super().__init__(**kwargs)

    def _fetch_bytes(self, url: str) -> tuple[bytes, str]:  # pragma: no cover - network
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
            content = response.read()
            media_type = response.headers.get_content_type()
        return content, media_type

    def fetch_nav_all(self, **fetch_kwargs) -> RawArtifact:
        """Fetch the full daily NAV file for every scheme of every AMC."""
        return self.fetch(NAV_ALL_URL, **fetch_kwargs)

    def fetch_nav_history(
        self,
        from_date: date | str,
        to_date: date | str,
        *,
        mf_code: int | str | None = None,
        **fetch_kwargs,
    ) -> RawArtifact:
        """Fetch NAV history over ``[from_date, to_date]`` (optionally one AMC).

        ``mf_code`` is AMFI's internal mutual-fund id; when omitted the report
        covers all AMCs for the range (larger, so callers should keep the range
        short and be patient/polite).
        """
        params = {"tp": "1", "frmdt": _fmt_date(from_date), "todt": _fmt_date(to_date)}
        if mf_code is not None:
            params["mf"] = str(mf_code)
        url = f"{NAV_HISTORY_URL}?{urllib.parse.urlencode(params)}"
        return self.fetch(url, **fetch_kwargs)


__all__ = ["AmfiConnector", "NAV_ALL_URL", "NAV_HISTORY_URL"]
