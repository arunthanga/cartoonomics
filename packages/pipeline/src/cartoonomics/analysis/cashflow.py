"""Build a company cashflow CartoonSpec from parsed financials (FR-4.1).

The cashflow cartoon shows the three activity streams (Operating, Investing,
Financing) flowing into a central cash pool, ending in the net change in cash.
Positive activity totals are inflows; negative totals are outflows. Direction is
encoded both by ``FlowDirection`` and by label so it is never colour-only
(A11Y-3).
"""

from __future__ import annotations

from datetime import datetime

from cartoonomics.format import (
    Accessibility,
    Animation,
    CartoonFlow,
    CartoonNode,
    CartoonSpec,
    CartoonType,
    FlowDirection,
    Provenance,
    TableRow,
)
from cartoonomics.parsing import ParsedFinancials

# Keyword buckets used to classify cashflow statement line items.
_ACTIVITY_KEYWORDS = {
    "operating": ("operating",),
    "investing": ("investing",),
    "financing": ("financing",),
}
_NET_KEYWORDS = ("net increase", "net decrease", "net change")


def _classify(label: str) -> str | None:
    text = label.lower()
    if any(k in text for k in _NET_KEYWORDS):
        return "net"
    for bucket, keywords in _ACTIVITY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return bucket
    return None


def _direction(value: float) -> FlowDirection:
    if value > 0:
        return FlowDirection.INFLOW
    if value < 0:
        return FlowDirection.OUTFLOW
    return FlowDirection.NEUTRAL


def _inr(value: float, unit: str) -> str:
    pretty_unit = {"INR_CRORE": "cr", "INR_LAKH": "lakh"}.get(unit, unit)
    return f"₹{value:,.0f} {pretty_unit}"


def build_cashflow_cartoon(
    parsed: ParsedFinancials,
    *,
    source: str,
    source_url: str,
    source_hash: str,
    fetched_at: datetime,
    unit: str = "INR_CRORE",
    entity_identifier: str | None = None,
) -> CartoonSpec:
    """Assemble a validated cashflow :class:`CartoonSpec`."""
    cf_items = [i for i in parsed.items if i.statement == "CF"]
    if not cf_items:
        raise ValueError("no cashflow (CF) line items found to cartoonize")

    activities: dict[str, float] = {"operating": 0.0, "investing": 0.0, "financing": 0.0}
    net_from_filing: float | None = None
    for item in cf_items:
        bucket = _classify(item.label)
        if bucket in activities:
            activities[bucket] += item.value
        elif bucket == "net":
            net_from_filing = item.value

    net_change = net_from_filing if net_from_filing is not None else sum(activities.values())

    icons = {"operating": "gears", "investing": "seedling", "financing": "bank"}
    nodes = [CartoonNode(id="cash", label="Cash Pool", value=abs(net_change), role=FlowDirection.NEUTRAL, icon="coins")]
    flows: list[CartoonFlow] = []
    for name, value in activities.items():
        nodes.append(
            CartoonNode(id=name, label=name.capitalize(), value=abs(value), role=_direction(value), icon=icons[name])
        )
        flows.append(
            CartoonFlow(
                source=name if value >= 0 else "cash",
                target="cash" if value >= 0 else name,
                amount=abs(value),
                direction=_direction(value),
                label=f"{name.capitalize()}: {_inr(abs(value), unit)}",
            )
        )

    nodes.append(
        CartoonNode(id="net", label="Net Change in Cash", value=abs(net_change), role=_direction(net_change), icon="delta")
    )
    flows.append(
        CartoonFlow(
            source="cash" if net_change >= 0 else "net",
            target="net" if net_change >= 0 else "cash",
            amount=abs(net_change),
            direction=_direction(net_change),
            label=f"Net change: {_inr(abs(net_change), unit)}",
        )
    )

    narrative = _narrative(activities, net_change, unit)
    table = [TableRow(label=i.label, value=i.value, unit=i.unit) for i in cf_items]

    alt = (
        f"Cashflow cartoon for {parsed.entity_name} ({parsed.period}). "
        f"Operating {_inr(activities['operating'], unit)}, "
        f"investing {_inr(activities['investing'], unit)}, "
        f"financing {_inr(activities['financing'], unit)}, "
        f"net change {_inr(net_change, unit)}."
    )

    return CartoonSpec(
        cartoon_type=CartoonType.CASHFLOW,
        title=f"{parsed.entity_name} — Cash Flow",
        subtitle=parsed.period,
        unit=unit,
        entity_name=parsed.entity_name,
        entity_identifier=entity_identifier,
        nodes=nodes,
        flows=flows,
        narrative=narrative,
        table=table,
        provenance=Provenance(
            source=source,
            source_url=source_url,
            fetched_at=fetched_at,
            source_hash=source_hash,
            filing_period=parsed.period,
        ),
        accessibility=Accessibility(
            alt_text=alt,
            table_caption=f"Cash flow line items for {parsed.entity_name}, {parsed.period}.",
        ),
        animation=Animation(
            duration_ms=1200,
            reduced_motion_ok=True,
            sequence=[f"{f.source}->{f.target}" for f in flows],
        ),
    )


def _narrative(activities: dict[str, float], net_change: float, unit: str) -> list[str]:
    lines: list[str] = []
    op = activities["operating"]
    if op > 0:
        lines.append(f"The business generated {_inr(op, unit)} from its core operations.")
    elif op < 0:
        lines.append(f"Core operations consumed {_inr(-op, unit)} of cash this period.")

    inv = activities["investing"]
    if inv < 0:
        lines.append(f"It invested {_inr(-inv, unit)} back into the business (outflow).")
    elif inv > 0:
        lines.append(f"It raised {_inr(inv, unit)} by selling investments/assets.")

    fin = activities["financing"]
    if fin < 0:
        lines.append(f"It returned {_inr(-fin, unit)} to lenders/shareholders (financing outflow).")
    elif fin > 0:
        lines.append(f"It raised {_inr(fin, unit)} from financing (debt/equity).")

    verdict = "grew" if net_change > 0 else "shrank" if net_change < 0 else "held steady"
    lines.append(f"Overall, the cash balance {verdict} by {_inr(abs(net_change), unit)}.")
    return lines
