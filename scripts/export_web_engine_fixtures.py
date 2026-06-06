#!/usr/bin/env python3
"""Export the web/ TS engine's runtime config + golden-vector parity oracle.

Single source of truth = the Python finance engine (``src/lp_reit_lab/finance``)
driven by ``config/assumptions.yaml`` + ``config/scoring.yaml``. The web TS mirror
(``web/src/lib/engine``) must reproduce ``evaluate_property`` + ``score_property``
exactly; rather than hand-copy the YAML values into TS (drift risk; violates the
no-magic-number directive), this script generates:

  1. ``web/src/lib/engine/config.generated.json`` — assumptions + scoring bands the
     TS app loads at runtime (so both languages use identical inputs);
  2. ``web/src/lib/engine/__fixtures__/golden_vectors.json`` — a self-contained set
     of (price, rent, hoa) cases with the Python engine's expected outputs, which
     the Vitest parity test asserts the TS engine matches within rtol.

IRR (levered/unlevered) is emitted for reference but is NOT part of the parity
contract: ``numpy_financial.irr`` selects among multiple real roots for the
sign-changing, cash-flow-negative streams typical of LP appreciation plays, which
a TS root-finder cannot be guaranteed to match. NPV (fixed discount rate) and the
equity multiple are deterministic and ARE gated. See ``finance/cashflow.py::irr``.

Usage::

    uv run python scripts/export_web_engine_fixtures.py            # write fixtures
    uv run python scripts/export_web_engine_fixtures.py --check    # CI drift gate

``--check`` regenerates in-memory and exits non-zero if the on-disk files differ,
so a change to the YAMLs or the engine without re-exporting fails the build.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lp_reit_lab import scoring  # noqa: E402
from lp_reit_lab.config import Assumptions, load_scoring, project_root  # noqa: E402
from lp_reit_lab.finance import cashflow as cf  # noqa: E402
from lp_reit_lab.finance import metrics as m  # noqa: E402
from lp_reit_lab.finance.evaluate import evaluate_property  # noqa: E402

# Representative (price, monthly_rent, hoa_monthly) cases spanning the decision
# space. Most are cash-flow-negative (monthly cash flow < 0) — the calibrated LP
# appreciation profile — but still NOI-positive, so the reversion uses the exit-cap
# (direct-capitalization) terminal value. The final case is NOI-negative (operating
# income < operating costs), which drives the reversion's appreciation-terminal
# fallback (cashflow.py:105) — included so the parity gate exercises that branch.
# Also: the high-yield GO path from test_evaluate_integration, zero-HOA single-
# family, high-HOA condo, and low/high extremes. Deterministic — no RNG — so the
# oracle is reproducible. Plain literals because they are *test coordinates*, not
# tunable model parameters.
CASES: list[dict[str, float]] = [
    {"price": 250_000.0, "monthly_rent": 3_000.0, "hoa_monthly": 150.0},  # GO path
    {"price": 1_200_000.0, "monthly_rent": 4_500.0, "hoa_monthly": 450.0},  # LP 3BR condo
    {"price": 900_000.0, "monthly_rent": 4_200.0, "hoa_monthly": 0.0},  # SFH, no HOA
    {"price": 1_750_000.0, "monthly_rent": 6_000.0, "hoa_monthly": 700.0},  # high-end condo
    {"price": 650_000.0, "monthly_rent": 3_400.0, "hoa_monthly": 300.0},  # townhouse
    {"price": 2_400_000.0, "monthly_rent": 7_500.0, "hoa_monthly": 600.0},  # luxury SFH
    {"price": 500_000.0, "monthly_rent": 2_600.0, "hoa_monthly": 280.0},  # entry condo
    {"price": 1_050_000.0, "monthly_rent": 5_200.0, "hoa_monthly": 0.0},  # 2-flat
    {"price": 350_000.0, "monthly_rent": 2_900.0, "hoa_monthly": 200.0},  # higher-yield
    {"price": 3_200_000.0, "monthly_rent": 8_000.0, "hoa_monthly": 900.0},  # trophy (deep NO-GO)
    {
        "price": 2_000_000.0,
        "monthly_rent": 1_400.0,
        "hoa_monthly": 1_500.0,
    },  # NOI-negative -> appreciation terminal basis
]


def _carry_monthly(
    price: float, monthly_rent: float, hoa_monthly: float, a: Assumptions
) -> dict[str, float]:
    """Year-0 monthly carrying-cost breakdown for the deal-memo display.

    Vacancy is shown as a line item (foregone rent) for the UI; in the engine it
    is a top-line haircut to EGI. The two reconcile exactly: rent - total_carry
    == monthly_cash_flow == (NOI - annual_debt_service)/12 (other_income = 0).
    Maintenance/management are fractions of EGI (post-vacancy), matching the engine.
    """
    loan = price * (1.0 - a.down_payment_fraction)
    egi_annual = m.effective_gross_income(monthly_rent, a.vacancy_rate, a.other_income_fraction)
    mortgage = m.mortgage_payment(loan, a.mortgage_rate_annual, a.amortization_years)
    tax = price * a.property_tax_rate_of_value / m.MONTHS_PER_YEAR
    insurance = a.insurance_annual / m.MONTHS_PER_YEAR
    hoa = hoa_monthly
    maintenance = egi_annual * a.maintenance_reserve_fraction / m.MONTHS_PER_YEAR
    management = egi_annual * a.property_management_fraction / m.MONTHS_PER_YEAR
    vacancy = monthly_rent * a.vacancy_rate
    total = mortgage + tax + insurance + hoa + maintenance + management + vacancy
    return {
        "mortgage": mortgage,
        "tax": tax,
        "insurance": insurance,
        "hoa": hoa,
        "maintenance": maintenance,
        "management": management,
        "vacancy": vacancy,
        "total": total,
    }


def _clean(obj: Any) -> Any:
    """Recursively JSON-sanitise: non-finite floats -> None; DataFrames already records."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


def build_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    a = Assumptions.load()
    bands = load_scoring()
    assumptions = dataclasses.asdict(a)

    cases = []
    for case in CASES:
        price, rent, hoa = case["price"], case["monthly_rent"], case["hoa_monthly"]
        result = evaluate_property(price, rent, hoa, a)
        result.pop("proforma")  # the year-by-year frame is re-derived in TS and gated separately
        proforma = cf.project_proforma(
            price,
            rent,
            hoa,
            a,
            m.annual_debt_service(
                price * (1 - a.down_payment_fraction), a.mortgage_rate_annual, a.amortization_years
            ),
        ).to_dict(orient="records")
        cases.append(
            {
                "input": case,
                "expected": _clean(result),
                "carry_monthly": _clean(_carry_monthly(price, rent, hoa, a)),
                "proforma": _clean(proforma),
                "score": scoring.score_property(result, bands),
            }
        )

    meta = {
        "_generator": "scripts/export_web_engine_fixtures.py",
        "_source": ["config/assumptions.yaml", "config/scoring.yaml", "src/lp_reit_lab/finance"],
        "_note": "GENERATED — do not edit by hand. Run the generator to refresh.",
    }
    config_payload = {**meta, "assumptions": assumptions, "scoring": bands}
    golden_payload = {**meta, "assumptions": assumptions, "scoring": bands, "cases": cases}
    return config_payload, golden_payload


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main(check: bool) -> int:
    root = project_root()
    config_path = root / "web" / "src" / "lib" / "engine" / "config.generated.json"
    golden_path = root / "web" / "src" / "lib" / "engine" / "__fixtures__" / "golden_vectors.json"
    config_payload, golden_payload = build_payloads()
    targets = [(config_path, _dump(config_payload)), (golden_path, _dump(golden_payload))]

    if check:
        # Byte-exact comparison against the LF bytes we write (files are eol=lf per
        # .gitattributes); avoids any text-mode newline translation.
        drift = [
            p for p, text in targets if not p.exists() or p.read_bytes() != text.encode("utf-8")
        ]
        if drift:
            print("DRIFT: re-run scripts/export_web_engine_fixtures.py — stale:", file=sys.stderr)
            for p in drift:
                print(f"  {p.relative_to(root)}", file=sys.stderr)
            return 1
        print("web engine fixtures up to date.")
        return 0

    for path, text in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))  # LF bytes on every platform
        print(f"wrote {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if on-disk fixtures are stale")
    sys.exit(main(ap.parse_args().check))
