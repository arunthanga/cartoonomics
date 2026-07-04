# ADR-0001: Technology Stack for cartoonomics

- **Status:** Accepted (foundational scope)
- **Resolves:** `requirements.md` §19 Q5 ("Concrete tech stack — to be fixed in an ADR")
- **Scope:** the scrape → parse → analyze → predefined-format → cartoon pipeline
  (requirements §7.1–§7.6, §11)

> ADRs record a decision and its rationale. This one recommends the concrete
> stack and is deliberately opinionated; alternatives and trade-offs are listed
> so the decision can be revisited per subsystem.

---

## 1. Summary (the recommended stack)

| Concern | Recommendation | Why (traceable to requirements) |
|---|---|---|
| **Language (backend/data)** | **Python 3.11+** | Best-in-class scraping, PDF/table, and data ecosystem; one language across §7.1–§7.2. |
| **HTTP fetching** | **httpx** (+ **tenacity** for retries) | Async + sync, HTTP/2, timeouts; polite fetching (FR-1.2). |
| **JS-rendered / anti-bot sites (NSE)** | **Playwright** (only when needed) | NSE requires a real browser session/cookies; use *sparingly* after the §17 gate. |
| **Bulk crawls / scheduling of many sources** | **Scrapy** (optional, for breadth phase) | Mature crawl framework with throttling & robots support. |
| **robots / politeness** | `urllib.robotparser` + per-source rate limits | CMP-1/CMP-2 hard gate. |
| **PDF text & tables** | **pdfplumber** (text + simple tables), **Camelot**/**tabula-py** (ruled financial tables) | Financial statements are table-heavy; FR-1.5. |
| **Scanned PDFs (OCR)** | **pytesseract** + Tesseract, **pdf2image** | Some filings are image-only. |
| **XBRL filings** | **Arelle** (or `python-xbrl`) | BSE/NSE/MCA structured financials are often XBRL — parse structured, not scraped. |
| **Data wrangling / metrics** | **pandas**, **numpy**; XIRR via **pyxirr** or pure-python (as here) | XIRR & metrics (FR-2.2–2.5). |
| **Schema / predefined format** | **pydantic v2** | The CartoonSpec contract is validated & versioned (FR-2.6, §13). |
| **Backend API** | **FastAPI** + **uvicorn** | Pydantic-native, async, OpenAPI out of the box; serves normalized data + provenance (§11 API layer). |
| **Canonical store** | **PostgreSQL** | Relational canonical model (§13); JSONB for semi-structured. |
| **Time series (NAV/prices)** | **TimescaleDB** (Postgres extension) or partitioned tables | PriceSeries at scale (§13). |
| **Raw artifact store** | **S3-compatible object storage** (AWS S3 / MinIO) | Immutable raw-then-parsed (TA-1, FR-1.5). |
| **Orchestration / scheduler** | **Prefect** (or Dagster) | Per-source cadences, retries, observability (FR-1.7). Airflow if already standardized. |
| **Frontend framework** | **React + TypeScript + Vite** | Component-driven cartoonization engine (§7.6). |
| **Animation** | **Framer Motion** (UI motion) + **GSAP** (complex timelines) + **Lottie** (character art) | Rich, controllable motion (§10) with `prefers-reduced-motion` support (A11Y-5). |
| **Data-viz primitives** | **D3** / **visx**; **d3-sankey** for cashflow flows | Sankey/waterfall/see-saw cartoons (FR-4.1–4.4). |
| **Styling / design system** | **Tailwind CSS** + tokens; **Storybook** for the primitive library | Design system as SSOT for UI (§10, FR-6.1). |
| **Accessibility testing** | **axe-core** / **jest-axe**, **Playwright** a11y checks | WCAG 2.1 AA (§12). |
| **Testing (Python)** | **pytest**, **pytest-cov**, **hypothesis**, **responses**/**vcrpy**, **schemathesis** | TDD, property-based regression, HTTP mocking, contract tests. |
| **Testing (frontend)** | **Vitest** + **React Testing Library** + **Playwright** (E2E) | Unit + regression + visual. |
| **Containerization / CI** | **Docker**, **GitHub Actions** | Reproducible envs; gate tests in CI. |

**One-line answer:** *Python (httpx/Playwright/Scrapy + pdfplumber/Camelot/Arelle
+ pandas + pydantic + FastAPI) for the data pipeline; PostgreSQL/Timescale +
object storage for data; Prefect for scheduling; React + TypeScript with Framer
Motion / GSAP / Lottie / D3-sankey for the cartoons; pytest + Vitest/Playwright
for TDD.*

---

## 2. Why Python for scraping + document reading + analysis

1. **One ecosystem, three jobs.** Scraping (httpx/Scrapy/Playwright), document
   parsing (pdfplumber/Camelot/Arelle/Tesseract), and analysis (pandas/numpy)
   are all first-class in Python. This keeps §7.1–§7.2 in a single toolchain.
2. **Government/exchange reality.** BSE/NSE/SEBI/AMFI publish a mix of **XBRL**,
   **PDF**, **CSV**, and **HTML**. Python has the widest, most battle-tested
   parsers for each — including OCR fallback for scanned documents.
3. **Politeness & compliance are easy to centralize** (robots, rate limits,
   retries, provenance) — see this repo's
   `packages/pipeline/src/cartoonomics/connectors/base.py` and its dedicated
   `robots.py` (`robots.txt` allow/deny + crawl-delay).

### Source-specific notes (foundational)
- **NSE:** heavy anti-bot; the site sets cookies via a browser session. Prefer
  their published reports / bhavcopy bulk files; use **Playwright** only where a
  real session is unavoidable, and only after the §17 gate.
- **BSE:** offers announcement/notice endpoints and downloadable filings; often
  scrape-able with plain HTTP + a proper user agent.
- **AMFI:** publishes daily NAV as a bulk text file — **no scraping needed**.
- **SEBI/MCA:** company financials frequently available as **XBRL** — parse the
  structured form (Arelle) rather than the rendered PDF whenever possible.

> **Compliance is a hard gate (§17).** Prefer official APIs / bulk downloads /
> feeds over HTML scraping; keep a source register; respect ToS & robots.

---

## 3. The "predefined format read by a system" — CartoonSpec

The pivotal architectural decision is a **stable, versioned, validated exchange
format** between analysis and rendering: **CartoonSpec** (implemented in
`packages/pipeline/src/cartoonomics/format/cartoon_spec.py`).

- **Serialization:** JSON. **Schema/validation:** pydantic v2 (Python side);
  the same JSON is consumed by the TypeScript renderer. A JSON Schema can be
  emitted from the pydantic models to generate TS types (e.g. `datamodel-codegen`
  / `json-schema-to-typescript`) so both sides share one contract.
- **Guarantees baked in:** provenance on every payload (FR-1.3/§4.6), a
  "Show the numbers" table (FR-6.2), an accessibility block (A11Y-2/3), and a
  reduced-motion contract (A11Y-5).
- **Renderer-agnostic:** the bundled vanilla-JS renderer proves the contract;
  the production renderer is React + Framer Motion consuming the *same* JSON.

This decoupling means the scraping/analysis stack and the animation stack can
evolve independently, and the format is what regression tests guard.

---

## 4. Cartoons & animation stack

- **React + TypeScript + Vite** for the component-driven cartoonization engine
  (FR-6.1). Each cartoon primitive (money-stream, coin-stack, character card,
  see-saw, waterfall block, surprise-event pop) is a component in **Storybook**.
- **Motion:** **Framer Motion** for declarative UI motion; **GSAP** for complex,
  timeline-based sequences (e.g. multi-year "story mode", FR-4.5); **Lottie** for
  hand-drawn character animation. All must honour `prefers-reduced-motion` and
  provide a static equivalent (A11Y-5) — the CartoonSpec carries the flag.
- **Data-viz:** **d3-sankey** for the cashflow flow (FR-4.1), a custom waterfall
  for P&L (FR-4.2), a balance "see-saw" (FR-4.3), and a pie/character chart for
  shareholding (FR-4.4). **visx** wraps D3 in React ergonomically.

---

## 5. TDD approach (switchable) — see `README.md` and `config.py`

- **pytest** + **pytest-cov** for unit + regression; **hypothesis** for
  property-based regression that guards invariants of the CartoonSpec;
  **responses**/**vcrpy** to test connectors without live network;
  **schemathesis** to fuzz the FastAPI contract later.
- The **TDD mode toggle** (`CARTOONOMICS_TDD_MODE` / `.tdd-mode` / `make tdd-on|off`)
  turns the red-green coverage gate on or off without deleting tests.

---

## 6. Alternatives considered

| Area | Chosen | Alternatives | Why not (for now) |
|---|---|---|---|
| Language | Python | Node/TS end-to-end, Go, JVM | Python's PDF/XBRL/scraping/data breadth is unmatched; TS reserved for UI. |
| Scraping | httpx + Playwright | Selenium, requests-only | Playwright is faster/more reliable than Selenium; requests lacks async/HTTP2. |
| PDF tables | pdfplumber + Camelot | PyMuPDF only, commercial APIs | Combo covers text + ruled/complex tables; OCR fallback for scans. |
| Format/validation | pydantic v2 | dataclasses + jsonschema, protobuf | pydantic gives validation + JSON + schema export in one; protobuf is overkill for a JSON UI contract. |
| API | FastAPI | Django REST, Flask | Pydantic-native, async, OpenAPI; least glue for our models. |
| Orchestration | Prefect | Airflow, Dagster, cron | Pythonic, low-ceremony scheduling with retries/observability; Airflow if org-standard. |
| Frontend motion | Framer Motion + GSAP + Lottie | CSS-only, anime.js, Rive | Best control + reduced-motion story + character art; CSS-only can't do §7.4 sequences well. |

---

## 7. Consequences

- **Positive:** one data language; a hard contract (CartoonSpec) that both sides
  test against; compliance/politeness centralized in the connector base;
  accessibility and provenance are structurally required, not bolted on.
- **Costs/risks:** Playwright/OCR add heavy runtime deps (keep them optional and
  behind the §17 gate); pydantic↔TypeScript type sync needs a codegen step in CI;
  Timescale/object-storage are infra to operate (defer until data volume warrants).

---

## 8. What this repository implements today

A runnable, dependency-light **vertical slice** of the stack above:

- Polite, `robots.txt`-aware, provenance-capturing **connector base** (allow/deny
  + advertised crawl-delay, in a dedicated `connectors/robots.py`) with an offline
  fixture connector and honest NSE/BSE reference connectors.
- **PDF and delimited** document parsing into a canonical intermediate.
- **XIRR** metric (pure Python) and a **cashflow → CartoonSpec** builder.
- The **CartoonSpec** pydantic contract (the predefined format).
- A framework-free **animated renderer** that consumes CartoonSpec.
- A **switchable TDD** workflow with unit + regression suites.

The heavier production choices (FastAPI, Postgres/Timescale, Prefect, React +
Framer Motion) are the documented target; the slice proves the seams between
them.
