"""Source connectors (§7.1 Data Acquisition).

Each connector is polite (FR-1.2) — honouring the source's ``robots.txt`` rules
and advertised crawl delay (see :mod:`cartoonomics.connectors.robots`) — captures
provenance (FR-1.3), and yields an immutable :class:`RawArtifact` (FR-1.5).
Connectors are isolated so one source breaking cannot take down others (TA-3).
"""

from cartoonomics.connectors.amfi import AmfiConnector
from cartoonomics.connectors.base import BaseConnector, RawArtifact
from cartoonomics.connectors.fixture import FixtureConnector
from cartoonomics.connectors.robots import RobotsDisallowed, RobotsPolicy
from cartoonomics.connectors.sebi_pms import PortfolioManager, SebiPmsConnector

__all__ = [
    "BaseConnector",
    "RawArtifact",
    "FixtureConnector",
    "RobotsPolicy",
    "RobotsDisallowed",
    "SebiPmsConnector",
    "PortfolioManager",
    "AmfiConnector",
]
