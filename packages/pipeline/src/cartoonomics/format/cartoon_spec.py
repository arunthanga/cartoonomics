"""Pydantic models defining the predefined CartoonSpec exchange format.

Design goals (traceable to requirements.md):

* FR-6.1  Reusable cartoon primitives -> ``CartoonNode`` / ``CartoonFlow``.
* FR-6.2  "Show the numbers" -> every spec carries a ``table``.
* FR-6.3  Accessibility -> mandatory ``Accessibility`` block; not colour-only.
* FR-1.3 / FR-4.6  Provenance -> mandatory ``Provenance`` block.
* A11Y-5  Reduced motion -> ``Animation.reduced_motion_ok`` + static fallback.

The format is intentionally renderer-agnostic: any frontend (the bundled
vanilla-JS renderer, or a future React/Framer-Motion app) can consume it.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

CARTOON_SPEC_VERSION = "1.0.0"


class CartoonType(str, Enum):
    """The kind of cartoon a spec describes (maps to §7.4 / §7.5)."""

    CASHFLOW = "cashflow"  # FR-4.1
    PL_WATERFALL = "pl_waterfall"  # FR-4.2
    BALANCE_SEESAW = "balance_seesaw"  # FR-4.3
    SHAREHOLDING_PIE = "shareholding_pie"  # FR-4.4
    PERSONAL_MONTHLY = "personal_monthly"  # FR-5.1


class FlowDirection(str, Enum):
    """Semantic direction of a money flow. Encoded redundantly for A11Y-3."""

    INFLOW = "inflow"
    OUTFLOW = "outflow"
    NEUTRAL = "neutral"


class Provenance(BaseModel):
    """Where every number came from (FR-1.3, FR-4.6, UX-4)."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., description="Source-of-record, e.g. 'BSE' or 'NSE'.")
    source_url: str = Field(..., description="Link back to the original filing.")
    fetched_at: datetime = Field(..., description="UTC fetch timestamp.")
    source_hash: str = Field(..., description="Hash of the raw artifact.")
    filing_period: str = Field(..., description="Reporting period, e.g. 'FY2024' or 'Q1FY25'.")


class CartoonNode(BaseModel):
    """A cartoon primitive that money flows into or out of (FR-6.1)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    value: float = Field(..., description="Node magnitude in the spec's unit.")
    role: FlowDirection = FlowDirection.NEUTRAL
    icon: str | None = Field(default=None, description="Named icon for the character/primitive.")


class CartoonFlow(BaseModel):
    """A directed money stream between two nodes (Sankey-style, FR-4.1)."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., description="Source node id.")
    target: str = Field(..., description="Target node id.")
    amount: float = Field(..., ge=0, description="Non-negative magnitude of the stream.")
    direction: FlowDirection = FlowDirection.NEUTRAL
    label: str | None = None


class TableRow(BaseModel):
    """One row of the "Show the numbers" table (FR-6.2)."""

    model_config = ConfigDict(extra="forbid")

    label: str
    value: float
    unit: str


class Accessibility(BaseModel):
    """Text/table equivalents so no meaning is visual-only (A11Y-2, A11Y-3)."""

    model_config = ConfigDict(extra="forbid")

    alt_text: str = Field(..., min_length=1, description="Screen-reader summary of the cartoon.")
    table_caption: str = Field(..., min_length=1)


class Animation(BaseModel):
    """Motion instructions with a mandatory reduced-motion contract (A11Y-5)."""

    model_config = ConfigDict(extra="forbid")

    duration_ms: int = Field(default=1200, ge=0)
    reduced_motion_ok: bool = Field(
        default=True,
        description="True iff a static fallback conveys the same information.",
    )
    sequence: list[str] = Field(
        default_factory=list,
        description="Ordered flow ids to animate; empty means animate all at once.",
    )


class CartoonSpec(BaseModel):
    """The complete, self-describing cartoon payload consumed by the renderer."""

    model_config = ConfigDict(extra="forbid")

    spec_version: str = Field(default=CARTOON_SPEC_VERSION)
    cartoon_type: CartoonType
    title: str
    subtitle: str | None = None
    currency: str = Field(default="INR")
    unit: str = Field(default="INR_CRORE", description="Magnitude unit for all values.")
    entity_name: str
    entity_identifier: str | None = None

    nodes: list[CartoonNode] = Field(default_factory=list)
    flows: list[CartoonFlow] = Field(default_factory=list)
    narrative: list[str] = Field(default_factory=list, description="Plain-language verdicts (UX-2).")
    table: list[TableRow] = Field(default_factory=list)

    provenance: Provenance
    accessibility: Accessibility
    animation: Animation = Field(default_factory=Animation)

    @model_validator(mode="after")
    def _flows_reference_known_nodes(self) -> "CartoonSpec":
        """Structural invariant: every flow endpoint must be a declared node."""
        known = {node.id for node in self.nodes}
        for flow in self.flows:
            missing = {flow.source, flow.target} - known
            if missing:
                raise ValueError(
                    f"flow references unknown node id(s): {sorted(missing)}"
                )
        for flow_id in self.animation.sequence:
            valid = {f"{f.source}->{f.target}" for f in self.flows}
            if flow_id not in valid:
                raise ValueError(f"animation.sequence references unknown flow: {flow_id!r}")
        return self

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize to canonical JSON for the renderer / for regression baselines."""
        return self.model_dump_json(indent=indent)
