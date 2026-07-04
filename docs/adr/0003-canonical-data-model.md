# ADR-0003: Canonical Financial Data Model (screener.in-style schema)

- **Status:** Accepted (foundational scope)
- **Implements:** `requirements.md` §13 (Canonical Data Model), §7.1–§7.4
- **Scope:** the structured schema for the company data cartoonomics ingests and
  shows, modelled on what **screener.in** and **tijorifinance.com** expose.

> ADRs record a decision and its rationale. ADR-0001 fixed the stack; ADR-0002
> fixed the repo structure. This one fixes the **input** data model — the
> canonical, validated shape that connectors/parsers write and the API/analysis
> read — as distinct from the **output** `CartoonSpec` rendering contract.

---

## 1. Context

`requirements.md` §13 sketches a canonical model (`Instrument`, `Filing`,
`PriceSeries`, `Financials`, `Holding`, `Metric`) but leaves the fields
"illustrative, to be finalized in an ADR". The product goal (§4.1 G1, §7.4) is to
show the same depth of company data users already trust on **screener.in** and
**tijorifinance.com**. We need a concrete, versioned schema so:

- connectors (§7.1) have an explicit target to map into (FR-1.1);
- analysis (§7.2) and the API (§11) share one validated contract;
- provenance is structural, not optional (FR-1.3, §13 invariant);
- missing data degrades gracefully instead of misleading (FR-2.7).

## 2. Decision

Model the canonical data as **pydantic v2** models (consistent with ADR-0001 and
the `CartoonSpec` contract) in a new package
`packages/pipeline/src/cartoonomics/canonical/`. `CartoonSpec`
(`cartoonomics.format`) stays the *rendering* contract; `canonical` is the
*source* data. Analysis builders read a `CompanyDataset` and emit a `CartoonSpec`.

Design rules:

- **Strongly-typed rows for standardised statements.** screener.in's P&L, balance
  sheet, cash flow, ratios, and shareholding line items are fixed, so each is a
  typed `*Row` = one period column. This makes the schema self-documenting.
- **Free-form models for open-ended data.** tijorifinance.com's operational
  metrics and revenue-mix segments are arbitrary, so they use `name`/`value`.
- **`float | None` everywhere for amounts.** A missing cell is `None`, never a
  misleading `0` (FR-2.7). Losses/outflows are negative.
- **Standalone vs consolidated** is a first-class `StatementBasis`; both bases can
  coexist in one dataset (both sites offer the toggle).
- **Provenance is required** at the dataset level and available per statement
  (`SourceRef`), upholding the §13 invariant.
- **Extra fields forbidden** (`extra="forbid"`) so schema drift fails loudly.

## 3. Model map (screener.in / tijorifinance.com → schema)

| Site section | Model(s) |
|---|---|
| Company header, links, sector/industry, about | `CompanyProfile`, `CompanyIdentifiers` |
| "Key Ratios" grid (Mkt Cap, CMP, High/Low, P/E, Book Value, Div Yield, ROCE, ROE, Face Value, D/E) | `KeyRatiosSnapshot` |
| Pros & Cons | `ProsAndCons` |
| Quarterly Results | `FinancialStatements.quarterly_results` (`ProfitLossRow`) |
| Profit & Loss (10y + TTM) | `FinancialStatements.profit_loss` (`ProfitLossRow`) |
| Compounded Sales/Profit growth, Stock Price CAGR, ROE | `CompoundedGrowth` |
| Balance Sheet | `BalanceSheetRow` |
| Cash Flows | `CashFlowRow` |
| Ratios (debtor/inventory/payable days, CCC, WC days, ROCE) | `RatiosRow` |
| Shareholding Pattern (Promoter/FII/DII/Govt/Public, pledge, #holders) | `ShareholdingRow` |
| Peers / Peer Comparison | `PeerComparison`, `PeerRow` |
| Revenue mix / segment break-up (tijori) | `RevenueSegment` |
| Operational Metrics (tijori, 1000s of KPIs) | `OperationalMetric` |
| Documents (annual reports, announcements, concalls, ratings, presentations) | `Document` |
| Corporate Actions (dividend/split/bonus/buyback/rights) | `CorporateAction` |
| Derived comparison metrics (XIRR, liquidity, …) | `ComputedMetric` |
| The whole company page | `CompanyDataset` |

## 4. Consequences

- **Positive:** one validated input contract; provenance and graceful-degradation
  baked in; a JSON Schema can be emitted (`CompanyDataset.model_json_schema()`)
  to generate TypeScript types alongside the `CartoonSpec` seam (ADR-0001 §3).
- **Costs/risks:** the schema will evolve as connectors meet real filings
  (`schema_version` is versioned for that); tijori's operational metrics are
  intentionally loose (`name`/`value`) and rely on connector-side normalisation.

## 5. Alternatives considered

| Choice | Alternatives | Why not |
|---|---|---|
| Typed `*Row` per statement | generic `line_item`/`value` rows for everything | loses type-safety and self-documentation for the standardised screener line items |
| Separate `canonical` package | extend `format/` | keeps the input model and the render contract decoupled (ADR-0001 §3) |
| pydantic v2 | dataclasses + jsonschema, protobuf | validation + JSON + schema export in one; consistent with the rest of the repo |
