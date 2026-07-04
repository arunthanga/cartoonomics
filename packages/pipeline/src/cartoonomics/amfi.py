"""Orchestrate ingestion of AMFI's official NAV feeds.

Ties :class:`~cartoonomics.connectors.amfi.AmfiConnector` to
:func:`~cartoonomics.parsing.amfi.parse_nav_file`, honouring the pipeline's
cross-cutting rules: polite single connector (FR-1.2), **raw-then-parsed**
storage (FR-1.5), **idempotent** by NAV date (FR-1.4), and provenance appended
to ``manifest.jsonl`` (FR-1.3).

Run it as a module::

    python -m cartoonomics.amfi --out ./amfi_data                       # today's full NAV file
    python -m cartoonomics.amfi --out ./amfi_data --from 01-Jun-2026 --to 05-Jun-2026 --mf 53
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

from cartoonomics.connectors.amfi import AmfiConnector
from cartoonomics.connectors.base import RawArtifact
from cartoonomics.parsing.amfi import NavFile, parse_nav_file


@dataclasses.dataclass
class NavIngestResult:
    """Outcome of ingesting one NAV feed artifact."""

    feed: str  # "nav_all" | "nav_history"
    status: str  # "fetched" | "skipped"
    raw_path: str
    parsed_path: str
    records: int
    amcs: int
    categories: int
    as_of: str | None
    source_hash: str | None = None


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text)


def _persist(
    artifact: RawArtifact,
    nav_file: NavFile,
    *,
    feed: str,
    stem: str,
    out_dir: Path,
) -> NavIngestResult:
    raw_dir = out_dir / "raw"
    parsed_dir = out_dir / "parsed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / f"{stem}.txt"
    parsed_path = parsed_dir / f"{stem}.json"
    raw_path.write_bytes(artifact.content)
    parsed_path.write_text(
        json.dumps(dataclasses.asdict(nav_file), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with (out_dir / "manifest.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "feed": feed,
                    "as_of": nav_file.as_of,
                    "records": len(nav_file.records),
                    "amcs": len(nav_file.amcs),
                    "categories": len(nav_file.categories),
                    "source_url": artifact.source_url,
                    "source_hash": artifact.source_hash,
                    "fetched_at": artifact.fetched_at.isoformat(),
                    "raw_path": str(raw_path),
                    "parsed_path": str(parsed_path),
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    return NavIngestResult(
        feed=feed,
        status="fetched",
        raw_path=str(raw_path),
        parsed_path=str(parsed_path),
        records=len(nav_file.records),
        amcs=len(nav_file.amcs),
        categories=len(nav_file.categories),
        as_of=nav_file.as_of,
        source_hash=artifact.source_hash,
    )


def scrape_nav_all(
    connector: AmfiConnector,
    *,
    out_dir: Path,
    overwrite: bool = False,
    **fetch_kwargs,
) -> NavIngestResult:
    """Fetch and persist AMFI's full daily NAV file (every scheme, every AMC)."""
    out_dir = Path(out_dir)
    artifact = connector.fetch_nav_all(**fetch_kwargs)
    nav_file = parse_nav_file(
        artifact.content.decode("utf-8", errors="replace"),
        source_url=artifact.source_url,
        source_hash=artifact.source_hash,
    )
    stem = f"nav_all_{_slug(nav_file.as_of or 'unknown')}"
    if not overwrite and (out_dir / "parsed" / f"{stem}.json").exists():
        return NavIngestResult(
            "nav_all", "skipped",
            str(out_dir / "raw" / f"{stem}.txt"), str(out_dir / "parsed" / f"{stem}.json"),
            len(nav_file.records), len(nav_file.amcs), len(nav_file.categories), nav_file.as_of,
        )
    return _persist(artifact, nav_file, feed="nav_all", stem=stem, out_dir=out_dir)


def scrape_nav_history(
    connector: AmfiConnector,
    *,
    out_dir: Path,
    from_date: str,
    to_date: str,
    mf_code: int | str | None = None,
    **fetch_kwargs,
) -> NavIngestResult:
    """Fetch and persist AMFI NAV history for a date range (optionally one AMC)."""
    out_dir = Path(out_dir)
    artifact = connector.fetch_nav_history(from_date, to_date, mf_code=mf_code, **fetch_kwargs)
    nav_file = parse_nav_file(
        artifact.content.decode("utf-8", errors="replace"),
        source_url=artifact.source_url,
        source_hash=artifact.source_hash,
    )
    suffix = f"_mf{mf_code}" if mf_code is not None else ""
    stem = f"nav_history_{_slug(from_date)}_{_slug(to_date)}{suffix}"
    return _persist(artifact, nav_file, feed="nav_history", stem=stem, out_dir=out_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest AMFI official NAV feeds.")
    parser.add_argument("--out", type=Path, default=Path("amfi_data"), help="Output directory.")
    parser.add_argument("--from", dest="from_date", default=None, help="History start (dd-Mon-YYYY).")
    parser.add_argument("--to", dest="to_date", default=None, help="History end (dd-Mon-YYYY).")
    parser.add_argument("--mf", default=None, help="AMFI mutual-fund id to scope history to one AMC.")
    parser.add_argument("--min-interval", type=float, default=2.0, help="Seconds between requests.")
    parser.add_argument("--overwrite", action="store_true", help="Re-fetch NAVAll even if already stored.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch + parse but do not write files.")
    args = parser.parse_args(argv)

    connector = AmfiConnector(min_interval_s=args.min_interval)

    if args.dry_run:
        artifact = connector.fetch_nav_all()
        nav_file = parse_nav_file(artifact.content.decode("utf-8", errors="replace"))
        print(
            f"NAVAll as of {nav_file.as_of}: {len(nav_file.records)} records "
            f"across {len(nav_file.amcs)} AMCs / {len(nav_file.categories)} categories"
        )
        return 0

    if args.from_date and args.to_date:
        result = scrape_nav_history(
            connector, out_dir=args.out, from_date=args.from_date, to_date=args.to_date,
            mf_code=args.mf,
        )
    else:
        result = scrape_nav_all(connector, out_dir=args.out, overwrite=args.overwrite)

    print(
        f"{result.feed}: {result.status} — {result.records} records "
        f"({result.amcs} AMCs, {result.categories} categories), as_of {result.as_of} -> {args.out}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
