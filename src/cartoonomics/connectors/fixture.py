"""Offline connector that serves bundled sample filings.

Used by the demo pipeline and tests so the full scrape->cartoon loop runs
without network access. It exercises the same polite/provenance machinery as a
real connector, but reads bytes from disk instead of HTTP.
"""

from __future__ import annotations

from pathlib import Path

from cartoonomics.connectors.base import BaseConnector

_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".csv": "text/csv",
    ".tsv": "text/tab-separated-values",
    ".txt": "text/plain",
}


class FixtureConnector(BaseConnector):
    """Serve local files as if fetched from a source-of-record."""

    def __init__(self, base_dir: Path, *, source: str = "fixture", **kwargs) -> None:
        super().__init__(**kwargs)
        self.source = source
        self.base_dir = Path(base_dir)

    def _fetch_bytes(self, url: str) -> tuple[bytes, str]:
        # ``url`` is a filename relative to base_dir for the fixture connector.
        path = self.base_dir / url
        content = path.read_bytes()
        media_type = _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
        return content, media_type
