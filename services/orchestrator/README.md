# `orchestrator` — scheduling & jobs (scaffold)

> **Status: planned scaffold.** Home for the background workers described in
> `requirements.md` FR-1.7 and §11. See
> [`ADR-0002`](../../docs/adr/0002-repository-structure.md).

Prefect (or Dagster) flows that run connectors on **per-source cadences** (NAV
daily, results/shareholding quarterly), trigger re-parsing and metric
recomputation, and enforce data-quality checks (§15.2). Kept separate from
`apps/api` because a scheduled worker has a different scaling, deploy, and
failure profile than a request/response API (TA-3: one source breaking must not
take down others).

Expected shape when it lands:

```text
services/orchestrator/
├─ pyproject.toml        # workspace member; depends on packages/pipeline
├─ src/cartoonomics_orchestrator/
│  ├─ flows/             # one flow per source / cadence
│  ├─ schedules.py       # cadences per source register (CMP-5)
│  └─ quality.py         # parse-failure queue + freshness metrics (FR-1.6)
└─ tests/
```

Cross-cutting: idempotent + incremental ingestion (FR-1.4); raw stored
immutably then parsed (FR-1.5, TA-1); politeness/rate limits honoured (FR-1.2).
