"""Analysis engine (§7.2): metrics + cartoon builders."""

from cartoonomics.analysis.cashflow import build_cashflow_cartoon
from cartoonomics.analysis.metrics import XIRRError, xirr

__all__ = ["build_cashflow_cartoon", "xirr", "XIRRError"]
