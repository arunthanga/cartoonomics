# Repository layout — reference

A quick "where does X go?" map. The **why** lives in
[`ADR-0002`](../adr/0002-repository-structure.md); this is the day-to-day index.

```text
cartoonomics/
├─ apps/
│  ├─ api/            # FastAPI service (§11). Owns HTTP, auth, serialization only.
│  └─ web/            # Frontend (§7.6). Cartoon primitives, Storybook, pages.
├─ services/
│  └─ orchestrator/   # Prefect/Dagster flows & schedules (FR-1.7).
├─ packages/
│  ├─ pipeline/       # Python library: connectors, parsing, analysis, pipeline wiring.
│  │  ├─ src/cartoonomics/
│  │  │  ├─ connectors/   # polite, provenance-capturing source connectors (FR-1.2/1.3)
│  │  │  ├─ parsing/      # raw doc -> canonical ParsedFinancials (FR-1.5)
│  │  │  ├─ analysis/     # metrics (XIRR) + CartoonSpec builders (§7.2)
│  │  │  ├─ format/       # CartoonSpec pydantic models (the contract source of truth)
│  │  │  ├─ pipeline.py   # end-to-end wiring: scrape -> parse -> analyze -> spec
│  │  │  ├─ config.py     # runtime config incl. switchable TDD mode
│  │  │  └─ data/         # bundled sample fixtures (never real/licensed data)
│  │  └─ tests/           # unit/ + regression/ (regression guards the contract)
│  └─ contracts/      # CartoonSpec JSON Schema + generated TypeScript types (the seam).
├─ infra/
│  ├─ docker/         # Dockerfiles + docker-compose for local dev
│  ├─ terraform/      # cloud infra as code (Postgres/Timescale, object storage, queues)
│  └─ k8s/            # deployment manifests / Helm charts
├─ docs/
│  ├─ adr/            # architecture decision records
│  └─ architecture/   # this file + diagrams
├─ scripts/           # repo-level dev/ops helpers (run_tests.sh, ...)
├─ .github/           # CI/CD workflows, issue/PR templates, CODEOWNERS, dependabot
├─ requirements.md    # product & technical single source of truth
├─ pyproject.toml     # root build + tooling config (grows into a workspace)
├─ Makefile           # task entry points (install, test, demo, serve, tdd-*)
└─ README.md
```

## Where does X go?

| I'm adding… | It goes in… |
|---|---|
| a new data source (exchange/AMC) | `packages/pipeline/src/cartoonomics/connectors/` |
| a new document parser | `packages/pipeline/src/cartoonomics/parsing/` |
| a new metric (liquidity, risk, tax…) | `packages/pipeline/src/cartoonomics/analysis/` |
| a new cartoon type / field | `packages/pipeline/src/cartoonomics/format/` (then regen the contract) |
| an HTTP endpoint | `apps/api/` |
| a scheduled job / connector cadence | `services/orchestrator/` |
| a cartoon UI component | `apps/web/src/components/` |
| a Dockerfile / compose / IaC | `infra/` |
| an architecture decision | `docs/adr/NNNN-*.md` |
| a repo-wide dev script | `scripts/` |

## Dependency direction (enforced by convention, see ADR-0002 §4)

```text
apps/  ─┐
        ├─▶ packages/   (never the reverse)
services/─┘
packages/api-consumers ─▶ packages/contracts
```

`packages/*` must be import-safe: no network or filesystem I/O at import time.
