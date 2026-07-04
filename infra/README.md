# `infra` — build, ship, run (scaffold)

> **Status: planned scaffold.** Declarative homes for how cartoonomics is built,
> shipped, and operated (ADR-0001 §1;
> [`ADR-0002`](../docs/adr/0002-repository-structure.md) §3).

```text
infra/
├─ docker/       # Dockerfiles per deployable + docker-compose for local dev
├─ terraform/    # cloud infra as code: Postgres/TimescaleDB, S3-compatible object store, queues
└─ k8s/          # deployment manifests / Helm charts
```

Design constraints these must encode:

- **Raw vs. derived** storage separated; raw artifacts immutable (TA-1, FR-1.5).
- **Object storage** for raw filings; **PostgreSQL** for the canonical model
  (§13); **TimescaleDB**/partitioned tables for price/NAV series.
- **Secrets are environment-driven, never committed** (TA-4).
- Each `apps/*` and `services/*` unit ships as its own image (independent deploy).
