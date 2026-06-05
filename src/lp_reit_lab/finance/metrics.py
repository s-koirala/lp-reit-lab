"""Single-period income-property metrics (pure functions).

All definitions per docs/research_notes/research_market-scoping_2026-06-05.md §7.
"""

from __future__ import annotations

MONTHS_PER_YEAR = 12


def mortgage_payment(loan: float, annual_rate: float, years: int) -> float:
    """Fixed-rate fully-amortizing monthly payment (standard annuity formula).

    M = P * r(1+r)^n / ((1+r)^n - 1), with r the monthly rate and n the number
    of monthly payments. Handles the zero-rate edge case (straight-line).
    """
    if years <= 0:
        raise ValueError("years must be positive")
    if loan < 0:
        raise ValueError("loan must be non-negative")
    n = years * MONTHS_PER_YEAR
    r = annual_rate / MONTHS_PER_YEAR
    if r == 0:
        return loan / n
    factor = (1.0 + r) ** n
    return loan * r * factor / (factor - 1.0)


def remaining_balance(loan: float, annual_rate: float, years: int, months_elapsed: int) -> float:
    """Outstanding principal after `months_elapsed` payments on a fixed loan."""
    if years <= 0:
        raise ValueError("years must be positive")
    if loan < 0:
        raise ValueError("loan must be non-negative")
    n = years * MONTHS_PER_YEAR
    k = max(0, min(months_elapsed, n))
    r = annual_rate / MONTHS_PER_YEAR
    if r == 0:
        return loan * (1.0 - k / n)
    factor_n = (1.0 + r) ** n
    factor_k = (1.0 + r) ** k
    return loan * (factor_n - factor_k) / (factor_n - 1.0)


def annual_debt_service(loan: float, annual_rate: float, years: int) -> float:
    """Total annual debt service (12 monthly payments)."""
    return mortgage_payment(loan, annual_rate, years) * MONTHS_PER_YEAR


def gross_potential_rent(monthly_rent: float) -> float:
    """Annual gross potential rent at full occupancy."""
    return monthly_rent * MONTHS_PER_YEAR


def effective_gross_income(
    monthly_rent: float, vacancy_rate: float, other_income_fraction: float = 0.0
) -> float:
    """EGI = gross potential rent net of vacancy, plus other income."""
    if not 0.0 <= vacancy_rate < 1.0:
        raise ValueError("vacancy_rate must be in [0, 1)")
    gpr = gross_potential_rent(monthly_rent)
    return gpr * (1.0 - vacancy_rate) + gpr * other_income_fraction


def operating_expenses(
    price: float,
    egi: float,
    hoa_monthly: float,
    *,
    property_tax_rate_of_value: float,
    insurance_annual: float,
    maintenance_reserve_fraction: float,
    property_management_fraction: float,
    owner_paid_utilities_monthly: float = 0.0,
) -> float:
    """Annual operating expenses.

    Excludes debt service, capex above reserves, income tax, and depreciation
    (Geltner et al.). Property tax is value-based; management and maintenance
    reserves are fractions of EGI; HOA/insurance/utilities are fixed dollar items.
    The caller owns deduplication: HOA and owner_paid_utilities must be mutually
    exclusive of services already bundled in the HOA (e.g. water).
    """
    property_tax = price * property_tax_rate_of_value
    hoa = hoa_monthly * MONTHS_PER_YEAR
    utilities = owner_paid_utilities_monthly * MONTHS_PER_YEAR
    management = egi * property_management_fraction
    maintenance = egi * maintenance_reserve_fraction
    return property_tax + insurance_annual + hoa + utilities + management + maintenance


def net_operating_income(egi: float, opex: float) -> float:
    """NOI = effective gross income - operating expenses."""
    return egi - opex


def cap_rate(noi: float, value: float) -> float:
    """Capitalization rate = NOI / value (going-in uses purchase price)."""
    if value <= 0:
        raise ValueError("value must be positive")
    return noi / value


def cash_invested(price: float, down_payment_fraction: float,
                  closing_cost_fraction: float) -> float:
    """Total equity in: down payment + closing costs.

    v0 models no acquisition rehab capex (synthetic data has no rehab field); add a
    rehab term here AND to the unlevered basis in evaluate_property together when
    real listings carry renovation estimates.
    """
    return price * down_payment_fraction + price * closing_cost_fraction


def pre_tax_cash_flow(noi: float, debt_service: float) -> float:
    """Before-tax cash flow = NOI - annual debt service."""
    return noi - debt_service


def cash_on_cash(annual_cash_flow: float, equity_invested: float) -> float:
    """Cash-on-cash = before-tax annual cash flow / total equity invested."""
    if equity_invested <= 0:
        raise ValueError("equity_invested must be positive")
    return annual_cash_flow / equity_invested


def debt_service_coverage_ratio(noi: float, debt_service: float) -> float:
    """DSCR = NOI / annual debt service. <1 means income cannot cover the loan."""
    if debt_service <= 0:
        raise ValueError("debt_service must be positive")
    return noi / debt_service


def gross_rent_multiplier(price: float, gross_potential_rent_annual: float) -> float:
    """GRM = price / annual gross potential rent."""
    if gross_potential_rent_annual <= 0:
        raise ValueError("gross_potential_rent_annual must be positive")
    return price / gross_potential_rent_annual


def operating_expense_ratio(opex: float, egi: float) -> float:
    """OER = operating expenses / effective gross income."""
    if egi <= 0:
        raise ValueError("egi must be positive")
    return opex / egi


def break_even_occupancy(opex: float, debt_service: float,
                         gross_potential_rent_annual: float) -> float:
    """Break-even occupancy = (opex + debt service) / gross potential rent.

    The minimum physical occupancy needed to cover all cash outflows.
    """
    if gross_potential_rent_annual <= 0:
        raise ValueError("gross_potential_rent_annual must be positive")
    return (opex + debt_service) / gross_potential_rent_annual


def loan_to_value(loan: float, value: float) -> float:
    """LTV = loan / value."""
    if value <= 0:
        raise ValueError("value must be positive")
    return loan / value
