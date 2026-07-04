"""End-to-end demo pipeline: scrape -> parse -> analyze -> CartoonSpec.

Wires the layers together (§11 architecture). The demo uses
:class:`FixtureConnector` so it runs fully offline, but any :class:`BaseConnector`
(e.g. the NSE/BSE connectors) can be substituted without changing the pipeline.

Run as a module to regenerate the renderer's payload::

    python -m cartoonomics.pipeline --out web/cartoon_spec.json
"""

from __future__ import annotations

import argparse
from pathlib import Path

from cartoonomics.analysis import build_cashflow_cartoon
from cartoonomics.connectors.base import BaseConnector
from cartoonomics.connectors.fixture import FixtureConnector
from cartoonomics.format import CartoonSpec
from cartoonomics.parsing import parse_financials

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_SAMPLE = "sample_cashflow.csv"


def run_cashflow_pipeline(
    connector: BaseConnector,
    *,
    url: str,
    entity_name: str,
    period: str,
    unit: str = "INR_CRORE",
    entity_identifier: str | None = None,
    **fetch_kwargs,
) -> CartoonSpec:
    """Fetch a filing, parse it, and produce a validated cashflow CartoonSpec."""
    artifact = connector.fetch(url, **fetch_kwargs)
    parsed = parse_financials(artifact, entity_name=entity_name, period=period)
    return build_cashflow_cartoon(
        parsed,
        source=artifact.source,
        source_url=artifact.source_url,
        source_hash=artifact.source_hash,
        fetched_at=artifact.fetched_at,
        unit=unit,
        entity_identifier=entity_identifier,
    )


def run_demo(sample: str = DEFAULT_SAMPLE) -> CartoonSpec:
    """Run the offline demo against the bundled sample filing."""
    connector = FixtureConnector(base_dir=DATA_DIR, source="BSE")
    return run_cashflow_pipeline(
        connector,
        url=sample,
        entity_name="Acme Industries Ltd",
        period="FY2024",
        entity_identifier="ACME",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="cartoonomics demo pipeline")
    parser.add_argument("--sample", default=DEFAULT_SAMPLE, help="Bundled sample filename.")
    parser.add_argument("--out", type=Path, default=None, help="Write CartoonSpec JSON here.")
    args = parser.parse_args(argv)

    spec = run_demo(args.sample)
    payload = spec.to_json()
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(f"Wrote CartoonSpec -> {args.out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
