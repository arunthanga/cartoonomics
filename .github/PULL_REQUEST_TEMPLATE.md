## What & why

<!-- What does this change do, and which requirement does it trace to? -->

## Requirement / ADR trace

- Requirement(s): <!-- e.g. FR-4.1, A11Y-5, or "n/a — tooling" -->
- ADR(s): <!-- e.g. ADR-0001 / ADR-0002, or "n/a" -->

## Checklist

- [ ] Traces to something in `requirements.md` (the SSOT), or is explicitly tooling/docs.
- [ ] Tests added/updated; `make test` passes (coverage gate honoured when TDD mode is ON).
- [ ] If a displayed number changed: provenance is preserved (FR-1.3).
- [ ] If a cartoon changed: "Show the numbers" + accessibility equivalents hold (FR-6.2, §12).
- [ ] If the CartoonSpec changed: regression golden regenerated intentionally and both producer/consumer updated.
- [ ] No secrets committed; config is environment-driven (TA-4).
