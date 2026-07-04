"""The top-level canonical company dataset.

``CompanyDataset`` is the screener.in / tijorifinance.com "company page" as one
validated object: profile + snapshot, both reporting bases of the financial
statements, shareholding, peers, revenue mix, operational metrics, documents,
corporate actions, and derived metrics — all anchored to dataset-level
provenance (the §13 invariant).

This is the *input* canonical model (§13). The *output* rendering contract is the
separate ``CartoonSpec`` in :mod:`cartoonomics.format`; analysis builders read a
``CompanyDataset`` and emit a ``CartoonSpec``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cartoonomics.canonical.business import OperationalMetric, RevenueSegment
from cartoonomics.canonical.common import SourceRef
from cartoonomics.canonical.company import CompanyProfile, KeyRatiosSnapshot, ProsAndCons
from cartoonomics.canonical.documents import CorporateAction, Document
from cartoonomics.canonical.financials import FinancialStatements
from cartoonomics.canonical.metrics import ComputedMetric
from cartoonomics.canonical.peers import PeerComparison
from cartoonomics.canonical.shareholding import ShareholdingRow

CANONICAL_SCHEMA_VERSION = "1.0.0"


class CompanyDataset(BaseModel):
    """A complete, validated canonical view of one listed company."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=CANONICAL_SCHEMA_VERSION)
    profile: CompanyProfile
    snapshot: KeyRatiosSnapshot | None = None
    pros_and_cons: ProsAndCons | None = None

    consolidated: FinancialStatements | None = None
    standalone: FinancialStatements | None = None

    shareholding: list[ShareholdingRow] = Field(default_factory=list)
    peers: PeerComparison | None = None
    revenue_segments: list[RevenueSegment] = Field(default_factory=list)
    operational_metrics: list[OperationalMetric] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)
    corporate_actions: list[CorporateAction] = Field(default_factory=list)
    metrics: list[ComputedMetric] = Field(default_factory=list)

    provenance: SourceRef

    @model_validator(mode="after")
    def _has_some_financials(self) -> "CompanyDataset":
        """A company dataset must carry at least one reporting basis."""
        if self.consolidated is None and self.standalone is None:
            raise ValueError("dataset must include consolidated and/or standalone financials")
        return self

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize to canonical JSON for the API / regression baselines."""
        return self.model_dump_json(indent=indent)
