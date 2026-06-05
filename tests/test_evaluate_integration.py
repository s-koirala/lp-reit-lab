"""Integration: evaluate + score a synthetic property end to end."""

import math

import pytest

from lp_reit_lab import scoring
from lp_reit_lab.config import Assumptions, load_scoring
from lp_reit_lab.finance.evaluate import evaluate_property
from lp_reit_lab.synthetic import generate_listings


def test_evaluate_and_score_runs_on_synthetic():
    assumptions = Assumptions.load()
    bands = load_scoring()
    row = generate_listings(20, seed=5).iloc[0]

    result = evaluate_property(
        float(row["price"]), float(row["est_monthly_rent"]), float(row["hoa_monthly"]),
        assumptions,
    )
    # NOI identity and finite/structured outputs
    assert result["noi"] == result["egi"] - result["opex"]
    assert result["dscr"] > 0
    assert result["equity_multiple"] >= 0
    assert math.isfinite(result["levered_irr"]) or math.isnan(result["levered_irr"])
    assert len(result["proforma"]) == assumptions.hold_years

    verdict = scoring.score_property(result, bands)
    assert verdict["verdict"] in {"GO", "WATCH", "NO-GO"}
    assert 0.0 <= verdict["composite_score"] <= 1.0


def test_high_yield_property_scores_go_end_to_end():
    # Low price + strong rent + low HOA -> high cap/CoC/DSCR -> GO. Exercises the
    # green path the synthetic universe never reaches (see synthetic.py docstring).
    a = Assumptions.load()
    bands = load_scoring()
    res = evaluate_property(250_000.0, 3_000.0, 150.0, a)
    verdict = scoring.score_property(res, bands)
    assert verdict["verdict"] == "GO"
    assert verdict["composite_score"] == pytest.approx(1.0)


def test_synthetic_universe_is_mostly_no_go():
    # Calibration intent (memo §9): LP is appreciation-led / sub-1%-rule, so the
    # synthetic universe is deliberately cash-flow-negative and mostly NO-GO.
    a = Assumptions.load()
    bands = load_scoring()
    df = generate_listings(200, seed=11)
    verdicts = [
        scoring.score_property(
            evaluate_property(float(r.price), float(r.est_monthly_rent),
                              float(r.hoa_monthly), a),
            bands,
        )["verdict"]
        for r in df.itertuples(index=False)
    ]
    assert verdicts.count("NO-GO") / len(verdicts) > 0.8
