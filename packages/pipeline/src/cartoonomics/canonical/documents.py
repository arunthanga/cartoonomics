"""Documents and corporate actions.

* :class:`Document` — the "Documents" list (announcements, annual reports, credit
  ratings, concall transcripts/notes, presentations, earnings releases).
* :class:`CorporateAction` — dividends, splits, bonuses, buybacks, etc.

Both link back to the original source (FR-1.3, CMP-4 attribution).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from cartoonomics.canonical.enums import CorporateActionType, DocumentType


class Document(BaseModel):
    """A single filing/document with a link to the original."""

    model_config = ConfigDict(extra="forbid")

    doc_type: DocumentType
    title: str
    url: str
    published_on: date | None = None
    period_label: str | None = Field(default=None, description="Related period, e.g. 'FY2024'.")


class CorporateAction(BaseModel):
    """A dividend/split/bonus/buyback/rights/AGM event."""

    model_config = ConfigDict(extra="forbid")

    action_type: CorporateActionType
    ex_date: date | None = None
    description: str = Field(default="", description="Human-readable detail, e.g. 'Dividend ₹5/share'.")
    value: float | None = Field(default=None, description="Ratio or amount where applicable.")
