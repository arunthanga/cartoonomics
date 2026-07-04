"""Unit tests for the canonical financial data model (screener.in-style schema)."""

from __future__ import annotations

import json
from datetime import date

import pytest
from pydantic import ValidationError

from cartoonomics.canonical import (
    CANONICAL_SCHEMA_VERSION,
    BalanceSheetRow,
    CashFlowRow,
    CompanyDataset,
    CompanyIdentifiers,
    CompanyProfile,
    ComputedMetric,
    CompoundedGrowth,
    CorporateAction,
    CorporateActionType,
    Document,
    DocumentType,
    FinancialStatements,
    GrowthMetricName,
    InstrumentType,
    KeyRatiosSnapshot,
    MetricName,
    OperationalMetric,
    PeerComparison,
    PeerRow,
    PeriodType,
    ProfitLossRow,
    ProsAndCons,
    RatiosRow,
    ReportingPeriod,
    RevenueSegment,
    SegmentKind,
    ShareholdingRow,
    SourceRef,
    StatementBasis,
)
from tests.conftest import FIXED_TS


def _period(label: str = "FY2024", period_type: PeriodType = PeriodType.ANNUAL) -> ReportingPeriod:
    return ReportingPeriod(label=label, period_type=period_type, fiscal_year=2024)


def _source() -> SourceRef:
    return SourceRef(
        source="screener.in",
        source_url="https://www.screener.in/company/ACME/",
        fetched_at=FIXED_TS,
        source_hash="deadbeef",
        filing_period="FY2024",
    )


def _statements(basis: StatementBasis) -> FinancialStatements:
    return FinancialStatements(
        basis=basis,
        quarterly_results=[
            ProfitLossRow(
                period=_period("Q4 FY2024", PeriodType.QUARTERLY),
                sales=500.0,
                operating_profit=105.0,
                opm_pct=21.0,
                net_profit=70.0,
                eps=3.5,
            )
        ],
        profit_loss=[
            ProfitLossRow(
                period=_period(),
                sales=1800.0,
                expenses=1400.0,
                operating_profit=400.0,
                opm_pct=22.2,
                other_income=20.0,
                interest=30.0,
                depreciation=60.0,
                profit_before_tax=330.0,
                tax_pct=25.0,
                net_profit=247.5,
                eps=12.4,
                dividend_payout_pct=20.0,
            )
        ],
        balance_sheet=[
            BalanceSheetRow(
                period=_period(),
                equity_capital=40.0,
                reserves=1200.0,
                borrowings=300.0,
                other_liabilities=260.0,
                total_liabilities=1800.0,
                fixed_assets=900.0,
                cwip=50.0,
                investments=350.0,
                other_assets=500.0,
                total_assets=1800.0,
            )
        ],
        cash_flow=[
            CashFlowRow(
                period=_period(),
                operating_activity=350.0,
                investing_activity=-120.0,
                financing_activity=-180.0,
                net_cash_flow=50.0,
            )
        ],
        ratios=[
            RatiosRow(
                period=_period(),
                debtor_days=45.0,
                inventory_days=60.0,
                days_payable=40.0,
                cash_conversion_cycle=65.0,
                working_capital_days=70.0,
                roce_pct=18.5,
            )
        ],
        growth=[
            CompoundedGrowth(
                metric=GrowthMetricName.SALES,
                ten_year_pct=14.0,
                five_year_pct=12.0,
                three_year_pct=10.0,
                one_year_pct=8.0,
            )
        ],
        source=_source(),
    )


def _dataset() -> CompanyDataset:
    return CompanyDataset(
        profile=CompanyProfile(
            identifiers=CompanyIdentifiers(
                name="Acme Industries Ltd",
                isin="INE000A01001",
                nse_code="ACME",
                bse_code="500001",
                website="https://acme.example",
            ),
            instrument_type=InstrumentType.EQUITY,
            sector="Industrials",
            industry="Diversified",
            about="Acme makes everything.",
        ),
        snapshot=KeyRatiosSnapshot(
            market_cap=12000.0,
            current_price=600.0,
            high_52w=720.0,
            low_52w=410.0,
            stock_pe=24.0,
            book_value=310.0,
            dividend_yield_pct=1.2,
            roce_pct=18.5,
            roe_pct=16.0,
            face_value=2.0,
            debt_to_equity=0.24,
            no_of_shareholders=125000,
            as_of=date(2024, 3, 31),
        ),
        pros_and_cons=ProsAndCons(
            pros=["Low debt", "Improving margins"],
            cons=["Rising debtor days"],
        ),
        consolidated=_statements(StatementBasis.CONSOLIDATED),
        standalone=_statements(StatementBasis.STANDALONE),
        shareholding=[
            ShareholdingRow(
                period=_period("Mar 2024", PeriodType.QUARTERLY),
                promoters_pct=55.0,
                fiis_pct=15.0,
                diis_pct=12.0,
                government_pct=0.0,
                public_pct=18.0,
                others_pct=0.0,
                no_of_shareholders=125000,
                promoter_pledged_pct=0.0,
            )
        ],
        peers=PeerComparison(
            industry="Diversified",
            median_pe=22.0,
            median_market_cap=9000.0,
            peers=[
                PeerRow(
                    name="Beta Corp",
                    nse_code="BETA",
                    cmp=450.0,
                    pe=20.0,
                    market_cap=8000.0,
                    dividend_yield_pct=1.0,
                    net_profit_qtr=60.0,
                    qtr_profit_var_pct=8.0,
                    sales_qtr=480.0,
                    qtr_sales_var_pct=6.0,
                    roce_pct=17.0,
                )
            ],
        ),
        revenue_segments=[
            RevenueSegment(
                name="India",
                kind=SegmentKind.GEOGRAPHY,
                period=_period(),
                value=1200.0,
                pct_of_total=66.7,
            )
        ],
        operational_metrics=[
            OperationalMetric(
                name="Installed Capacity",
                period=_period(),
                value=350.0,
                unit="MW",
            )
        ],
        documents=[
            Document(
                doc_type=DocumentType.ANNUAL_REPORT,
                title="Annual Report FY2024",
                url="https://acme.example/ar2024.pdf",
                published_on=date(2024, 6, 30),
                period_label="FY2024",
            )
        ],
        corporate_actions=[
            CorporateAction(
                action_type=CorporateActionType.DIVIDEND,
                ex_date=date(2024, 7, 15),
                description="Final dividend ₹5/share",
                value=5.0,
            )
        ],
        metrics=[
            ComputedMetric(
                name=MetricName.XIRR,
                value=0.145,
                unit="ratio",
                formula_version="xirr-v1",
                computed_at=FIXED_TS,
                inputs={"years": 5.0},
                source=_source(),
            )
        ],
        provenance=_source(),
    )


@pytest.mark.unit
def test_full_dataset_roundtrips_json():
    ds = _dataset()
    restored = CompanyDataset.model_validate_json(ds.to_json())
    assert restored == ds
    assert restored.schema_version == CANONICAL_SCHEMA_VERSION


@pytest.mark.unit
def test_to_json_is_valid_json():
    payload = json.loads(_dataset().to_json())
    assert payload["profile"]["identifiers"]["nse_code"] == "ACME"
    assert payload["consolidated"]["basis"] == "consolidated"


@pytest.mark.unit
def test_dataset_requires_some_financials():
    with pytest.raises(ValidationError):
        CompanyDataset(
            profile=CompanyProfile(identifiers=CompanyIdentifiers(name="Acme")),
            provenance=_source(),
        )


@pytest.mark.unit
def test_dataset_accepts_single_basis():
    ds = CompanyDataset(
        profile=CompanyProfile(identifiers=CompanyIdentifiers(name="Acme")),
        standalone=_statements(StatementBasis.STANDALONE),
        provenance=_source(),
    )
    assert ds.consolidated is None
    assert ds.standalone is not None


@pytest.mark.unit
def test_shareholding_sum_out_of_tolerance_rejected():
    with pytest.raises(ValidationError):
        ShareholdingRow(
            period=_period(),
            promoters_pct=55.0,
            fiis_pct=15.0,
            diis_pct=12.0,
            government_pct=0.0,
            public_pct=5.0,
            others_pct=0.0,
        )


@pytest.mark.unit
def test_shareholding_partial_disclosure_skips_sum_check():
    row = ShareholdingRow(period=_period(), promoters_pct=55.0)
    assert row.fiis_pct is None


@pytest.mark.unit
def test_shareholding_pct_bounds_enforced():
    with pytest.raises(ValidationError):
        ShareholdingRow(period=_period(), promoters_pct=140.0)


@pytest.mark.unit
def test_metric_without_value_must_flag_insufficient():
    with pytest.raises(ValidationError):
        ComputedMetric(
            name=MetricName.RISK,
            formula_version="risk-v1",
            computed_at=FIXED_TS,
        )


@pytest.mark.unit
def test_metric_insufficient_data_is_valid():
    metric = ComputedMetric(
        name=MetricName.RISK,
        formula_version="risk-v1",
        computed_at=FIXED_TS,
        insufficient_data=True,
    )
    assert metric.value is None
    assert metric.insufficient_data


@pytest.mark.unit
def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        CompanyIdentifiers(name="Acme", ticker="nope")


@pytest.mark.unit
def test_negative_shareholder_count_rejected():
    with pytest.raises(ValidationError):
        ShareholdingRow(period=_period(), no_of_shareholders=-1)


@pytest.mark.unit
def test_json_schema_exportable_for_codegen():
    schema = CompanyDataset.model_json_schema()
    assert schema["title"] == "CompanyDataset"
    assert "$defs" in schema
