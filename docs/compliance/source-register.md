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

---

| Field | Value |
|---|---|
| Source | AMFI — Association of Mutual Funds in India (NAV feeds) |
| Connector | `cartoonomics.connectors.amfi.AmfiConnector` |
| Entry points | `https://portal.amfiindia.com/spages/NAVAll.txt` (daily, all schemes) and `https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx` (history for a date range, optionally one AMC). |
| Data captured | Per scheme/plan: scheme code, ISINs (growth / reinvestment), scheme name, NAV, date, and (history feed) repurchase/sale price — with AMC and scheme-category context attached to each record. |
| Format | Semicolon-delimited text (**official machine-readable bulk feed — no HTML scraping**, FR-1.2/CMP-1/CMP-6). Column order differs between the daily and history feeds; a single header-driven parser handles both. |
| `robots.txt` | Neither `www.amfiindia.com` nor `portal.amfiindia.com` serves a `robots.txt` (404 → no restrictions, treated permissively); the connector still honours `robots` by default. |
| Access method | Plain HTTP GET with the honest research User-Agent; no session/headers needed. |
| Politeness | Default 2 s min interval + retry/backoff. The daily file is a single request for the whole industry; callers should keep history ranges short. |
| Provenance | Source URL, fetch timestamp, and SHA-256 content hash captured per feed and appended to `manifest.jsonl` (FR-1.3). |
| Raw-then-parsed | Raw text stored immutably, then parsed to JSON; idempotent by NAV date for the daily feed (FR-1.4/FR-1.5). |
| Legal basis / redistribution | AMFI is the SEBI-recognised industry body; NAV data is published for public use. Attribute AMFI and link back (CMP-4). Confirm redistribution terms before any bulk re-publication/export (CMP-3, constrains FR-3.5/FR-6.4). |
| Refresh cadence | NAVs are published daily (business days). Incremental: a daily file already stored for its NAV date is skipped unless `--overwrite`. |
| Status | Connector + parser + ingestion implemented and verified end-to-end (daily NAVAll and a history range). |

## Usage — SEBI PMS

```bash
# Enumerate managers/years/months without fetching anything:
python -m cartoonomics.sebi_pms --dry-run

# Fetch one manager's March 2025 report (raw HTML + parsed JSON + manifest):
python -m cartoonomics.sebi_pms --out ./sebi_pms_data --pm INP000006457 --years 2025 --months 3

# Politely walk the first 5 managers for a month, capped for safety:
python -m cartoonomics.sebi_pms --out ./sebi_pms_data --years 2025 --months 3 --limit 5 --max-reports 5
```

## Usage — AMFI NAV

```bash
# Summarise today's full NAV file without writing anything:
python -m cartoonomics.amfi --dry-run

# Fetch + persist today's NAVAll (raw text + parsed JSON + manifest):
python -m cartoonomics.amfi --out ./amfi_data

# NAV history for a date range, scoped to one AMC (AMFI mf id):
python -m cartoonomics.amfi --out ./amfi_data --from 01-Jun-2026 --to 05-Jun-2026 --mf 53
```
