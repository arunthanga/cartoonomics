"""Orchestrate scraping SEBI Portfolio Manager Monthly Reports.

Ties the connector (:mod:`cartoonomics.connectors.sebi_pms`) to the parser
(:mod:`cartoonomics.parsing.sebi_pms`) and walks every Portfolio Manager for
each requested month, honouring the pipeline's cross-cutting rules:

* **Polite** (FR-1.2): one rate-limited, ``robots``-aware connector; a global
  ``max_reports`` safety cap so a single run can never hammer SEBI.
* **Raw-then-parsed** (FR-1.5): the raw HTML is written to disk first, then
  parsed into JSON, so re-parsing never needs a re-fetch.
* **Idempotent / incremental** (FR-1.4): a report whose raw file already exists
  is skipped unless ``overwrite`` is set.
* **Provenance** (FR-1.3): every report records its source URL, fetch time and
  content hash, appended to ``manifest.jsonl``.
* **Failures are surfaced, not dropped** (FR-1.6): a fetch/parse error is
  recorded and the walk continues.

Run it as a module::

    python -m cartoonomics.sebi_pms --out ./sebi_pms_data --years 2025 --months 3 --limit 5
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from cartoonomics.connectors.sebi_pms import PortfolioManager, SebiPmsConnector
from cartoonomics.parsing.sebi_pms import parse_pms_report

_MONTH_ABBR = ["", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]


@dataclasses.dataclass
class ScrapeResult:
    """Outcome of attempting one (Portfolio Manager, year, month) report."""

    registration_number: str
    name: str
    year: int
    month: int
    status: str  # "fetched" | "skipped" | "error"
    raw_path: str | None = None
    parsed_path: str | None = None
    source_hash: str | None = None
    error: str | None = None


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text)


def scrape_reports(
    connector: SebiPmsConnector,
    *,
    out_dir: Path,
    years: Iterable[int],
    months: Iterable[int],
    managers: list[PortfolioManager] | None = None,
    limit: int | None = None,
    max_reports: int | None = None,
    overwrite: bool = False,
    **fetch_kwargs,
) -> list[ScrapeResult]:
    """Walk Portfolio Managers x (year, month) and persist raw + parsed reports."""
    out_dir = Path(out_dir)
    raw_dir = out_dir / "raw"
    parsed_dir = out_dir / "parsed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "manifest.jsonl"

    if managers is None:
        managers = connector.list_portfolio_managers(**fetch_kwargs)
    if limit is not None:
        managers = managers[:limit]

    years = list(years)
    months = list(months)
    results: list[ScrapeResult] = []
    fetched = 0

    for manager in managers:
        for year in years:
            for month in months:
                if max_reports is not None and fetched >= max_reports:
                    return results

                stem = f"{year}-{_MONTH_ABBR[month]}"
                reg_slug = _slug(manager.registration_number)
                raw_path = raw_dir / reg_slug / f"{stem}.html"
                parsed_path = parsed_dir / reg_slug / f"{stem}.json"

                if raw_path.exists() and not overwrite:
                    results.append(
                        ScrapeResult(
                            manager.registration_number, manager.name, year, month,
                            "skipped", str(raw_path),
                            str(parsed_path) if parsed_path.exists() else None,
                        )
                    )
                    continue

                try:
                    artifact = connector.fetch_report(manager, year, month, **fetch_kwargs)
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_path.write_bytes(artifact.content)

                    report = parse_pms_report(
                        artifact.content.decode("utf-8", errors="replace"),
                        year=year,
                        month=month,
                        source_url=artifact.source_url,
                        source_hash=artifact.source_hash,
                    )
                    parsed_path.parent.mkdir(parents=True, exist_ok=True)
                    parsed_path.write_text(
                        json.dumps(dataclasses.asdict(report), indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )

                    _append_manifest(
                        manifest,
                        {
                            "registration_number": manager.registration_number,
                            "name": manager.name,
                            "year": year,
                            "month": month,
                            "source_url": artifact.source_url,
                            "source_hash": artifact.source_hash,
                            "fetched_at": artifact.fetched_at.isoformat(),
                            "raw_path": str(raw_path),
                            "parsed_path": str(parsed_path),
                        },
                    )
                    fetched += 1
                    results.append(
                        ScrapeResult(
                            manager.registration_number, manager.name, year, month,
                            "fetched", str(raw_path), str(parsed_path), artifact.source_hash,
                        )
                    )
                except Exception as exc:  # noqa: BLE001 - surfaced, never silently dropped
                    results.append(
                        ScrapeResult(
                            manager.registration_number, manager.name, year, month,
                            "error", error=f"{type(exc).__name__}: {exc}",
                        )
                    )

    return results


def _append_manifest(manifest: Path, record: dict) -> None:
    with manifest.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _parse_int_list(raw: str | None, default: list[int]) -> list[int]:
    if not raw:
        return default
    return [int(part) for part in raw.split(",") if part.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scrape SEBI Portfolio Manager Monthly Reports.")
    parser.add_argument("--out", type=Path, default=Path("sebi_pms_data"), help="Output directory.")
    parser.add_argument("--years", default=None, help="Comma-separated years (default: all available).")
    parser.add_argument("--months", default="1,2,3,4,5,6,7,8,9,10,11,12", help="Comma-separated months.")
    parser.add_argument("--pm", action="append", default=None, help="Registration number filter (repeatable).")
    parser.add_argument("--limit", type=int, default=None, help="Max number of Portfolio Managers.")
    parser.add_argument("--max-reports", type=int, default=None, help="Global cap on reports fetched this run.")
    parser.add_argument("--min-interval", type=float, default=2.0, help="Seconds between requests (politeness).")
    parser.add_argument("--overwrite", action="store_true", help="Re-fetch even if raw file exists.")
    parser.add_argument("--dry-run", action="store_true", help="Enumerate managers/years and exit.")
    args = parser.parse_args(argv)

    connector = SebiPmsConnector(min_interval_s=args.min_interval)
    landing = connector.fetch_landing().content.decode("utf-8", errors="replace")
    managers = connector.list_portfolio_managers(landing_html=landing)
    if args.pm:
        wanted = {p.upper() for p in args.pm}
        managers = [m for m in managers if m.registration_number.upper() in wanted]

    years = _parse_int_list(args.years, connector.available_years(landing_html=landing))
    months = _parse_int_list(args.months, list(range(1, 13)))

    if args.dry_run:
        print(f"{len(managers)} portfolio managers; years={years}; months={months}")
        return 0

    results = scrape_reports(
        connector,
        out_dir=args.out,
        years=years,
        months=months,
        managers=managers,
        max_reports=args.max_reports,
        overwrite=args.overwrite,
    )
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    print(f"Done. {counts} -> {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
