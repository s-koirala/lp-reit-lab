"""Money/units tests (exact integer-cents arithmetic, CPI deflation)."""

from decimal import Decimal

import pytest

from lp_reit_lab.ingest import money


def test_dollars_to_cents_exact():
    assert money.dollars_to_cents("1234.56") == 123456
    assert money.dollars_to_cents("0.10") == 10


def test_cents_to_dollars_roundtrip():
    assert money.cents_to_dollars(123456) == Decimal("1234.56")


def test_price_per_sqft():
    # $600,000 over 1,500 sqft = $400/sqft
    assert money.price_per_sqft(600_000 * 100, 1500.0) == Decimal("400.00")


def test_price_per_sqft_rejects_nonpositive_sqft():
    with pytest.raises(ValueError):
        money.price_per_sqft(100, 0)


def test_deflate_to_base_period():
    # nominal $100 at CPI 200, base CPI 100 -> real $50
    assert money.deflate(10_000, cpi_period=200, cpi_base=100) == 5_000


def test_deflate_rejects_nonpositive_cpi():
    with pytest.raises(ValueError):
        money.deflate(10_000, cpi_period=0, cpi_base=100)


def test_deflate_rejects_nonpositive_base():
    with pytest.raises(ValueError):
        money.deflate(10_000, cpi_period=200, cpi_base=0)


def test_price_per_sqft_rejects_nan_sqft():
    with pytest.raises(ValueError):
        money.price_per_sqft(100, float("nan"))
