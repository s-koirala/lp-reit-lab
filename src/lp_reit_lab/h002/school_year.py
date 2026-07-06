"""Sale-date -> CPS school-year vintage in force (H002 design.md §2 roll-handling).

REGISTERED CONVENTION: attendance boundaries for school year Y-(Y+1) are in
force from September 1 of Y through August 31 of Y+1. CPS first days of school
fall in late August/early September (post-Labor-Day historically, late August
in recent years), and boundary layers publish ahead of the fall term; Sep 1 is
the fixed convention date, with the Aug-31/Sep-1 edge registered as a
freeze-time sensitivity rather than tuned. Sales before the first available
vintage (SY0607) return None — they cannot be side-labelled point-in-time.
"""

from __future__ import annotations

import pandas as pd

from ..ingest.sources.cps_boundaries import school_years

_SY_START_MONTH = 9  # September 1 convention (module docstring)


def vintage_in_force(sale_date: pd.Timestamp) -> str | None:
    """SYxxyy label whose boundary set governs `sale_date`, or None if pre-SY0607."""
    ts = pd.Timestamp(sale_date)
    start_year = ts.year if ts.month >= _SY_START_MONTH else ts.year - 1
    label = f"SY{start_year % 100:02d}{(start_year + 1) % 100:02d}"
    return label if label in school_years() else None


def attach_vintages(pairs: pd.DataFrame) -> pd.DataFrame:
    """Add the boundary vintage in force at each sale of every pair.

    `vintage_t1`/`vintage_t2` drive the point-in-polygon side labels; a pair
    with EITHER vintage missing predates boundary coverage and is excluded
    from the confirmatory set at analysis time (design §2 coverage floor).
    """
    out = pairs.copy()
    out["vintage_t1"] = out["t1"].map(vintage_in_force)
    out["vintage_t2"] = out["t2"].map(vintage_in_force)
    return out
