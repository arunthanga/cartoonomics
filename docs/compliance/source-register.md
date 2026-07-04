# Source register (CMP-5)

Per `requirements.md` §17 (Data Sourcing Compliance — a **hard gate**), every
data source has an entry here recording its legal basis for use, permitted uses,
and refresh cadence **before** its connector ships. When a doc here disagrees
with the SSOT (`requirements.md`), the SSOT wins until amended.

| Field | Value |
|---|---|
| Source | SEBI — Portfolio Manager Monthly Report (PMR) |
| Connector | `cartoonomics.connectors.sebi_pms.SebiPmsConnector` |
| Entry point | `https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doPmr=yes` |
| Data captured | Per Portfolio Manager, per month: general information (name, registration no./date, address, principal officer), client count, total AUM and its break-up, funds inflow/outflow, transaction data, and per-strategy TWRR performance vs benchmark. |
| Format | HTML report (the endpoint also emits Excel/XML; XML uses opaque SSRS `TextboxNNN` names, so the labelled HTML is parsed instead). **Not a PDF.** |
| `robots.txt` | Disallows only `/js` and `/css`; the PMR path is permitted (checked 2026). |
| Access method | Public form: GET the landing page to enumerate managers/years/months, then POST `pmrId`/`year`/`month`. SEBI's WAF requires browser-style `Referer`/`Origin`/`Content-Type` headers on the POST; the connector sends these while still identifying honestly via the research User-Agent (FR-1.2, CMP-2). |
| Politeness | Default 2 s min interval + retry/backoff; a global `--max-reports` cap bounds any single run so it cannot degrade the source (CMP-2). |
| Provenance | Source URL, fetch timestamp, and SHA-256 content hash captured per report and appended to `manifest.jsonl` (FR-1.3). |
| Raw-then-parsed | Raw HTML stored immutably, then parsed to JSON; re-parsing never re-fetches (FR-1.5). |
| Legal basis / redistribution | Public regulatory disclosure. Attribute SEBI and link back to the original report (CMP-4). Redistribution rights are **not yet confirmed** for bulk re-publication — treat scraped data as viewable/analysable pending legal review before any export/share feature (CMP-3, constrains FR-3.5/FR-6.4). |
| Refresh cadence | Monthly (reports are published per calendar month). Incremental: a report whose raw file already exists is skipped unless `--overwrite` (FR-1.4). |
| Status | Connector + parser + scraper implemented and verified end-to-end on a single report. Bulk crawl is intentionally gated behind explicit `--limit`/`--max-reports` flags. |

## Usage

```bash
# Enumerate managers/years/months without fetching anything:
python -m cartoonomics.sebi_pms --dry-run

# Fetch one manager's March 2025 report (raw HTML + parsed JSON + manifest):
python -m cartoonomics.sebi_pms --out ./sebi_pms_data --pm INP000006457 --years 2025 --months 3

# Politely walk the first 5 managers for a month, capped for safety:
python -m cartoonomics.sebi_pms --out ./sebi_pms_data --years 2025 --months 3 --limit 5 --max-reports 5
```
