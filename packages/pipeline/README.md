# `cartoonomics` pipeline

The Python **data pipeline** library: polite, provenance-capturing ingestion →
document parsing → analysis/metrics → **CartoonSpec** (the predefined format).
Covers `requirements.md` §7.1–§7.2 and §7.6 (the contract).

Import package: `cartoonomics`. Distributed from the repo-root build for now
(see [`ADR-0002`](../../docs/adr/0002-repository-structure.md) §2.4 for the
workspace growth path).

```text
src/cartoonomics/
├─ connectors/   # BaseConnector (polite fetch + provenance), robots (robots.txt policy), fixture, NSE/BSE (FR-1.2/1.3)
├─ parsing/      # PDF + delimited -> canonical ParsedFinancials (FR-1.5)
├─ analysis/     # metrics (XIRR) + cashflow -> CartoonSpec builder (§7.2, FR-4.1)
├─ format/       # CartoonSpec pydantic models — the source of truth for the contract
├─ pipeline.py   # end-to-end wiring: scrape -> parse -> analyze -> spec
├─ config.py     # runtime config incl. switchable TDD mode
├─ tdd.py        # TDD mode CLI (python -m cartoonomics.tdd on|off|status)
└─ data/         # bundled sample fixtures (never real/licensed data — §17)
tests/
├─ unit/         # fast, isolated module tests (-m unit)
└─ regression/   # golden + property tests guarding the CartoonSpec contract (-m regression)
```

Run from the repository root: `make test` (unit + regression), `make demo`
(regenerates `apps/web/cartoon_spec.json`). See the root `README.md` for the full
developer workflow and the switchable TDD mode.
