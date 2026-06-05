"""Money and units: integer cents, $/sqft, CPI deflation (pure functions).

Convention: amounts carrying fractional precision (e.g. $/sqft, CPI-deflated
values) are handled in **integer cents** — exact, since IEEE-754 floats cannot
represent most decimal cash amounts. Whole-dollar ingested amounts (Cook County
`sale_price`) stay int64 USD and only enter these helpers after an explicit
`dollars_to_cents` conversion. Division-bearing computations use Decimal with
banker's rounding (ROUND_HALF_EVEN) applied once, at the boundary.

These are forward-looking utilities for the analysis layer ($/sqft, real-dollar
series); they are intentionally not yet wired into the raw Cook County panel, whose
`sale_price` is whole-dollar integer USD. Sources: Python `decimal`; Modern
Treasury "floats don't work for storing cents"; BLS CPI math fact sheet.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_EVEN, Decimal

_CENTS = Decimal("0.01")


def dollars_to_cents(dollars: Decimal | str | int) -> int:
    """Exact dollars → integer cents (banker's rounding).

    Pass str/int/Decimal, not float, so binary-float imprecision is never carried
    into money.
    """
    return int((Decimal(str(dollars)) * 100).to_integral_value(rounding=ROUND_HALF_EVEN))


def cents_to_dollars(cents: int) -> Decimal:
    """Integer cents → Decimal dollars, quantized to 2 places."""
    return (Decimal(int(cents)) / 100).quantize(_CENTS, rounding=ROUND_HALF_EVEN)


def price_per_sqft(price_cents: int, sqft: float) -> Decimal:
    """Price per square foot in dollars (Decimal), rounded once at the boundary.

    Rejects non-positive AND non-finite sqft (a NaN sqft — common for CCAO land
    parcels — would otherwise pass `sqft <= 0` and inject NaN into a money field).
    """
    if not (sqft > 0) or not math.isfinite(sqft):
        raise ValueError("sqft must be positive and finite")
    return (Decimal(int(price_cents)) / 100 / Decimal(str(sqft))).quantize(
        _CENTS, rounding=ROUND_HALF_EVEN
    )


def deflate(nominal_cents: int, cpi_period: Decimal | float, cpi_base: Decimal | float) -> int:
    """Nominal cents → real (base-period) cents: real = nominal * (CPI_base / CPI_period).

    Both CPI inputs must be strictly positive (index values; either zero/negative
    breaks the deflator). Use CPI-U NSA (BLS series CUUR0000SA0) for point-in-time
    stability. Source: BLS CPI math fact sheet.
    """
    if Decimal(str(cpi_period)) <= 0:
        raise ValueError("cpi_period must be positive")
    if Decimal(str(cpi_base)) <= 0:
        raise ValueError("cpi_base must be positive")
    real = Decimal(int(nominal_cents)) * Decimal(str(cpi_base)) / Decimal(str(cpi_period))
    return int(real.to_integral_value(rounding=ROUND_HALF_EVEN))
