"""Seeded SYNTHETIC listing generator for UI scaffolding.

NOT REAL LISTINGS. Calibrated to published Lincoln Park / North Side aggregates
(research memo §5) so the v0 screener/report look realistic. Deterministic given
a seed; regenerate via scripts/generate_synthetic.py. Real-data ingestion
(Cook County / Census / MLS) replaces this module — see research memo §9.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
import pandas as pd

SYNTHETIC_NOTICE = (
    "SYNTHETIC DATA — not real listings. Calibrated to published Lincoln Park / "
    "North Side aggregates for UI scaffolding only (research memo §5)."
)

# Research memo §4.5: pre-1980 condo buildings see special assessments more often.
_SPECIAL_ASSESSMENT_VINTAGE_YEAR = 1980

# Per-neighborhood calibration anchors (research memo §5).
class _Hood(NamedTuple):
    psf: float
    rent_psf: float
    hoa: float
    weight: float
    lat: float
    lon: float


_NEIGHBORHOODS: dict[str, _Hood] = {
    #               sale $/sqft, rent $/sqft/mo, HOA $/mo, share, lat, lon
    "Lincoln Park": _Hood(462, 3.0, 450, 0.42, 41.9214, -87.6513),
    "Lake View": _Hood(381, 2.6, 400, 0.30, 41.9400, -87.6530),
    "Old Town": _Hood(500, 3.1, 550, 0.10, 41.9100, -87.6360),
    "DePaul": _Hood(470, 3.0, 420, 0.10, 41.9240, -87.6560),
    "RANCH Triangle": _Hood(520, 3.2, 500, 0.08, 41.9170, -87.6520),
}

# Central sqft by bedroom count (lognormal spread applied around these).
_SQFT_BY_BEDS = {2: 1100, 3: 1550, 4: 2100}


def generate_listings(n: int = 150, seed: int = 20260605) -> pd.DataFrame:
    """Return `n` synthetic candidate listings (deterministic given `seed`).

    Spread parameters (lognormal sigma, gamma shapes) are chosen for plausible
    visual dispersion only; this is synthetic scaffolding, not an estimate.
    """
    rng = np.random.default_rng(seed)
    names = list(_NEIGHBORHOODS)
    weights = np.array([_NEIGHBORHOODS[k].weight for k in names], dtype=float)
    weights /= weights.sum()
    chosen = rng.choice(names, size=n, p=weights)
    beds = rng.choice([2, 3, 4], size=n, p=[0.25, 0.60, 0.15])  # 3BR-focused thesis

    rows = []
    for i in range(n):
        hood = _NEIGHBORHOODS[chosen[i]]
        bed = int(beds[i])
        sqft = float(rng.lognormal(mean=np.log(_SQFT_BY_BEDS[bed]), sigma=0.18))
        psf = hood.psf * float(rng.lognormal(mean=0.0, sigma=0.12))
        rent = sqft * hood.rent_psf * float(rng.lognormal(mean=0.0, sigma=0.12))
        hoa = max(150.0, hood.hoa * float(rng.lognormal(mean=0.0, sigma=0.25)))
        year_built = int(rng.integers(1900, 2025))
        rows.append({
            "property_id": f"SYN-{i + 1:04d}",
            "neighborhood": chosen[i],
            "beds": bed,
            "baths": int(np.clip(round(rng.normal(bed - 0.5, 0.6)), 1, 4)),
            "sqft": round(sqft),
            "year_built": year_built,
            "price": float(round(sqft * psf, -3)),
            "hoa_monthly": round(hoa),
            "est_monthly_rent": float(round(rent, -1)),
            "days_on_market": int(np.clip(rng.gamma(shape=4.0, scale=12.0), 3, 365)),
            "latitude": round(hood.lat + rng.normal(0, 0.006), 6),
            "longitude": round(hood.lon + rng.normal(0, 0.006), 6),
            "walk_index": round(float(np.clip(rng.normal(16, 2.0), 1, 20)), 1),
            "transit_distance_m": int(np.clip(rng.gamma(3.0, 180.0), 80, 2000)),
            "school_rating": int(np.clip(round(rng.normal(7, 1.6)), 1, 10)),
            "pre_1980_assessment_risk": year_built < _SPECIAL_ASSESSMENT_VINTAGE_YEAR,
            "synthetic": True,
        })
    return pd.DataFrame(rows)
