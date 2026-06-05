"""Traffic-light scoring tests."""

import pytest

from lp_reit_lab import scoring
from lp_reit_lab.config import load_scoring

S = load_scoring()


def test_light_below_bands():
    assert scoring.light_below(0.10, 0.08, 0.04) == "green"
    assert scoring.light_below(0.06, 0.08, 0.04) == "amber"
    assert scoring.light_below(0.02, 0.08, 0.04) == "red"


def test_light_above_bands():
    assert scoring.light_above(0.80, 0.85, 0.90) == "green"
    assert scoring.light_above(0.88, 0.85, 0.90) == "amber"
    assert scoring.light_above(0.95, 0.85, 0.90) == "red"


def test_strong_property_scores_go():
    metrics = {"cash_on_cash": 0.12, "dscr": 1.5,
               "cap_rate_spread": 0.03, "break_even_occupancy": 0.70}
    res = scoring.score_property(metrics, S)
    assert res["verdict"] == "GO"
    assert res["composite_score"] == pytest.approx(1.0)


def test_weak_property_scores_no_go():
    metrics = {"cash_on_cash": 0.0, "dscr": 0.8,
               "cap_rate_spread": 0.0, "break_even_occupancy": 0.95}
    res = scoring.score_property(metrics, S)
    assert res["verdict"] == "NO-GO"
    assert res["composite_score"] == pytest.approx(0.0)


def test_mixed_property_scores_watch():
    # two greens (CoC, cap-spread) + two reds (DSCR, break-even) -> composite 0.55
    metrics = {"cash_on_cash": 0.10, "dscr": 0.8,
               "cap_rate_spread": 0.03, "break_even_occupancy": 0.95}
    res = scoring.score_property(metrics, S)
    assert res["verdict"] == "WATCH"
    assert res["composite_score"] == pytest.approx(0.55)
