import pytest
from pydantic import ValidationError

from cartoonomics.format import (
    Accessibility,
    Animation,
    CartoonFlow,
    CartoonNode,
    CartoonSpec,
    CartoonType,
    Provenance,
)
from tests.conftest import FIXED_TS


def _provenance() -> Provenance:
    return Provenance(
        source="BSE",
        source_url="https://example.test/filing",
        fetched_at=FIXED_TS,
        source_hash="deadbeef",
        filing_period="FY2024",
    )


def _spec(**overrides) -> CartoonSpec:
    base = dict(
        cartoon_type=CartoonType.CASHFLOW,
        title="Demo",
        entity_name="Acme",
        nodes=[CartoonNode(id="a", label="A", value=1.0), CartoonNode(id="b", label="B", value=1.0)],
        flows=[CartoonFlow(source="a", target="b", amount=1.0)],
        provenance=_provenance(),
        accessibility=Accessibility(alt_text="alt", table_caption="cap"),
    )
    base.update(overrides)
    return CartoonSpec(**base)


@pytest.mark.unit
def test_valid_spec_roundtrips_json():
    spec = _spec()
    restored = CartoonSpec.model_validate_json(spec.to_json())
    assert restored == spec


@pytest.mark.unit
def test_flow_referencing_unknown_node_rejected():
    with pytest.raises(ValidationError):
        _spec(flows=[CartoonFlow(source="a", target="ghost", amount=1.0)])


@pytest.mark.unit
def test_animation_sequence_must_reference_real_flows():
    with pytest.raises(ValidationError):
        _spec(animation=Animation(sequence=["a->ghost"]))


@pytest.mark.unit
def test_negative_flow_amount_rejected():
    with pytest.raises(ValidationError):
        CartoonFlow(source="a", target="b", amount=-1.0)


@pytest.mark.unit
def test_accessibility_is_mandatory():
    with pytest.raises(ValidationError):
        CartoonSpec(
            cartoon_type=CartoonType.CASHFLOW,
            title="Demo",
            entity_name="Acme",
            provenance=_provenance(),
        )


@pytest.mark.unit
def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        _spec(unexpected="nope")
