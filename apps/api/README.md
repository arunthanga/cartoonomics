# `api` — backend service (scaffold)

> **Status: planned scaffold.** No code ships here until the endpoints it needs
> exist. This README fixes the intent and boundaries so the folder is a real,
> navigable home (see [`ADR-0002`](../../docs/adr/0002-repository-structure.md)).

FastAPI + uvicorn service (ADR-0001) that serves normalized data, computed
metrics, and **provenance** to the frontend (`requirements.md` §11). It is a
thin HTTP layer: it depends on `packages/pipeline` for domain logic and emits
**CartoonSpec** payloads validated against `packages/contracts`.

Responsibilities (and non-responsibilities):

- **Owns:** routing, request/response schemas, auth, pagination, error mapping,
  OpenAPI. Pydantic-native so CartoonSpec models serialize directly.
- **Does not own:** scraping/parsing/metrics (that is `packages/pipeline`), or
  scheduling (that is `services/orchestrator`).

Expected shape when it lands:

```text
apps/api/
├─ pyproject.toml        # workspace member; depends on packages/pipeline + contracts
├─ src/cartoonomics_api/
│  ├─ main.py            # FastAPI app factory
│  ├─ routers/           # /instruments, /companies, /compare, /provenance, ...
│  └─ deps.py            # settings, DB session, pipeline services
└─ tests/
```

Cross-cutting: no secrets in code (TA-4); every served number carries provenance
(FR-1.3); this is research/education, not advice (§16).
