"""Typed configuration loader for assumptions and scoring bands.

Values live in config/assumptions.yaml and config/scoring.yaml, each carrying a
cited basis (no magic numbers; CLAUDE.md). This module loads them into frozen
dataclasses so downstream code is not stringly-typed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    """Repository root (two levels above this file: src/lp_reit_lab/config.py)."""
    return Path(__file__).resolve().parents[2]


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


@dataclass(frozen=True)
class Assumptions:
    """Financing and operating assumptions (see config/assumptions.yaml)."""

    mortgage_rate_annual: float
    amortization_years: int
    down_payment_fraction: float
    closing_cost_fraction: float
    vacancy_rate: float
    rent_growth_annual: float
    other_income_fraction: float
    property_tax_rate_of_value: float
    insurance_annual: float
    maintenance_reserve_fraction: float
    property_management_fraction: float
    owner_paid_utilities_monthly: float
    hoa_monthly_default: float
    cost_inflation_annual: float
    hold_years: int
    exit_cap_spread: float
    selling_cost_fraction: float
    appreciation_annual: float
    discount_rate: float
    treasury_10y: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Assumptions:
        fin = data["financing"]
        inc = data["income"]
        opx = data["operating_expenses"]
        ext = data["exit"]
        val = data["valuation"]
        return cls(
            mortgage_rate_annual=float(fin["mortgage_rate_annual"]),
            amortization_years=int(fin["amortization_years"]),
            down_payment_fraction=float(fin["down_payment_fraction"]),
            closing_cost_fraction=float(fin["closing_cost_fraction"]),
            vacancy_rate=float(inc["vacancy_rate"]),
            rent_growth_annual=float(inc["rent_growth_annual"]),
            other_income_fraction=float(inc["other_income_fraction"]),
            property_tax_rate_of_value=float(opx["property_tax_rate_of_value"]),
            insurance_annual=float(opx["insurance_annual"]),
            maintenance_reserve_fraction=float(opx["maintenance_reserve_fraction"]),
            property_management_fraction=float(opx["property_management_fraction"]),
            owner_paid_utilities_monthly=float(opx["owner_paid_utilities_monthly"]),
            hoa_monthly_default=float(opx["hoa_monthly_default"]),
            cost_inflation_annual=float(opx["cost_inflation_annual"]),
            hold_years=int(ext["hold_years"]),
            exit_cap_spread=float(ext["exit_cap_spread"]),
            selling_cost_fraction=float(ext["selling_cost_fraction"]),
            appreciation_annual=float(ext["appreciation_annual"]),
            discount_rate=float(val["discount_rate"]),
            treasury_10y=float(val["treasury_10y"]),
        )

    @classmethod
    def load(cls, path: str | Path | None = None) -> Assumptions:
        path = path or project_root() / "config" / "assumptions.yaml"
        return cls.from_dict(load_yaml(path))


def load_scoring(path: str | Path | None = None) -> dict[str, Any]:
    """Return the scoring-band config (see config/scoring.yaml)."""
    path = path or project_root() / "config" / "scoring.yaml"
    return load_yaml(path)
