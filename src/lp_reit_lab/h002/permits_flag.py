"""Renovation-contamination flag from Chicago building permits (design.md §3/§4).

A pair is flagged when a MAJOR permit at the pair's parcel is issued strictly
between the two sales (t1 < issue < t2): the renovation then contaminates the
constant-quality assumption and the pair is excluded from the confirmatory
set. Sale-day permits are NOT flagged — a permit issued on the closing date
belongs to the incoming owner's works and does not affect the price already
struck (documented boundary convention; sensitivity at freeze).

Join key: the permits `pin_list` carries 10-digit PIN prefixes (`pin10` =
building), not unit-level PIN14s, so a condo unit inherits every major permit
of its BUILDING. Direction of error: over-flagging -> over-exclusion, which is
CONSERVATIVE for constant-quality (building-wide capital works do affect unit
quality; a neighbouring unit's remodel flags this unit spuriously, but the
cost is sample loss, not contamination). Quantified at freeze.

`major_types` defaults to the FREEZE-PINNED set (design.md §3, resolved
2026-07-06): the three structural-alteration permit types of the City
permit-type taxonomy, with NO reported-cost floor (declared costs are
owner-reported and gameable; a $10k-floor variant is a registered
sensitivity).
"""

from __future__ import annotations

import pandas as pd

from ..ingest.sources.chicago_permits import explode_pin10

# City of Chicago permit-type taxonomy (ydr8-5enu `permit_type` values):
# structural-alteration types that break constant-quality. PINNED at the H002
# freeze (design.md §3, 2026-07-06).
FROZEN_MAJOR_TYPES: frozenset[str] = frozenset({
    "PERMIT - RENOVATION/ALTERATION",
    "PERMIT - NEW CONSTRUCTION",
    "PERMIT - WRECKING/DEMOLITION",
})


def major_permits(permits: pd.DataFrame,
                  major_types: frozenset[str] = FROZEN_MAJOR_TYPES,
                  min_reported_cost: float | None = None) -> pd.DataFrame:
    """Major-permit events exploded to one row per (pin10, issue_date)."""
    keep = permits[permits["permit_type"].isin(sorted(major_types))].copy()
    if min_reported_cost is not None:
        keep = keep[keep["reported_cost"].fillna(0) >= min_reported_cost]
    keep["pin10"] = keep["pin_list"].map(explode_pin10)
    exploded = keep.explode("pin10").dropna(subset=["pin10"])
    return exploded[["pin10", "issue_date", "permit_type", "reported_cost"]]


def flag_pairs(pairs: pd.DataFrame, major: pd.DataFrame) -> pd.Series:
    """Boolean `reno_permit_flag` per pair: any major permit with t1 < issue < t2."""
    out = pd.Series(False, index=pairs.index, name="reno_permit_flag")
    if major.empty or pairs.empty:
        return out
    lookup = pairs[["pin", "t1", "t2"]].copy()
    lookup["pin10"] = lookup["pin"].astype(str).str[:10]
    merged = lookup.reset_index(names="pair_idx").merge(major, on="pin10", how="inner")
    hit = merged[(merged["issue_date"] > merged["t1"])
                 & (merged["issue_date"] < merged["t2"])]
    out.loc[hit["pair_idx"].unique()] = True
    return out
