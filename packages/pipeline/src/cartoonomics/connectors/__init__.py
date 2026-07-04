"""Source connectors (§7.1 Data Acquisition).

Each connector is polite (FR-1.2), captures provenance (FR-1.3), and yields an
immutable :class:`RawArtifact` (FR-1.5). Connectors are isolated so one source
breaking cannot take down others (TA-3).
"""

from cartoonomics.connectors.base import BaseConnector, RawArtifact
from cartoonomics.connectors.fixture import FixtureConnector

__all__ = ["BaseConnector", "RawArtifact", "FixtureConnector"]
