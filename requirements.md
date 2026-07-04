# cartoonomics — Requirements (Single Source of Truth)

> **This document is the single source of truth (SSOT) for cartoonomics.**
> Every feature, data source, screen, and technical decision must trace back to something here.
> If a change is made to the product, this document is updated **first**. If code and this
> document disagree, this document wins until it is explicitly amended.

---

## 0. Document Control

| Field | Value |
|---|---|
| Product | cartoonomics |
| Document | Product & Technical Requirements |
| Status | **Draft v0.1** (foundational scope) |
| Owner | Product Manager, cartoonomics |
| Audience | Engineering, Design, Data, Compliance, Founders |
| Last updated | See git history for this file |

### 0.1 How to use this document
- Read Sections 1–4 to understand **why** cartoonomics exists.
- Read Sections 5–9 to understand **what** we are building.
- Read Sections 10–14 to understand **how** it is built and designed.
- Read Sections 15–19 for delivery, risk, compliance, and open questions.

### 0.2 Change log
| Version | Summary |
|---|---|
| v0.1 | Initial requirements: vision, scope, data sources, cartoonization engine, personal cashflow simulator, UX, architecture, compliance, roadmap. |

---

## 1. Vision & Mission

**Vision.** Make the Indian financial system understandable to any human being, not just finance professionals — by turning dry disclosures, factsheets, and cashflows into clean, playful, **cartoonized** stories.

**Mission.** Do deep, defensible research across every major Indian asset class — PMS, AIF, mutual funds, NPS, gold, real estate — and present it through comparisons and visual narratives that a non-expert can grasp in seconds and an expert can trust.

**One-line pitch.** *"See where the money actually goes — cartoonized."*

---

## 2. Problem Statement

Retail and semi-professional investors in India face three problems:

1. **Fragmentation.** Data lives in dozens of silos — BSE/NSE filings, AMFI, SEBI, individual AMC/PMS/AIF websites, NPS trust, gold benchmarks, property indices. There is no single lens.
2. **Opacity.** PMS and AIF disclosures, company financials (P&L, balance sheet, cashflow), and shareholding patterns are dense, inconsistent, and intimidating.
3. **No apples-to-apples comparison.** Comparing a PMS to a mutual fund to real estate on *return, risk, liquidity, transferability, taxation, and cost* requires manual, error-prone work.

cartoonomics solves all three: **aggregate → analyze → cartoonize → compare.**

---

## 3. Target Users & Personas

| Persona | Description | Primary need |
|---|---|---|
| **Curious Retail Investor ("Riya")** | Salaried, invests in MFs/NPS, curious about PMS/AIF/gold/real estate. | "Explain it to me visually. Where does my money go and what do I get back?" |
| **DIY Power Investor ("Arjun")** | Reads annual reports, tracks XIRR, wants raw + derived data. | "Give me trustworthy numbers and let me compare deeply." |
| **Advisor / RIA ("Meera")** | Advises clients, needs credible comparisons and shareable visuals. | "Client-ready, correct, and easy to explain." |
| **The Household CFO ("Sunil")** | Plans family cashflow across a lifetime. | "Show me my cash over my life — income vs expected/unexpected expenses." |

**Design implication:** every screen must serve Riya (clarity) *without* alienating Arjun (depth). The default is cartoonized/simple; depth is one click away ("Show the numbers").

---

## 4. Product Goals & Non-Goals

### 4.1 Goals
- G1. Aggregate official, source-of-record Indian financial data across all six asset classes.
- G2. Compute standardized, comparable metrics (XIRR, liquidity score, transferability, cost, risk, taxation impact).
- G3. Cartoonize (a) **company money flow** — P&L, balance sheet, cashflow; and (b) **individual money flow** — lifetime and monthly.
- G4. Deliver a comparison experience across asset classes on user-selected parameters.
- G5. Make every page clean, cartoonized, and delightful — UX is the #1 priority.

### 4.2 Non-Goals (explicitly out of scope for now)
- N1. **We are not a broker or transaction platform.** No buy/sell/execution.
- N2. **We are not giving personalized investment advice** (SEBI RIA/RA regulated activity). We present research and education. See §16.
- N3. Not real-time tick data / trading terminal.
- N4. Not a tax filing tool (we *estimate* tax impact for comparison only).
- N5. Not global markets in the foundational scope — India first.

---

## 5. Key Concepts & Glossary

| Term | Meaning |
|---|---|
| **PMS** | Portfolio Management Service — SEBI-regulated, min. investment ₹50 lakh, discretionary/non-discretionary. |
| **AIF** | Alternative Investment Fund — Category I / II / III, min. ₹1 crore. |
| **Mutual Fund** | Pooled, SEBI/AMFI-regulated; factsheets published monthly. |
| **NPS** | National Pension System — regulated by PFRDA. |
| **XIRR** | Extended Internal Rate of Return — annualized return accounting for irregular cashflows and timing. |
| **Liquidity** | How quickly and cheaply an asset converts to cash without loss of value. |
| **Transferability** | Ease of transferring ownership (e.g., to heirs, nominees, or a buyer). |
| **Shareholding pattern** | Quarterly BSE/NSE disclosure of promoter/FII/DII/public holdings. |
| **Cartoonize** | Our core UX act: convert numbers/relationships into a clean, friendly, animated visual narrative. |

---

## 6. Scope Overview (Feature Map)

cartoonomics has five product pillars. Each maps to functional requirements in §7.

1. **Data Acquisition** — scrape/ingest official disclosures (§7.1).
2. **Analysis Engine** — normalize + compute metrics (§7.2).
3. **Asset-Class Comparison** — compare on parameters (§7.3).
4. **Company Money-Flow Cartoons** — P&L, balance sheet, cashflow (§7.4).
5. **Personal Money-Flow Cartoons** — lifetime + monthly simulator (§7.5).

### 6.1 Foundational vs later
- **Foundational (must-have):** MF + equities (BSE/NSE) ingestion; XIRR + core metrics; company cashflow cartoon; personal monthly cashflow cartoon; one clean comparison page.
- **Later:** PMS/AIF disclosure ingestion at scale, NPS, gold, real estate; lifetime simulator with unexpected-expense modeling; advisor sharing.

Phasing (no calendar estimates — see §15) is expressed in terms of subsystems and dependencies.

---

## 7. Functional Requirements

### 7.1 Data Acquisition (scraping & ingestion)

**Objective:** collect data from source-of-record, official sites, respecting each source's terms (see §17 Compliance — this is a hard gate).

**Sources (target list):**

| Asset class | Primary official sources | Data captured |
|---|---|---|
| Equities | BSE, NSE (corporate filings/announcements) | Quarterly/annual results, shareholding patterns, corporate actions, board meeting outcomes. |
| Mutual funds | AMFI, SEBI, AMC factsheets | NAV history, factsheets, expense ratio, portfolio holdings, key ratios (SD, Sharpe, beta, alpha, turnover). |
| PMS | SEBI monthly PMS disclosures, PMS provider disclosures | AUM, client count, monthly returns, strategy disclosures. |
| AIF | SEBI AIF disclosures, provider reports | Category, AUM, commitments, drawn amount, performance where disclosed. |
| NPS | PFRDA / NPS Trust, scheme NAVs | Scheme NAVs, allocation, returns by pension fund manager. |
| Gold | Recognized benchmarks (e.g., IBJA/exchange references) | Spot/benchmark price history. |
| Real estate | Recognized indices / public govt data | Price indices, rental yields where available. |

**Requirements:**
- FR-1.1 Each source has a dedicated, versioned **connector** with an explicit schema mapping to our canonical model (§13).
- FR-1.2 Connectors must be **polite**: respect `robots.txt`, rate limits, and terms of use; identify via a proper user agent; back off on errors. Prefer official APIs / bulk downloads / RSS/announcement feeds over HTML scraping when available.
- FR-1.3 Every ingested record stores **provenance**: source URL, fetch timestamp, source document hash, and a link to the original filing.
- FR-1.4 Ingestion is **idempotent** and **incremental** (only fetch new/changed filings).
- FR-1.5 **Raw-then-parsed** pipeline: store the raw artifact (PDF/HTML/CSV) immutably, then parse into structured data, so re-parsing is possible without re-fetching.
- FR-1.6 Parsing failures are queued for review, never silently dropped. Data quality metrics are tracked (see §15.2).
- FR-1.7 A scheduler runs connectors on cadences matching each source (e.g., NAV daily, results quarterly, shareholding quarterly).

### 7.2 Analysis Engine (normalize + compute)

- FR-2.1 Normalize disparate inputs into canonical entities: `Instrument`, `Filing`, `PriceSeries`, `Financials`, `Holding`.
- FR-2.2 Compute **XIRR** from an instrument's/portfolio's dated cashflows. XIRR must handle irregular contributions, redemptions, dividends, and current valuation.
- FR-2.3 Compute a **Liquidity Score** (0–100) per asset class using: settlement/redemption time, exit load/lock-in, market depth, and penalty on exit. Rubric documented and versioned.
- FR-2.4 Compute a **Transferability Score** (0–100): nominee/heir transfer ease, demat vs non-demat, third-party sale friction, paperwork.
- FR-2.5 Compute **Cost** (TER/management fee/carry/stamp/brokerage/AMC), **Risk** (volatility, drawdown, category-appropriate), and **Taxation impact** (holding-period-based estimate; assumptions surfaced).
- FR-2.6 All computed metrics store their **inputs, formula version, and timestamp** for reproducibility and auditability.
- FR-2.7 Metrics degrade gracefully: if a source lacks data (common for PMS/AIF/real estate), show "insufficient data" rather than a misleading number.

### 7.3 Asset-Class Comparison

- FR-3.1 User selects 2+ items (can be cross-asset-class, e.g., a specific MF vs a PMS strategy vs gold).
- FR-3.2 User selects parameters (XIRR, liquidity, transferability, cost, risk, taxation, min investment, lock-in).
- FR-3.3 Output is a **cartoonized comparison** (see §7.6): side-by-side "characters"/cards, radar/spider "spark" charts, and a plain-language verdict per parameter ("Most liquid: Mutual Fund 🥇").
- FR-3.4 Every comparison cell links to the underlying source/provenance.
- FR-3.5 Comparisons are shareable via a stable URL (respecting data licensing — see §17).

### 7.4 Company Money-Flow Cartoons (deep research)

For a selected listed company, cartoonize the financial statements:

- FR-4.1 **Cashflow cartoon:** an animated flow (Sankey-style, cartoonized) showing cash from Operating, Investing, Financing activities → net change in cash. Money is depicted as flowing "coins/streams."
- FR-4.2 **P&L cartoon:** Revenue → COGS → Gross Profit → Opex → EBITDA → Interest/Tax/Depreciation → Net Profit, as a friendly waterfall of characters/blocks.
- FR-4.3 **Balance sheet cartoon:** Assets vs Liabilities + Equity as a balanced "see-saw"/scale metaphor, drillable into line items.
- FR-4.4 **Shareholding-pattern cartoon:** promoter/FII/DII/public as a pie of characters, with quarter-over-quarter movement animated.
- FR-4.5 Multi-year trend "story mode": step through years and watch the cartoon evolve.
- FR-4.6 Every figure traces to the exact BSE/NSE filing (FR-1.3).

### 7.5 Personal Money-Flow Cartoons (individual simulator)

- FR-5.1 **Monthly cashflow cartoon:** income streams → fixed expenses → variable expenses → savings/investments → surplus/deficit, as a flowing cartoon. User inputs income and expense buckets.
- FR-5.2 **Lifetime cashflow cartoon:** timeline from now to end-of-life showing income phases (working years, retirement), expected life events (education, marriage, home, children, retirement), and **unexpected expenses** (medical, job loss, emergencies) modeled as probabilistic "surprise" events.
- FR-5.3 Inputs: current age, income (with growth assumption), recurring expenses, one-off planned events, assets, inflation assumption, expected returns per asset class (pulled from §7.2 where possible).
- FR-5.4 Outputs: a cartoon "river of money" over life; net-worth curve; "will I run out?" moment highlighted; scenario toggles (e.g., "add a medical shock at 55").
- FR-5.5 All assumptions are **visible and editable**; nothing hidden. Defaults are conservative and cited.
- FR-5.6 **Not advice:** the simulator shows scenarios, clearly labeled as illustrative (see §16).

### 7.6 Cartoonization Engine (cross-cutting)

The visual system that powers §7.3–7.5. This is the product's soul.

- FR-6.1 A reusable component library of "cartoon primitives": money-stream, coin-stack, character card, see-saw, waterfall block, surprise-event pop.
- FR-6.2 Every cartoon has a **"Show the numbers"** toggle that reveals the exact underlying table/values.
- FR-6.3 Cartoons are **accessible** (see §12): every visual has a text/table equivalent; not color-only; keyboard navigable; screen-reader labeled.
- FR-6.4 Cartoons are **exportable** (PNG/share link) for advisors, respecting data licensing.
- FR-6.5 Consistent characters, palette, and motion language across the whole app (design system — §11).

---

## 8. Information Architecture (page-by-page)

Clean, cartoonized pages. One primary job per page.

1. **Home / "The Money Universe"** — friendly entry; pick an asset class or a task ("Compare", "Explore a company", "Plan my cash").
2. **Asset-class explorer** — browse MFs / equities / PMS / AIF / NPS / gold / real estate with cartoon summaries.
3. **Instrument page** — one MF/stock/PMS: cartoonized snapshot + "Show the numbers".
4. **Company deep-dive** — the §7.4 cartoons (cashflow, P&L, balance sheet, shareholding).
5. **Compare** — the §7.3 comparison experience.
6. **My Cashflow** — the §7.5 personal simulator (monthly + lifetime).
7. **Sources & Trust** — provenance, methodology, disclaimers (builds credibility; see §16/§17).
8. **Glossary / Learn** — cartoon explainers of terms in §5.

**Navigation principle:** never more than **two clicks** from Home to any cartoon.

---

## 9. UX Principles (the #1 priority)

- UX-1. **Cartoon first, numbers on demand.** Default view is visual and playful; depth is always one toggle away.
- UX-2. **Plain language.** No unexplained jargon; every term links to the glossary.
- UX-3. **Progressive disclosure.** Start simple; reveal complexity only when asked.
- UX-4. **Trust by transparency.** Every number links to its source and its formula.
- UX-5. **Delight, tastefully.** Motion and character add joy but never obscure meaning or slow comprehension.
- UX-6. **Fast.** Perceived performance matters; cartoons render progressively, skeletons first.
- UX-7. **Mobile-first, responsive.** Riya is on a phone.
- UX-8. **Accessible to all** (WCAG 2.1 AA target — §12).
- UX-9. **Consistency.** One design system, one set of characters, one motion vocabulary.

---

## 10. Design Language (cartoonized)

- Friendly, rounded, high-contrast illustration style; a small cast of recurring "money characters."
- Motion communicates *flow* (cash moving), *balance* (see-saw), and *surprise* (unexpected events).
- Color used semantically (inflow/outflow, profit/loss) **and** redundantly encoded (icon/label) for accessibility.
- A documented design system (tokens: color, type, spacing, motion) is the source of truth for UI.

---

## 11. Technical Architecture (high level)

> Concrete stack choices are deferred to an engineering ADR; this section fixes the shape, not the vendors.

- **Ingestion layer:** independent, scheduled connectors (§7.1) writing raw artifacts to immutable storage + a parse stage writing to the canonical store.
- **Data store:** relational canonical model (§13) for structured entities; object storage for raw filings/PDFs; a time-series store (or partitioned tables) for prices/NAVs.
- **Analysis service:** computes metrics (§7.2), versioned and reproducible.
- **API layer:** serves normalized data + computed metrics + provenance to the frontend.
- **Frontend:** cartoonization engine (§7.6) — component-driven, animated, accessible, mobile-first.
- **Jobs/scheduler:** orchestrates connectors, recomputation, and data-quality checks.

**Cross-cutting requirements:**
- TA-1. Separation of **raw** vs **derived** data (never overwrite raw).
- TA-2. Every derived value is reproducible from raw + formula version.
- TA-3. Connectors are isolated so one source breaking cannot take down others.
- TA-4. Configuration and secrets are never committed; environment-driven.

---

## 12. Accessibility (NFR, non-negotiable)

- A11Y-1. Target **WCAG 2.1 AA**.
- A11Y-2. Every cartoon has a semantic, screen-reader-friendly text/table equivalent.
- A11Y-3. No information conveyed by color alone.
- A11Y-4. Full keyboard navigation; visible focus states.
- A11Y-5. Respect `prefers-reduced-motion`; provide a static equivalent for every animation.

---

## 13. Canonical Data Model (initial)

Core entities (fields illustrative, to be finalized in an ADR):

- **Instrument**(id, type[EQUITY|MF|PMS|AIF|NPS|GOLD|REALESTATE], name, identifiers[ISIN/scheme code/scrip], provider, meta)
- **Filing**(id, instrument_id, type[RESULTS|SHAREHOLDING|FACTSHEET|DISCLOSURE], period, source_url, fetched_at, raw_ref, source_hash)
- **PriceSeries**(instrument_id, date, value, kind[NAV|CLOSE|BENCHMARK])
- **Financials**(instrument_id, period, statement[PL|BS|CF], line_item, value, unit, currency, source_filing_id)
- **Holding**(instrument_id, period, holder_category, pct, source_filing_id)
- **Metric**(instrument_id, name[XIRR|LIQUIDITY|TRANSFERABILITY|COST|RISK|TAX], value, formula_version, inputs_ref, computed_at)
- **UserScenario**(id, inputs_json, created_at) — for the personal simulator (privacy — §14).

**Invariant:** every `Metric` and `Financials`/`Holding` row must reference the `Filing`/source it came from (provenance).

---

## 14. Privacy & Security

- SEC-1. Personal simulator inputs (income, expenses) are **sensitive**. Prefer client-side/local computation; if stored, encrypt and minimize; never sell or share.
- SEC-2. No PII in logs or analytics.
- SEC-3. Standard web security hygiene (authN/authZ if accounts are added later, input validation, HTTPS, dependency scanning).
- SEC-4. Clear data-retention and deletion policy for any stored user scenarios.

---

## 15. Delivery Plan (phased by subsystem, not calendar)

Phases are ordered by dependency, not dates.

- **Phase A — Foundations.** Canonical model (§13); one equity connector (BSE/NSE announcements + results); one MF connector (AMFI NAV + factsheet); provenance + raw/derived split.
- **Phase B — Analysis.** XIRR, liquidity, transferability, cost, risk, tax metrics (§7.2) with reproducibility.
- **Phase C — First cartoons.** Company cashflow cartoon (§7.4) + personal monthly cashflow cartoon (§7.5) + the design system (§10).
- **Phase D — Comparison.** Cross-asset comparison experience (§7.3).
- **Phase E — Breadth.** PMS/AIF disclosure ingestion, NPS, gold, real estate; lifetime simulator with unexpected-expense modeling; sharing/export.

**Dependency notes:** B depends on A. C depends on A (and B for real numbers). D depends on B + C. E depends on A–D and is the most compliance-sensitive (§17).

### 15.1 Definition of Done (per feature)
- Traces to a requirement ID here.
- Cartoon has a "Show the numbers" equivalent (FR-6.2) and passes accessibility checks (§12).
- Every displayed number links to provenance (FR-1.3).
- Assumptions/formulas are versioned and visible.

### 15.2 Success Metrics
- **Comprehension:** users correctly answer "where did the money go?" after viewing a cartoon (usability tests).
- **Trust:** % of numbers with visible provenance (target 100%).
- **Data quality:** parse success rate per connector; freshness (lag vs source).
- **Engagement:** comparisons created, company deep-dives viewed, simulator scenarios run.
- **Accessibility:** automated + manual audit pass rate.

---

## 16. Regulatory Positioning (India)

- REG-1. cartoonomics is **research & education**, not investment advice, not distribution/execution. This framing must be reflected in UI copy and the "Sources & Trust" page.
- REG-2. If we ever cross into personalized recommendations, that is SEBI **RIA/Research Analyst** regulated territory — a separate, explicit decision with legal review. Until then, avoid recommend/buy/sell language.
- REG-3. All performance figures carry standard disclaimers ("past performance is not indicative of future returns").
- REG-4. The personal simulator is labeled **illustrative**; assumptions are user-editable and visible (FR-5.5).

---

## 17. Data Sourcing Compliance (hard gate)

Scraping official sites carries legal and ethical obligations. **No connector ships without clearing this gate.**

- CMP-1. Review each source's **terms of use** and `robots.txt`; prefer official APIs, bulk data, RSS/announcement feeds, and licensed feeds over HTML scraping.
- CMP-2. Respect rate limits; never degrade a source's service. Identify honestly via user agent.
- CMP-3. Track **redistribution rights** per source. Some data (e.g., certain exchange/benchmark data) may be viewable but **not redistributable/shareable/exportable** — this directly constrains FR-3.5 and FR-6.4.
- CMP-4. Attribute sources; link back to originals.
- CMP-5. Maintain a **source register**: for each source, its legal basis for use, license, permitted uses, and refresh cadence.
- CMP-6. When in doubt, obtain the licensed/paid feed rather than scrape.

**Open compliance questions are tracked in §19.**

---

## 18. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Source ToS prohibits scraping/redistribution | Legal; blocks features | §17 gate; prefer licensed feeds; source register; legal review before Phase E. |
| PMS/AIF data is sparse/inconsistent | Misleading comparisons | FR-2.7 "insufficient data"; never fabricate; clearly mark gaps. |
| Parsing breaks when sites change | Stale/wrong data | Raw-then-parsed (FR-1.5); parse-failure queue; data-quality metrics. |
| Cartoons oversimplify → mislead | Trust/regulatory | Always "Show the numbers"; provenance; disclaimers (§16). |
| Being seen as giving advice | Regulatory | REG-1/REG-2 framing and copy discipline. |
| Personal financial data leakage | Trust/legal | Client-side compute preference; encryption; no PII in logs (§14). |

---

## 19. Open Questions & Assumptions

**Assumptions made in this draft (to validate):**
- A1. India-only, foundational scope; INR only.
- A2. No transactions/execution — research & education product.
- A3. Users accept editable, visible assumptions in the personal simulator.
- A4. "Cartoonized" means clean, friendly, animated data storytelling — not literal comic strips.

**Open questions (owners to resolve):**
- Q1. Which exact BSE/NSE/AMFI/SEBI/PFRDA access channels are licensed/permitted for our uses? (Compliance)
- Q2. Do we need user accounts in the foundational scope, or is the simulator fully local? (Product/Eng)
- Q3. Which gold and real-estate benchmarks are both authoritative **and** redistributable? (Compliance/Data)
- Q4. Exact rubric weights for Liquidity and Transferability scores. (Product/Data)
- Q5. Concrete tech stack (frontend framework, DB, animation lib) — to be fixed in an ADR. (Eng)
- Q6. Tax estimation depth — how detailed before it risks looking like advice? (Product/Legal)

---

## 20. Appendix — Requirement Index

- Data acquisition: FR-1.1 … FR-1.7
- Analysis engine: FR-2.1 … FR-2.7
- Comparison: FR-3.1 … FR-3.5
- Company cartoons: FR-4.1 … FR-4.6
- Personal cartoons: FR-5.1 … FR-5.6
- Cartoonization engine: FR-6.1 … FR-6.5
- UX: UX-1 … UX-9
- Accessibility: A11Y-1 … A11Y-5
- Architecture: TA-1 … TA-4
- Security/Privacy: SEC-1 … SEC-4
- Regulatory: REG-1 … REG-4
- Compliance: CMP-1 … CMP-6

> **Reminder:** this file is the single source of truth. Update it before you change the product.
