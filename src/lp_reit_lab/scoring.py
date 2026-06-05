"""Go/no-go traffic-light scoring from cited bands (config/scoring.yaml).

These are SCREENS, not valuation (research memo §7). All bands come from config,
not literals here, so there are no magic numbers in this module.
"""

from __future__ import annotations

from typing import Any


def light_below(value: float, amber_below: float, red_below: float) -> str:
    """Lower-is-worse metric: red below red_below, amber below amber_below, else green."""
    if value < red_below:
        return "red"
    if value < amber_below:
        return "amber"
    return "green"


def light_above(value: float, amber_above: float, red_above: float) -> str:
    """Higher-is-worse metric: red above red_above, amber above amber_above, else green."""
    if value > red_above:
        return "red"
    if value > amber_above:
        return "amber"
    return "green"


def score_property(metrics: dict[str, Any], scoring: dict[str, Any]) -> dict[str, Any]:
    """Per-metric traffic lights + weighted composite + GO/WATCH/NO-GO verdict."""
    coc = light_below(
        metrics["cash_on_cash"],
        scoring["cash_on_cash"]["amber_below"], scoring["cash_on_cash"]["red_below"],
    )
    dscr = light_below(
        metrics["dscr"], scoring["dscr"]["amber_below"], scoring["dscr"]["red_below"],
    )
    spread = light_below(
        metrics["cap_rate_spread"],
        scoring["cap_rate_spread_over_treasury"]["amber_below"],
        scoring["cap_rate_spread_over_treasury"]["red_below"],
    )
    beo = light_above(
        metrics["break_even_occupancy"],
        scoring["break_even_occupancy"]["amber_above"],
        scoring["break_even_occupancy"]["red_above"],
    )
    lights = {"cash_on_cash": coc, "dscr": dscr,
              "cap_rate_spread": spread, "break_even_occupancy": beo}

    light_scores = scoring["composite"]["light_scores"]
    weights = scoring["composite"]["weights"]
    composite = (
        light_scores[coc] * weights["cash_on_cash"]
        + light_scores[spread] * weights["cap_rate_spread"]
        + light_scores[dscr] * weights["dscr"]
        + light_scores[beo] * weights["break_even_occupancy"]
    )
    if composite >= scoring["composite"]["green_min"]:
        verdict = "GO"
    elif composite >= scoring["composite"]["amber_min"]:
        verdict = "WATCH"
    else:
        verdict = "NO-GO"
    return {"lights": lights, "composite_score": composite, "verdict": verdict}
