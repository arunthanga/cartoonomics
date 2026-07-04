# Contributing to cartoonomics

Thanks for helping make Indian finance understandable! Please read this with
[`requirements.md`](requirements.md) (the single source of truth) and the ADRs in
[`docs/adr/`](docs/adr/).

## Repository layout

This is a monorepo. See
[`docs/architecture/repository-layout.md`](docs/architecture/repository-layout.md)
for the "where does X go?" map and
[`ADR-0002`](docs/adr/0002-repository-structure.md) for the rationale.

- `packages/*` — importable libraries (must be import-safe: no I/O at import).
- `apps/*` / `services/*` — deployables; they may depend on `packages/*`, never
  the reverse.
- The **CartoonSpec** contract is defined once (in the pipeline's `format/`,
  surfaced via `packages/contracts`); consumers import it, never re-declare it.

## Getting started

```bash
make install     # editable install with dev extras (pytest, hypothesis, ...)
make test        # unit + regression (honours the switchable TDD mode)
make demo        # regenerate apps/web/cartoon_spec.json
make serve       # view the cartoon at http://localhost:8000
```

Optional local hooks: `pip install pre-commit && pre-commit install`.

## Test-Driven Development

TDD mode is **ON** by default; `make test` then enforces the coverage gate. Use
`make tdd-off` to run tests for feedback only without deleting any. See the root
`README.md` for how the toggle resolves.

## Pull requests

- Every change traces to a requirement in `requirements.md` (or is explicitly
  tooling/docs). If the product changes, update the SSOT **first**.
- Keep changes surgical and scoped to their area; respect `CODEOWNERS`.
- Fill in the PR template checklist (provenance, accessibility, contract, secrets).
