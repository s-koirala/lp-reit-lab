"""Multi-year DCF pro forma, reversion, and discounted-return metrics.

Growth conventions (documented, not hidden):
- Gross rent grows at `rent_growth_annual`.
- Property value (for the value-based property tax) grows at `appreciation_annual`.
- Fixed cash costs (insurance, HOA, owner utilities) grow at `cost_inflation_annual`
  (a documented CPI proxy, decoupled from rent growth).
- Property-tax growth is a smooth-annual approximation of Cook County's triennial
  reassessment step (memo §4.5).
- Management and maintenance are fractions of EGI, so they scale with rent.
- Debt service is constant (fixed-rate loan).
Terminal value uses the exit-capitalization method: sale price = next-year NOI /
exit cap rate (exit cap = going-in cap + `exit_cap_spread`).
"""

from __future__ import annotations

import numpy as np
import numpy_financial as npf
import pandas as pd

from ..config import Assumptions
from . import metrics as m


def amortization_schedule(loan: float, annual_rate: float, years: int) -> pd.DataFrame:
    """Monthly amortization schedule: payment, interest, principal, balance."""
    n = years * m.MONTHS_PER_YEAR
    r = annual_rate / m.MONTHS_PER_YEAR
    payment = m.mortgage_payment(loan, annual_rate, years)
    balance = loan
    rows = []
    for month in range(1, n + 1):
        interest = balance * r
        principal = payment - interest
        balance = max(0.0, balance - principal)
        rows.append(
            {"month": month, "payment": payment, "interest": interest,
             "principal": principal, "balance": balance}
        )
    return pd.DataFrame(rows)


def opex_for_year(price: float, egi_year: float, hoa_monthly: float,
                  a: Assumptions, year_index: int) -> float:
    """Operating expenses for a projection year (0-based index).

    Property tax grows with value at `appreciation_annual` — a deliberate smooth-
    annual approximation of Cook County's triennial reassessment step (memo §4.5);
    it understates tax just after a reassessment and overstates between cycles.
    Fixed cash costs grow at `cost_inflation_annual` (CPI proxy).
    """
    value_t = price * (1.0 + a.appreciation_annual) ** year_index
    cost_inflator = (1.0 + a.cost_inflation_annual) ** year_index
    property_tax = value_t * a.property_tax_rate_of_value
    insurance = a.insurance_annual * cost_inflator
    hoa = hoa_monthly * m.MONTHS_PER_YEAR * cost_inflator
    utilities = a.owner_paid_utilities_monthly * m.MONTHS_PER_YEAR * cost_inflator
    management = egi_year * a.property_management_fraction
    maintenance = egi_year * a.maintenance_reserve_fraction
    return property_tax + insurance + hoa + utilities + management + maintenance


def noi_for_year(price: float, monthly_rent: float, hoa_monthly: float,
                 a: Assumptions, year_index: int) -> float:
    """Net operating income for a projection year (0-based index)."""
    rent_t = monthly_rent * (1.0 + a.rent_growth_annual) ** year_index
    egi_t = m.effective_gross_income(rent_t, a.vacancy_rate, a.other_income_fraction)
    return egi_t - opex_for_year(price, egi_t, hoa_monthly, a, year_index)


def project_proforma(price: float, monthly_rent: float, hoa_monthly: float,
                     a: Assumptions, debt_service: float) -> pd.DataFrame:
    """Year-by-year levered pro forma over the hold period."""
    rows = []
    for year in range(1, a.hold_years + 1):
        idx = year - 1
        rent_t = monthly_rent * (1.0 + a.rent_growth_annual) ** idx
        egi_t = m.effective_gross_income(rent_t, a.vacancy_rate, a.other_income_fraction)
        opex_t = opex_for_year(price, egi_t, hoa_monthly, a, idx)
        noi_t = egi_t - opex_t
        rows.append(
            {"year": year, "gross_potential_rent": rent_t * m.MONTHS_PER_YEAR,
             "egi": egi_t, "opex": opex_t, "noi": noi_t,
             "debt_service": debt_service, "levered_cash_flow": noi_t - debt_service}
        )
    return pd.DataFrame(rows)


def reversion(price: float, monthly_rent: float, hoa_monthly: float, a: Assumptions,
              going_in_cap: float, loan: float) -> dict[str, float | str]:
    """Net sale proceeds at end of hold.

    Terminal value uses the exit-cap (direct-capitalization) method when projected
    next-year NOI is positive: sale = NOI_(N+1) / exit cap. Direct capitalization is
    undefined for non-positive NOI, so a cash-flow-negative property (common for LP
    3BR appreciation plays) falls back to an appreciation-based terminal value
    (price grown at `appreciation_annual`). `terminal_basis` records which was used.
    """
    exit_cap = going_in_cap + a.exit_cap_spread
    noi_next = noi_for_year(price, monthly_rent, hoa_monthly, a, a.hold_years)
    if noi_next > 0:
        sale_price = noi_next / exit_cap
        terminal_basis = "exit-cap"
    else:
        sale_price = price * (1.0 + a.appreciation_annual) ** a.hold_years
        terminal_basis = "appreciation"
    selling_costs = sale_price * a.selling_cost_fraction
    loan_balance = m.remaining_balance(
        loan, a.mortgage_rate_annual, a.amortization_years, a.hold_years * m.MONTHS_PER_YEAR
    )
    return {
        "exit_cap": exit_cap, "noi_next": noi_next, "sale_price": sale_price,
        "selling_costs": selling_costs, "loan_balance": loan_balance,
        "terminal_basis": terminal_basis,
        "net_reversion": sale_price - selling_costs - loan_balance,
    }


def irr(cashflows: list[float]) -> float:
    """Internal rate of return via numpy-financial.

    Returns NaN when the stream has no sign change / no real positive root. When the
    stream changes sign more than once and several real roots exist, numpy-financial
    returns the root of smallest magnitude — interpret with care for streams with
    interim capital calls (e.g. cash-flow-negative holds). NPV at a chosen discount
    rate (`npv`) is the more robust ranking statistic in that case.
    """
    arr = np.asarray(cashflows, dtype=float)
    value = npf.irr(arr)
    return float(value) if np.isfinite(value) else float("nan")


def npv(rate: float, cashflows: list[float]) -> float:
    """Net present value; cashflows[0] is the t=0 (undiscounted) outflow."""
    return float(npf.npv(rate, np.asarray(cashflows, dtype=float)))
