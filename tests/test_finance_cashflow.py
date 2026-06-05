"""DCF / amortization / IRR tests vs numpy-financial and analytical benchmarks."""

import numpy as np
import numpy_financial as npf
import pytest

from lp_reit_lab.config import Assumptions
from lp_reit_lab.finance import cashflow as cf

A = Assumptions.load()


def test_amortization_fully_amortizes():
    sched = cf.amortization_schedule(300_000, 0.06, 30)
    assert sched["balance"].iloc[-1] == pytest.approx(0.0, abs=1e-6)
    assert sched["principal"].sum() == pytest.approx(300_000, rel=1e-9)


def test_irr_matches_numpy_financial():
    cfs = [-100_000, 8_000, 8_000, 8_000, 8_000, 140_000]
    assert cf.irr(cfs) == pytest.approx(float(npf.irr(cfs)), rel=1e-9)


def test_npv_is_zero_at_irr():
    cfs = [-100_000, 8_000, 8_000, 8_000, 8_000, 140_000]
    assert cf.npv(cf.irr(cfs), cfs) == pytest.approx(0.0, abs=1e-3)


def test_irr_nan_without_sign_change():
    assert np.isnan(cf.irr([1.0, 2.0, 3.0]))


def test_proforma_length_matches_hold_period():
    pf = cf.project_proforma(600_000, 4_000, 450, A, 20_000)
    assert len(pf) == A.hold_years
    assert (pf["noi"] > 0).all()


def test_reversion_uses_exit_cap_above_going_in():
    rev = cf.reversion(600_000, 4_000, 450, A, going_in_cap=0.05, loan=450_000)
    assert rev["exit_cap"] == pytest.approx(0.05 + A.exit_cap_spread)
    assert rev["sale_price"] > 0
    assert rev["terminal_basis"] == "exit-cap"


def test_reversion_falls_back_to_appreciation_for_negative_noi():
    # tiny rent + huge HOA -> negative projected NOI -> appreciation terminal value
    rev = cf.reversion(1_000_000, 100, 5_000, A, going_in_cap=0.05, loan=750_000)
    assert rev["terminal_basis"] == "appreciation"
    assert rev["sale_price"] > 0
