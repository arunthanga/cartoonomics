"""SEBI Portfolio Manager Monthly Report (PMR) connector.

SEBI publishes a *Portfolio Manager Monthly Report* for every registered
Portfolio Management Service (PMS) provider at::

    https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doPmr=yes

The page is a form: pick a Portfolio Manager (``pmrId``), a ``year`` and a
``month`` and POST it back to the same endpoint, which returns the monthly
report as an HTML page (labelled tables of AUM, clients, funds flow and TWRR
performance). Despite the common assumption, the report is **HTML, not a PDF**;
the same endpoint can also emit Excel/XML, but the XML uses opaque SSRS
``TextboxNNN`` field names, so the labelled HTML is the better parse target
(see :mod:`cartoonomics.parsing.sebi_pms`).

Compliance (§17 — hard gate): SEBI's ``robots.txt`` only disallows ``/js`` and
``/css``; the PMR path is permitted. This connector identifies honestly via the
research :data:`~cartoonomics.connectors.base.USER_AGENT` and rate-limits itself
(FR-1.2). SEBI's WAF rejects form POSTs that lack browser-style ``Referer`` /
``Origin`` / ``Content-Type`` headers, so those are sent on the report POST.
Network I/O is confined to :meth:`_fetch_bytes` so the enumeration/POST logic is
unit-testable offline.
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
from dataclasses import dataclass

from cartoonomics.connectors.base import BaseConnector, RawArtifact

PMR_LANDING_URL = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doPmr=yes"
_ORIGIN = "https://www.sebi.gov.in"

_MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}

# <select name="X"> ... </select>  and each <option value="V">Label</option>.
_SELECT_RE = re.compile(r'<select[^>]*\bname="([^"]+)"[^>]*>(.*?)</select>', re.DOTALL | re.IGNORECASE)
_OPTION_RE = re.compile(r'<option\s+value="([^"]*)"[^>]*>(.*?)</option>', re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class PortfolioManager:
    """A registered Portfolio Manager as listed in the ``pmrId`` dropdown.

    ``option_value`` is the raw ``INPxxxx@@INPxxxx@@NAME`` string the form
    expects back verbatim; ``registration_number`` and ``name`` are parsed from
    it for convenience/provenance.
    """

    registration_number: str
    name: str
    option_value: str

    @classmethod
    def from_option(cls, value: str, label: str) -> "PortfolioManager":
        parts = value.split("@@")
        reg = parts[0].strip() if parts else value.strip()
        name = parts[-1].strip() if len(parts) >= 3 else label.strip()
        return cls(registration_number=reg, name=name, option_value=value)


class SebiPmsConnector(BaseConnector):
    """Enumerate Portfolio Managers and fetch their SEBI monthly reports."""

    source = "SEBI_PMS"

    def __init__(self, **kwargs) -> None:
        # SEBI is a public regulator site; be conservative and polite by default.
        kwargs.setdefault("min_interval_s", 2.0)
        super().__init__(**kwargs)

    def _fetch_bytes(
        self,
        url: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[bytes, str]:  # pragma: no cover - network
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(url, data=data, headers=request_headers)
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
            content = response.read()
            media_type = response.headers.get_content_type()
        return content, media_type

    def fetch_landing(self, **fetch_kwargs) -> RawArtifact:
        """Fetch the PMR landing page (GET) that holds the selection dropdowns."""
        return self.fetch(PMR_LANDING_URL, **fetch_kwargs)

    def list_portfolio_managers(self, landing_html: str | None = None, **fetch_kwargs) -> list[PortfolioManager]:
        """Return every Portfolio Manager offered by the ``pmrId`` dropdown."""
        html = landing_html if landing_html is not None else self.fetch_landing(**fetch_kwargs).content.decode(
            "utf-8", errors="replace"
        )
        managers: list[PortfolioManager] = []
        for name, label in self._select_options(html, "pmrId"):
            if not name:  # skip the "-- Select --" placeholder (empty value)
                continue
            managers.append(PortfolioManager.from_option(name, label))
        return managers

    def available_years(self, landing_html: str | None = None, **fetch_kwargs) -> list[int]:
        """Return the years offered by the ``year`` dropdown (newest first)."""
        html = landing_html if landing_html is not None else self.fetch_landing(**fetch_kwargs).content.decode(
            "utf-8", errors="replace"
        )
        years = [int(v) for v, _ in self._select_options(html, "year") if v.strip().isdigit()]
        return years

    def fetch_report(
        self,
        manager: PortfolioManager,
        year: int,
        month: int,
        **fetch_kwargs,
    ) -> RawArtifact:
        """POST the form for ``manager``/``year``/``month`` and return the report HTML."""
        if month not in _MONTHS:
            raise ValueError(f"month must be 1..12, got {month!r}")
        form = {
            "currdate": "",
            "pmrId": manager.option_value,
            "year": str(year),
            "month": str(month),
        }
        data = urllib.parse.urlencode(form).encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": _ORIGIN,
            "Referer": PMR_LANDING_URL,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        return self.fetch(PMR_LANDING_URL, data=data, headers=headers, **fetch_kwargs)

    @staticmethod
    def _select_options(html: str, select_name: str) -> list[tuple[str, str]]:
        """Return ``(value, label)`` pairs for the named ``<select>`` in ``html``."""
        for name, body in _SELECT_RE.findall(html):
            if name != select_name:
                continue
            pairs = []
            for value, label in _OPTION_RE.findall(body):
                clean_label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", label)).strip()
                pairs.append((value.strip(), clean_label))
            return pairs
        return []


__all__ = ["SebiPmsConnector", "PortfolioManager", "PMR_LANDING_URL"]
