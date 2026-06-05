"""Finance metric tests vs numpy-financial and closed-form benchmarks."""

import numpy_financial as npf
import pytest

from lp_reit_lab.finance import metrics as m


def test_mortgage_payment_matches_numpy_financial():
    loan, rate, years = 300_000.0, 0.06, 30
    expected = -npf.pmt(rate / 12, years * 12, loan)
    assert m.mortgage_payment(loan, rate, years) == pytest.approx(expected, rel=1e-9)


def test_mortgage_payment_zero_rate_is_straight_line():
    assert m.mortgage_payment(120_000, 0.0, 10) == pytest.approx(1000.0)


def test_remaining_balance_endpoints():
    loan, rate, years = 300_000.0, 0.06, 30
    assert m.remaining_balance(loan, rate, years, 0) == pytest.approx(loan)
    assert m.remaining_balance(loan, rate, years, years * 12) == pytest.approx(0.0, abs=1e-6)


def test_remaining_balance_interior_matches_numpy_financial():
    loan, rate, years, month = 300_000.0, 0.06, 30, 84
    pmt = npf.pmt(rate / 12, years * 12, loan)
    expected = -npf.fv(rate / 12, month, pmt, loan)
    assert m.remaining_balance(loan, rate, years, month) == pytest.approx(expected, rel=1e-9)


def test_cap_rate_and_dscr_identities():
    assert m.cap_rate(30_000, 500_000) == pytest.approx(0.06)
    assert m.debt_service_coverage_ratio(30_000, 24_000) == pytest.approx(1.25)


def test_effective_gross_income_applies_vacancy():
    assert m.effective_gross_income(2_000, 0.05) == pytest.approx(2_000 * 12 * 0.95)


def test_break_even_occupancy_definition():
    # (opex + debt service) / gross potential rent
    assert m.break_even_occupancy(12_000, 12_000, 48_000) == pytest.approx(0.5)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        m.cap_rate(1, 0)
    with pytest.raises(ValueError):
        m.effective_gross_income(2000, 1.0)
    with pytest.raises(ValueError):
        m.mortgage_payment(100_000, 0.05, 0)
    with pytest.raises(ValueError):
        m.remaining_balance(100_000, 0.05, 0, 0)
