# Scrapable data-source landscape (India)

A discovery survey of where each asset class's data lives, whether it is
**scrapable/ingestable**, and the **compliance posture** of each source. It
extends `requirements.md` §7.1 (the sources target list) and feeds the shipping
gate in [`../compliance/source-register.md`](../compliance/source-register.md).
When this doc disagrees with `requirements.md` (the SSOT), the SSOT wins.

> **Guiding principle (from §17 CMP-1/CMP-6 and reaffirmed by the product owner):
> prefer official / source-of-record feeds over private commercial websites.**
> Private aggregators are convenient but are *derived* data, usually
> ToS-restricted, and rarely add anything the official source lacks.

## Legend — ingestion verdict

| Verdict | Meaning |
|---|---|
| ✅ **Official feed** | Authoritative, machine-readable, permitted. Preferred. Build a connector. |
| 🟢 **Official, scrape OK** | Authoritative HTML/portal, `robots`-permitted, no anti-bot. Scrape politely. |
| 🟡 **Official, hard** | Authoritative but anti-bot / JS / session-gated. Needs care (browser session, backoff) after the §17 gate. |
| 🔴 **Restricted / licensed** | ToS prohibits scraping, or data is paid/licensed. Do **not** scrape; obtain a feed. |
| ⚪ **Private aggregator** | Non-source-of-record commercial site. Avoid; use the official origin it derives from. |

*Verdicts below reflect probes run on 2026-07-04 (`robots.txt` + endpoint reachability with the honest research User-Agent). Anti-bot behaviour changes over time — re-verify before building.*

---

## 1. Mutual funds

| Data | Source | Endpoint / form | Verdict | Notes |
|---|---|---|---|---|
| Daily NAV (all schemes) | **AMFI** | `portal.amfiindia.com/spages/NAVAll.txt` | ✅ | **Implemented** (`AmfiConnector`). No `robots.txt` → permissive. |
| Historical NAV | **AMFI** | `DownloadNAVHistoryReport_Po.aspx?tp=1&frmdt=&todt=&mf=` | ✅ | **Implemented**. Date-range, optional AMC. |
| Scheme factsheet (top-10 holdings, TER, risk) | AMC websites + AMFI | "Scheme Performance" section | 🟢 | Standardised by SEBI/AMFI; per-AMC PDFs; AMFI aggregates. |
| Monthly full portfolio (every holding, XLS/CSV) | AMC websites | per-AMC "Portfolio Disclosure" | 🟢 | Mandated machine-readable since 2020; per-AMC URLs vary. |
| SID / SAI / KIM (offer docs) | AMC + **SEBI** | `sebi.gov.in` (Mutual Funds → Offer Documents) | 🟢 | SEBI `robots` permits; SEBI is source-of-record for filings. |
| Industry AUM statistics | **AMFI** | `amfiindia.com` statistics | 🟢 | Aggregate industry data. |

**Recommendation:** AMFI (NAV — done) + per-AMC factsheet/portfolio connectors + SEBI for offer docs. This is the §6.1 foundational MF path.

## 2. PMS (Portfolio Management Services)

| Data | Source | Endpoint / form | Verdict | Notes |
|---|---|---|---|---|
| Monthly report (AUM, clients, TWRR performance) | **SEBI** | `OtherAction.do?doPmr=yes` (form POST) | 🟢 | **Implemented** (`SebiPmsConnector`). HTML, not PDF. |
| Registered PMS list | **SEBI** | `OtherAction.do?doRecognised=yes` | 🟢 | Same portal pattern; downloadable list. |
| Per-provider disclosure docs | PMS provider sites | varies | 🟡 | Fragmented; per-provider, no standard endpoint. |

## 3. AIF (Alternative Investment Funds)

| Data | Source | Endpoint / form | Verdict | Notes |
|---|---|---|---|---|
| Registered AIF list (Cat I/II/III) | **SEBI** | `OtherAction.do?doRecognised=yes&intmId=11` | 🟢 | Probed 200 OK; downloadable list (same pattern as PMS). |
| Quarterly/annual Activity Reports (QAR) | SEBI **SI Portal** | `siportal.sebi.gov.in` | 🔴 | Login-gated regulatory filings — **not public**. |
| PPM (private placement memorandum), investor complaints | AIF/issuer (private) | — | 🔴 | Disclosed to investors, not centrally public. |
| Performance benchmarking | SEBI-appointed benchmarking agencies (CRISIL etc.) | — | 🔴 | Subscription/licensed. |

**Recommendation:** Only the **registered AIF list** is reliably scrapable (SEBI). Fund-level AIF performance is largely **not public** (FR-2.7 "insufficient data" applies).

## 4. Gold & Sovereign Gold Bonds (SGB)

| Data | Source | Endpoint | Verdict | Notes |
|---|---|---|---|---|
| Gold benchmark AM/PM rates | **IBJA** | `ibja.co` / `ibjarates.com` | 🟡/🔴 | `robots` permits browsing, but historical rate data is members/licensed (CMP-3). Daily rate is published. |
| Gold ETF NAVs | **AMFI** | NAVAll (category "Other Scheme - Gold ETF") | ✅ | **Already ingested** via `AmfiConnector`. |
| SGB issue price, tranches, redemption price | **RBI** | `rbi.org.in` press releases | 🔴/🟡 | RBI main site blocks bots (HTTP 418, Akamai). Use RBI PDFs manually or a licensed feed. |
| SGB secondary-market price | **NSE / BSE** | exchange debt/ETF segment | 🟡 | SGBs trade on exchanges; see §6 exchange anti-bot notes. |

## 5. Government bonds (G-secs, T-bills, SDLs)

| Data | Source | Endpoint | Verdict | Notes |
|---|---|---|---|---|
| NDS-OM traded prices/yields, G-sec data | **CCIL** | `ccilindia.com` | 🟢 | Probed 200 OK; `robots` allow-all. Authoritative for G-sec market data. |
| Retail G-sec (RBI Retail Direct) | **RBI Retail Direct** | `rbiretaildirect.org.in` | 🟢 | `robots` allow-all. Retail platform for G-secs/SGB/T-bills. |
| Auctions, yield curve, DBIE time series | **RBI** | `rbi.org.in` / DBIE | 🔴/🟡 | RBI main site blocks bots (418). DBIE has bulk downloads but is anti-bot; treat as manual/licensed. |
| Listed G-sec/SDL secondary trades | **NSE / BSE** | exchange debt segment | 🟡 | See §6. |

**Recommendation:** **CCIL** + **RBI Retail Direct** are the scrapable, authoritative G-sec sources.

## 6. Corporate / private bonds listed on exchanges

| Data | Source | Endpoint | Verdict | Notes |
|---|---|---|---|---|
| Listed bond/NCD master, daily debt trades | **NSE** | `nseindia.com` debt-market reports/APIs | 🟡 | `robots` permits (`Allow: /`), but APIs need a browser session + headers (direct call failed). Anti-bot; use a real session after the §17 gate. |
| Listed bond/NCD data, debt bhavcopy | **BSE** | `bseindia.com` debt segment | 🟡 | Homepage/`robots` blocked at the edge (HTTP 403 Akamai). Downloadable reports exist but are anti-bot. |
| NCD/bond public-issue filings, prospectuses | **SEBI** | `sebi.gov.in` (Filings) | 🟢 | Source-of-record for offer documents. |
| Security/ISIN master | **NSDL / CDSL** | depository sites | 🟡 | ISIN master and corporate-action data. |
| Credit ratings | CRISIL / ICRA / CARE / India Ratings | rating-agency sites | 🟢/🟡 | Ratings are published per-issue on agency sites (often HTML). |

**Recommendation:** The **exchanges (NSE/BSE debt segments)** + **SEBI filings** are the source-of-record for listed corporate bonds. Both exchanges are anti-bot, so a polite browser-session connector is required (deferred behind §17).

## 7. Online Bond Platform Providers — GoldenPi, Fincues, IndiaBonds, INRBonds, …

These are **SEBI-registered Online Bond Platform Providers (OBPPs) / debt brokers**
(framework: SEBI circular of 16 Sep 2022). They are **distribution front-ends**, not
data sources of record.

| Platform | Verdict | Finding |
|---|---|---|
| **GoldenPi** (`goldenpi.com`) | ⚪ / 🔴 | SEBI-registered OBPP. **No public developer API** (only B2B SaaS for issuers). `robots.txt` allows listing pages but blocks user/session areas; ToS prohibits automated extraction/scraping. Its inventory is sourced from the **BSE new debt segment (secondary) + primary issuances** — i.e. the exchanges are the real origin. |
| **Fincues** (`fincues.com`) | ⚪ | Private SGB-information site; **did not resolve/connect** from our probe (unreliable). Not an OBPP for corporate bonds; SGB data originates from RBI/exchanges. |
| IndiaBonds, INRBonds, Wint, Jiraaf, GripInvest, Aspero, BondSkart, StableMoney | ⚪ / 🔴 | Same class: registered debt brokers, ToS-restricted, data derives from the exchange debt segments. |

**Verdict for OBPP aggregators:** **Do not scrape.** They add no source-of-record
data over NSE/BSE + SEBI, and scraping a registered broker's site is ToS-restricted
(and against the "official over private" principle the product owner set). If richer
coverage than the exchange feeds is needed, pursue a **commercial data licence / API
partnership** (CMP-6), not scraping.

---

## Summary — build priority

| Priority | Source | Verdict | Status |
|---|---|---|---|
| P0 | AMFI NAV (daily + history) | ✅ | **Done** |
| P0 | SEBI PMS monthly report | 🟢 | **Done** |
| P1 | SEBI registered lists (AIF / PMS / brokers) | 🟢 | Next: reuse `OtherAction.do` pattern |
| P1 | CCIL G-sec market data | 🟢 | Candidate connector |
| P1 | RBI Retail Direct (G-sec/SGB) | 🟢 | Candidate connector |
| P2 | AMC factsheets / monthly portfolios | 🟢 | Per-AMC, fragmented |
| P2 | SEBI offer-document filings (MF/NCD) | 🟢 | Source-of-record |
| P3 | NSE / BSE debt segments | 🟡 | Anti-bot; browser-session connector, §17 gate |
| P3 | IBJA gold rates | 🟡/🔴 | Daily rate OK; history licensed |
| — | RBI main site / DBIE | 🔴/🟡 | Anti-bot (418); manual or licensed |
| — | OBPP aggregators (GoldenPi/Fincues/…) | ⚪/🔴 | **Avoid — use exchange/SEBI origin; licence if needed** |

## Compliance reminder (§17, hard gate)

Every new connector must clear the §17 gate and get a
[`source-register`](../compliance/source-register.md) entry before it ships:
review ToS + `robots.txt`, prefer official feeds, rate-limit and identify
honestly, capture provenance (FR-1.3), and confirm redistribution rights (CMP-3)
before any export/share feature. **When in doubt, licence — don't scrape (CMP-6).**
