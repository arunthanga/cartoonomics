# ADR-0002: Repository & Folder Structure

- **Status:** Accepted (foundational scope)
- **Builds on:** [`ADR-0001 Technology Stack`](0001-technology-stack.md)
- **Resolves:** "Create an optimal folder structure based on best practices for
  this class of project and technology; analyse the possibilities and
  scalability."
- **Scope:** the whole repository — the data pipeline (§7.1–§7.2), the API layer
  (§11), the cartoonization frontend (§7.6), orchestration (§7.1 FR-1.7),
  infrastructure, docs, and CI.

> ADRs record a decision and its rationale. This one is deliberately opinionated
> about layout; the alternatives and their trade-offs are documented so the
> decision can be revisited as the system grows.

---

## 1. Context

`cartoonomics` is **not** a single Python package. Per ADR-0001 the target system
spans several independently-deployable units in **two languages**:

| Unit | Language / stack | Requirement |
|---|---|---|
| Ingestion + parsing + analysis pipeline | Python (httpx/Scrapy/Playwright, pdfplumber/Camelot/Arelle, pandas, pydantic) | §7.1–§7.2 |
| **CartoonSpec** predefined format (the analysis↔render contract) | pydantic (Python) → JSON Schema → generated TS types | §7.6, FR-2.6, §13 |
| API layer | Python (FastAPI + uvicorn) | §11 |
| Orchestration / scheduler | Python (Prefect / Dagster) | FR-1.7 |
| Cartoonization frontend | TypeScript (React + Vite + Framer Motion / GSAP / Lottie / D3) | §7.3–§7.6 |
| Data + object + time-series stores | PostgreSQL / TimescaleDB / S3-compatible | §11, §13 |
| Infrastructure | Docker, GitHub Actions, IaC | ADR-0001 §1 |

The repository must therefore express **many services, two toolchains, and one
shared contract** — and must scale from today's single vertical slice to the
full Phase A–E roadmap (`requirements.md` §15) without a disruptive re-layout.

Two structural forces dominate every decision below:

1. **The contract is the seam.** CartoonSpec decouples the Python analysis stack
   from the TypeScript render stack (ADR-0001 §3). The layout must make that seam
   a first-class, shared, independently-versioned location — not an
   implementation detail buried inside one service.
2. **Compliance & provenance are cross-cutting** (`requirements.md` §17, FR-1.3).
   Connectors, the source register, and raw-vs-derived separation (TA-1) must
   have obvious, auditable homes.

---

## 2. The possibilities considered

### 2.1 Repository topology — monorepo vs. polyrepo

| Option | What it is | Pros | Cons | Verdict |
|---|---|---|---|---|
| **Polyrepo** | one git repo per service (`-pipeline`, `-api`, `-web`, `-infra`) | independent release cadence; hard ownership boundaries; small clones | the **CartoonSpec contract drifts** across repos; cross-cutting changes need N PRs; painful for a small team; onerous local dev | ❌ premature for foundational scope |
| **Monolith** (single package, everything imported together) | one Python package, frontend stuffed beside it | simplest to start | cannot host a second language cleanly; API/pipeline/worker cannot deploy independently; violates TA-3 (connector isolation) | ❌ does not fit a two-language, multi-service target |
| **Monorepo** (many units, one repo) | `apps/` + `packages/` + `services/` + `infra/` | one PR spans contract + producer + consumer; **atomic contract changes**; shared tooling/CI; still allows per-unit deploy | needs a little tooling discipline (workspaces, path filters in CI) | ✅ **chosen** |

**Decision: a monorepo.** For a small team building a producer (Python) and a
consumer (TypeScript) of one shared, versioned contract, the monorepo is the
industry-standard answer (cf. large data/ML + web products). It makes the
CartoonSpec change *and* both sides that depend on it move in a single reviewable
commit, which is exactly what the regression suite guards.

### 2.2 Top-level partitioning — how to name the buckets

The widely-adopted convention (Nx, Turborepo, Bazel-style, and most polyglot
product monorepos) is to separate **deployables** from **libraries**:

- `apps/` — things you deploy/run (API, web frontend).
- `packages/` — importable libraries shared by apps (the pipeline library, the
  contract/SDK).
- `services/` — long-running background workers / schedulers (orchestration).
- `infra/` — how it is built, shipped, and run (Docker, IaC, k8s).
- `docs/` — decisions (ADRs) and architecture.
- `scripts/` — repo-level dev/ops helpers.

Alternatives rejected: a flat `src/`-at-root (can't host two languages or
multiple deployables); grouping by layer at the very top (`frontend/`,
`backend/`) — this hides that the API and the worker are *different* deployables
that happen to share Python, and it has no obvious home for shared libraries.

### 2.3 Python project layout — `src/` layout vs. flat

`src/`-layout (package under `.../src/<pkg>`) is the modern Python packaging best
practice: it prevents "works because the CWD is on `sys.path`" bugs, forces
tests to run against the *installed* package, and keeps import roots explicit.
The current repo already uses it — we keep it, one level down, inside each Python
package (`packages/pipeline/src/cartoonomics/...`).

### 2.4 Python multi-package management — the growth path

| Option | When it fits | Notes |
|---|---|---|
| **Single root build, one importable package** (today) | exactly one Python package exists | simplest; what this ADR ships |
| **uv / hatch workspace** (per-package `pyproject.toml`, one lockfile) | 2+ Python packages (api, worker, pipeline, contracts) | recommended next step; add when `apps/api` lands |
| **Bazel / Pants** | very large, cache-critical, many-language build graphs | overkill here; revisit only at large scale |

We do **not** adopt heavyweight build tooling now (YAGNI). The directory shape,
however, is chosen so that promoting `packages/pipeline` and a future
`packages/contracts` / `apps/api` to workspace members is a config-only change.

### 2.5 Frontend layout

The frontend is a standard Vite + React + TS app under `apps/web/`, with
`src/components/` for cartoon primitives (FR-6.1), Storybook for the primitive
library (ADR-0001 §4), and generated CartoonSpec types imported from the shared
contract package rather than re-declared (single source of truth).

Today `apps/web/` holds the framework-free reference renderer (proving the
contract end-to-end); it is the seed the React app replaces without moving.

---

## 3. Decision — the recommended structure

```text
cartoonomics/
├─ apps/                      # deployable applications (one deploy unit each)
│  ├─ api/                    # FastAPI service: serves normalized data + provenance (§11)
│  └─ web/                    # frontend: cartoonization engine (§7.6) — React+Vite target
├─ services/                  # long-running background workers
│  └─ orchestrator/           # Prefect/Dagster flows & schedules (FR-1.7)
├─ packages/                  # importable, versioned libraries (no side effects on import)
│  ├─ pipeline/               # ingestion + parsing + analysis library (§7.1–§7.2)
│  │  ├─ src/cartoonomics/    # connectors/ parsing/ analysis/ format/ pipeline.py
│  │  └─ tests/               # unit/ + regression/ (guards the contract)
│  └─ contracts/              # CartoonSpec: schema + generated TS types (the seam, §7.6)
├─ infra/                     # how it is built, shipped, run
│  ├─ docker/                 # Dockerfiles + docker-compose for local dev
│  ├─ terraform/              # cloud infra as code (stores, buckets, queues)
│  └─ k8s/                    # deployment manifests / Helm charts
├─ docs/
│  ├─ adr/                    # architecture decision records (this file, ADR-0001)
│  └─ architecture/           # diagrams, the annotated layout reference
├─ scripts/                   # repo-level dev/ops helpers (run_tests.sh, ...)
├─ .github/                   # CI/CD workflows, issue/PR templates, CODEOWNERS
├─ requirements.md            # product & technical SSOT (unchanged)
├─ pyproject.toml             # root build + tool config (grows into a workspace)
├─ Makefile                   # task entry points
└─ README.md
```

**Why each boundary exists (traceability):**

- `packages/pipeline` isolates connectors so *one source breaking cannot take
  down others* (TA-3) and centralizes politeness/provenance (FR-1.2/1.3).
- `packages/contracts` is the **CartoonSpec** seam (ADR-0001 §3): the pydantic
  models are the source of truth; a JSON Schema + generated TS types are emitted
  so the Python producer and the TS consumer can never silently diverge.
- `apps/api` vs `services/orchestrator` are split because a request/response API
  and a scheduled worker have different scaling, deploy, and failure profiles —
  keeping them separate honours independent deployability and TA-3.
- `infra/` keeps raw-vs-derived storage (TA-1), object storage, and time-series
  choices declarative and reviewable.
- `docs/adr` keeps the "why" versioned next to the code it governs.

---

## 4. Scalability analysis

**Along the roadmap (§15 Phase A→E):**

- *Phase A/B (foundations, analysis):* new connectors and metrics are new
  modules inside `packages/pipeline` — no structural change. A `sources/`
  register + per-source subpackages scale connector count linearly.
- *Phase C (first cartoons + design system):* `apps/web` grows a
  `src/components/` primitive library and Storybook; CartoonSpec additions land
  in `packages/contracts` and flow to both sides atomically.
- *Phase D (comparison):* a comparison endpoint in `apps/api` + a compare view in
  `apps/web`; both consume the same contract package.
- *Phase E (breadth, most compliance-sensitive):* many more connectors and stores
  — this is where per-package `pyproject.toml` + a uv/hatch workspace and
  CI **path filters** (build/test only what changed) pay off.

**Scaling dimensions and how the layout absorbs them:**

| Dimension | Growth pressure | How this structure copes |
|---|---|---|
| **Sources/connectors** | dozens of exchanges/AMCs (§7.1) | each is a module/subpackage in `packages/pipeline/connectors`; isolation = TA-3 |
| **Contract evolution** | more cartoon types (§7.4–§7.5) | `packages/contracts` versions the schema; regression golden tests gate changes |
| **Team size** | more contributors | `CODEOWNERS` per top-level dir; PR templates; clear ownership seams |
| **Build/CI time** | more packages/apps | CI path filters + a workspace tool build only affected units |
| **Deploy independence** | API vs worker vs web | separate `apps/`/`services/` units, separate Dockerfiles/images |
| **Data volume** | prices/NAV at scale (§13) | `infra/` declares Timescale/partitioning + object storage; code unaffected |
| **Second language** | Python + TypeScript | `apps/`+`packages/` cleanly host both; shared contract bridges them |

**Guardrails that keep it scalable (documented so they are enforced, not
assumed):**

1. Dependencies flow **one way**: `apps/` and `services/` may depend on
   `packages/`; `packages/` never depend on `apps/`.
2. `packages/*` are import-safe (no I/O or network at import time) so they are
   reusable and testable.
3. The **contract** is only defined in `packages/contracts`; consumers import
   generated types, never hand-copies.
4. Raw artifacts are immutable and separated from derived data (TA-1); secrets
   are environment-driven, never committed (TA-4).

---

## 5. Consequences

- **Positive:** producer + consumer of the contract change atomically; each
  deployable has a clear home and its own image; ownership and CI can be scoped
  per directory; the growth path (workspace tooling, path-filtered CI, more
  apps) is additive, not a re-layout.
- **Costs / risks:** a monorepo needs a little discipline (dependency direction,
  CI path filters) to avoid slow pipelines; the pydantic↔TypeScript type sync
  needs a codegen step in CI (accepted in ADR-0001 §7). These are configuration
  concerns, not structural ones.

---

## 6. What this ADR changes in the repo today

The foundational slice is re-homed into the structure above **without changing
any behaviour** (the test suite is green before and after):

- `src/cartoonomics` → `packages/pipeline/src/cartoonomics`
- `tests/` → `packages/pipeline/tests/`
- `web/` → `apps/web/`
- new **scaffold** homes (README-only, documenting intent + traceability) for
  `apps/api`, `services/orchestrator`, `packages/contracts`, and `infra/*`, so
  the target shape is real and navigable before the code lands.
- repo-level governance/tooling added: `.github/` (CI + templates + CODEOWNERS),
  `.editorconfig`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`.

Heavier choices (uv/hatch workspace, per-package manifests, path-filtered CI)
are deferred until a second Python package (`apps/api`) actually exists —
adopting them earlier would be speculative.
