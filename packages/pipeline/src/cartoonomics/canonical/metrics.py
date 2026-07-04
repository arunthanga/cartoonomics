"""Derived, comparison-ready metrics (requirements §13 ``Metric``, §7.2).

Every computed value records its inputs, formula version, and timestamp so it is
reproducible and auditable (FR-2.6). When a source lacks the data needed, the
metric degrades to ``insufficient_data=True`` rather than a misleading number
(FR-2.7).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cartoonomics.canonical.common import SourceRef
from cartoonomics.canonical.enums import MetricName


class ComputedMetric(BaseModel):
    """A single reproducible derived metric."""

    model_config = ConfigDict(extra="forbid")

    name: MetricName
    value: float | None = None
    unit: str | None = None
    formula_version: str = Field(..., description="Versioned formula id for reproducibility.")
    computed_at: datetime
    inputs: dict[str, float] = Field(default_factory=dict)
    source: SourceRef | None = None
    insufficient_data: bool = Field(default=False, description="True iff inputs were inadequate (FR-2.7).")

    @model_validator(mode="after")
    def _value_or_insufficient(self) -> "ComputedMetric":
        """A metric must either carry a value or declare insufficient data."""
        if self.value is None and not self.insufficient_data:
            raise ValueError("metric has no value; set insufficient_data=True to flag a gap")
        return self
