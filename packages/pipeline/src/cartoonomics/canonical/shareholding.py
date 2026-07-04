"""Shareholding pattern over time (screener.in "Shareholding Pattern").

Each row is one period column: the percentage held by each investor category,
the promoter pledge, and the total number of shareholders. Percentages should
add up to ~100 for a complete disclosure; a tolerant validator guards obvious
data errors without rejecting normal rounding.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cartoonomics.canonical.common import ReportingPeriod

_SUM_TOLERANCE = 1.5  # percentage points


class ShareholdingRow(BaseModel):
    """Investor-category breakdown for one period."""

    model_config = ConfigDict(extra="forbid")

    period: ReportingPeriod
    promoters_pct: float | None = Field(default=None, ge=0, le=100)
    fiis_pct: float | None = Field(default=None, ge=0, le=100, description="Foreign institutional investors.")
    diis_pct: float | None = Field(default=None, ge=0, le=100, description="Domestic institutional investors.")
    government_pct: float | None = Field(default=None, ge=0, le=100)
    public_pct: float | None = Field(default=None, ge=0, le=100)
    others_pct: float | None = Field(default=None, ge=0, le=100)
    no_of_shareholders: int | None = Field(default=None, ge=0)
    promoter_pledged_pct: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def _categories_sum_to_100(self) -> "ShareholdingRow":
        """If every main category is disclosed, they must total ~100%."""
        parts = [
            self.promoters_pct,
            self.fiis_pct,
            self.diis_pct,
            self.government_pct,
            self.public_pct,
            self.others_pct,
        ]
        if all(p is not None for p in parts):
            total = sum(parts)  # type: ignore[arg-type]
            if abs(total - 100.0) > _SUM_TOLERANCE:
                raise ValueError(
                    f"shareholding categories sum to {total:.2f}%, expected ~100%"
                )
        return self
