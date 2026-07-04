"""The predefined, versioned "CartoonSpec" exchange format.

CartoonSpec is the contract between the analysis backend (§7.2) and the
cartoonization frontend (§7.6). The backend emits a validated CartoonSpec; the
renderer consumes it to draw an accessible, animated cartoon.
"""

from cartoonomics.format.cartoon_spec import (
    CARTOON_SPEC_VERSION,
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

__all__ = [
    "CARTOON_SPEC_VERSION",
    "Accessibility",
    "Animation",
    "CartoonFlow",
    "CartoonNode",
    "CartoonSpec",
    "CartoonType",
    "FlowDirection",
    "Provenance",
    "TableRow",
]
