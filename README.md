# cartoonomics

Make the Indian financial system understandable to anyone — by turning dry
disclosures (BSE/NSE filings, factsheets, cashflows) into clean, playful,
**cartoonized** stories. See [`requirements.md`](requirements.md) for the full
product & technical requirements (the single source of truth).

This repository implements a runnable **vertical slice** of the pipeline:

```
scrape/ingest  →  parse documents  →  analyze/normalize  →  CartoonSpec (predefined format)  →  animated cartoon
   (§7.1)            (§7.1)                (§7.2)                    (§7.6)                          (§7.6)
```

The recommended production technology stack is documented in
[`docs/adr/0001-technology-stack.md`](docs/adr/0001-technology-stack.md)
(this resolves open question Q5). The repository is a **monorepo**; its folder
structure and the analysis behind it are in
[`docs/adr/0002-repository-structure.md`](docs/adr/0002-repository-structure.md),
with a quick "where does X go?" map in
[`docs/architecture/repository-layout.md`](docs/architecture/repository-layout.md).

---

## What's here

```text
apps/       # deployables:  api/ (FastAPI, scaffold) · web/ (cartoon renderer)
services/   # workers:       orchestrator/ (Prefect flows, scaffold)
packages/   # libraries:     pipeline/ (the Python data pipeline) · contracts/ (CartoonSpec, scaffold)
infra/      # docker / terraform / k8s  (scaffold)
docs/       # adr/ + architecture/
scripts/    # dev/ops helpers
```

The working vertical slice lives in `packages/pipeline` and `apps/web`:

| Path | Role |
|---|---|
| `packages/pipeline/src/cartoonomics/connectors/` | Polite, provenance-capturing source connectors (`base`, offline `fixture`, reference `NSE`/`BSE`). |
| `packages/pipeline/src/cartoonomics/parsing/` | Read PDF (pdfplumber) and delimited documents into a canonical intermediate. |
| `packages/pipeline/src/cartoonomics/analysis/` | Metrics (XIRR) and the cashflow → CartoonSpec builder. |
| `packages/pipeline/src/cartoonomics/format/` | **CartoonSpec** — the predefined, versioned exchange format (pydantic). |
| `packages/pipeline/src/cartoonomics/pipeline.py` | Wires it all together end-to-end. |
| `packages/pipeline/src/cartoonomics/config.py`, `tdd.py` | The switchable **TDD mode**. |
| `apps/web/` | A framework-free **animated renderer** that consumes a CartoonSpec. |
| `packages/pipeline/tests/unit/`, `.../tests/regression/` | The unit and regression test suites. |

The **predefined format** (`CartoonSpec`) is the contract between the analysis
backend and the cartoon frontend: the backend emits validated JSON; any renderer
(the bundled one, or a future React + Framer Motion app) draws it. It carries
provenance, a "Show the numbers" table, and accessibility + reduced-motion
guarantees by construction.

---

## Quick start

```bash
# 1. Install dev dependencies (into your user site or a venv)
pip install --user -e ".[dev]"     # or: make install

# 2. Run the end-to-end demo (offline) and emit the CartoonSpec the UI reads
make demo                          # writes apps/web/cartoon_spec.json

# 3. See the animated cartoon
make serve                         # http://localhost:8000
```

Swap the offline `FixtureConnector` for `NSEConnector`/`BSEConnector` (after
clearing the §17 compliance gate) to run against real filings — the rest of the
pipeline is unchanged.

---

## Test-Driven Development (switchable)

TDD is **on by default** and can be switched off without deleting any tests.

```bash
make tdd-status        # show current mode
make tdd-on            # tests + coverage GATE development (red-green-refactor)
make tdd-off           # tests still run, but no longer block the workflow

make test              # unit + regression (honours the mode)
make test-unit         # only the unit suite
make test-regression   # only the regression suite
```

How the toggle is resolved (highest precedence first):

1. `CARTOONOMICS_TDD_MODE` environment variable (`on`/`off`, `1`/`0`, …)
2. the `.tdd-mode` state file (written by `make tdd-on|off`)
3. the built-in default: **ON**

When **ON**, `scripts/run_tests.sh` requires the suites to pass **and** coverage
to meet `COVERAGE_MIN` (85%) or it exits non-zero. When **OFF**, the same tests
run for feedback only.

### Test suites

- **Unit** (`packages/pipeline/tests/unit/`, `-m unit`): fast, isolated tests of each module —
  config toggle, XIRR (incl. a hypothesis property test), document parsing (real
  PDF via `fpdf2`), polite fetching/retry/provenance, CartoonSpec validation,
  the cashflow builder, the pipeline, and the TDD CLI.
- **Regression** (`packages/pipeline/tests/regression/`, `-m regression`): guards
  the CartoonSpec contract — a **golden-file** test for the demo payload plus
  property-based invariants (e.g. net change == sum of activity totals).
  Regenerate the golden intentionally with
  `python packages/pipeline/tests/regression/_regen_golden.py`.

---

## Notes

- **Compliance is a hard gate.** No real connector ships without clearing
  `requirements.md` §17 (ToS/robots, rate limits, redistribution rights, source
  register). The NSE/BSE connectors here implement the *polite pattern* but are
  not wired to fetch by default.
- **Not investment advice** — research & education only (§16).
