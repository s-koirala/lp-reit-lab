"""One-way sensitivity (tornado) and scenario analysis over assumptions.

The research memo (§7) notes the three load-bearing forward assumptions — rent
growth, exit cap, discount rate — should be the first-class sensitivity levers.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import pandas as pd

from ..config import Assumptions
from .evaluate import evaluate_property


def one_way(price: float, monthly_rent: float, hoa_monthly: float, a: Assumptions,
            variable: str, low: float, high: float,
            metric: str = "levered_irr") -> dict[str, Any]:
    """Vary one assumption field low/high; record the swing in `metric`."""
    base = evaluate_property(price, monthly_rent, hoa_monthly, a)[metric]
    low_out = evaluate_property(
        price, monthly_rent, hoa_monthly, dataclasses.replace(a, **{variable: low})
    )[metric]
    high_out = evaluate_property(
        price, monthly_rent, hoa_monthly, dataclasses.replace(a, **{variable: high})
    )[metric]
    return {
        "variable": variable, "low_input": low, "high_input": high,
        "base": base, "low_output": low_out, "high_output": high_out,
        "swing": abs(high_out - low_out),
    }


def tornado(price: float, monthly_rent: float, hoa_monthly: float, a: Assumptions,
            specs: list[tuple[str, float, float]],
            metric: str = "levered_irr") -> pd.DataFrame:
    """Tornado table: one row per (variable, low, high), sorted by swing desc."""
    rows = [one_way(price, monthly_rent, hoa_monthly, a, var, lo, hi, metric)
            for (var, lo, hi) in specs]
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)


def scenarios(price: float, monthly_rent: float, hoa_monthly: float, a: Assumptions,
              overrides: dict[str, dict[str, float]]) -> dict[str, dict[str, Any]]:
    """Evaluate named scenarios (e.g. base/bull/bear) given per-scenario overrides."""
    return {
        name: evaluate_property(price, monthly_rent, hoa_monthly, dataclasses.replace(a, **ov))
        for name, ov in overrides.items()
    }
