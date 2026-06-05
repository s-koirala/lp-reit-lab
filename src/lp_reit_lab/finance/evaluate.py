"""High-level property evaluation: single-period metrics + multi-year DCF."""

from __future__ import annotations

from typing import Any

from ..config import Assumptions
from . import cashflow as cf
from . import metrics as m


def evaluate_property(price: float, monthly_rent: float, hoa_monthly: float,
                      a: Assumptions) -> dict[str, Any]:
    """Return a full metric + pro-forma result for one property under assumptions `a`."""
    gpr = m.gross_potential_rent(monthly_rent)
    egi = m.effective_gross_income(monthly_rent, a.vacancy_rate, a.other_income_fraction)
    opex = cf.opex_for_year(price, egi, hoa_monthly, a, 0)
    noi = m.net_operating_income(egi, opex)
    going_in_cap = m.cap_rate(noi, price)

    loan = price * (1.0 - a.down_payment_fraction)
    debt_service = m.annual_debt_service(loan, a.mortgage_rate_annual, a.amortization_years)
    equity = m.cash_invested(price, a.down_payment_fraction, a.closing_cost_fraction)
    annual_cf = m.pre_tax_cash_flow(noi, debt_service)

    proforma = cf.project_proforma(price, monthly_rent, hoa_monthly, a, debt_service)
    rev = cf.reversion(price, monthly_rent, hoa_monthly, a, going_in_cap, loan)

    levered_cfs = [-equity, *proforma["levered_cash_flow"].tolist()]
    levered_cfs[-1] += rev["net_reversion"]
    unlevered_basis = price + price * a.closing_cost_fraction
    unlevered_cfs = [-unlevered_basis, *proforma["noi"].tolist()]
    unlevered_cfs[-1] += rev["sale_price"] - rev["selling_costs"]

    # Equity multiple via the conventional capital-calls method: interim negative
    # cash flows are additional equity in; distributions are positive CFs + net
    # sale proceeds. Always >= 0 (a cash-flow-negative appreciation play can have
    # EM < 1). LP 3BR rentals are frequently cash-flow negative — surface, not hide.
    operating_cfs = proforma["levered_cash_flow"].tolist()
    total_equity_in = equity + sum(-cf for cf in operating_cfs if cf < 0)
    total_distributions = sum(cf for cf in operating_cfs if cf > 0) + max(rev["net_reversion"], 0.0)
    equity_multiple = total_distributions / total_equity_in if total_equity_in > 0 else float("nan")

    return {
        "price": price,
        "monthly_rent": monthly_rent,
        "hoa_monthly": hoa_monthly,
        "gross_potential_rent": gpr,
        "egi": egi,
        "opex": opex,
        "noi": noi,
        "going_in_cap": going_in_cap,
        "cap_rate_spread": going_in_cap - a.treasury_10y,
        "loan": loan,
        "equity_invested": equity,
        "annual_debt_service": debt_service,
        "annual_cash_flow": annual_cf,
        "monthly_cash_flow": annual_cf / m.MONTHS_PER_YEAR,
        "cash_on_cash": m.cash_on_cash(annual_cf, equity),
        "dscr": m.debt_service_coverage_ratio(noi, debt_service),
        "grm": m.gross_rent_multiplier(price, gpr),
        "oer": m.operating_expense_ratio(opex, egi),
        "break_even_occupancy": m.break_even_occupancy(opex, debt_service, gpr),
        "ltv": m.loan_to_value(loan, price),
        "levered_irr": cf.irr(levered_cfs),
        "unlevered_irr": cf.irr(unlevered_cfs),
        "npv": cf.npv(a.discount_rate, levered_cfs),
        "equity_multiple": equity_multiple,
        "total_equity_in": total_equity_in,
        "terminal_basis": rev["terminal_basis"],
        "exit_cap": rev["exit_cap"],
        "sale_price": rev["sale_price"],
        "net_reversion": rev["net_reversion"],
        "proforma": proforma,
    }
