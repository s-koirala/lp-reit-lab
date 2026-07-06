"""Repeat-sale pair construction (BMN 1963 §; H002 design.md §4).

A pair is two CONSECUTIVE arms-length sales of the same 14-digit PIN; the
outcome is the log price relative y = log(p2) - log(p1). Residential filter:
CCAO major class 2 (codes 200-299; 299 = residential condominium) — the class
digit taxonomy per the CCAO class dictionary (ccao-data code & docs); all
non-2xx classes are excluded per design §2 ("non-residential CCAO classes
excluded").

Constant-quality hygiene handled HERE: (a) same-day multi-price sales of one
PIN are ambiguous deed events — every sale on that (pin, date) is dropped
before pairing; (b) pairs whose two sales carry different CCAO classes are
flagged (`same_class=False`) — a reclassification (e.g. condo conversion)
breaks the same-unit assumption and is excluded from the confirmatory set at
analysis time. The minimum-holding-period filter is a PARAMETER with no
default here: its value is data-driven and pinned at freeze (design §4
`# TBD-at-freeze`), so nothing in this module hand-sets it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_RESIDENTIAL_CLASS_PREFIX = "2"  # CCAO major class 2 = residential (see module doc)

PAIR_COLUMNS = [
    "pin", "t1", "t2", "p1", "p2", "log_relative", "holding_days",
    "class1", "class2", "same_class", "latitude", "longitude",
    "chicago_community_area_num",
]


def residential_sales(panel: pd.DataFrame) -> pd.DataFrame:
    """CCAO major-class-2 rows of the ingested sales panel."""
    cls = panel["class"].astype(str).str.strip()
    return panel[cls.str.startswith(_RESIDENTIAL_CLASS_PREFIX)].copy()


def build_pairs(panel: pd.DataFrame,
                min_holding_days: int | None = None) -> pd.DataFrame:
    """Consecutive same-PIN sale pairs with the log price relative.

    `min_holding_days` is the freeze-pinned flip screen (design §4); None (the
    draft default) applies no filter so the freeze step can CHOOSE it from the
    observed inter-sale-interval distribution rather than inherit a hand-set
    value.
    """
    sales = residential_sales(panel)
    sales = sales.dropna(subset=["sale_date", "sale_price"])

    # (a) ambiguous same-day deed events: drop every sale on a (pin, date)
    # that carries more than one price row.
    dup_key = sales.duplicated(subset=["pin", "sale_date"], keep=False)
    sales = sales[~dup_key]

    sales = sales.sort_values(["pin", "sale_date"], kind="stable")
    prev = sales.groupby("pin").shift(1)
    have_prev = prev["sale_date"].notna()

    pairs = pd.DataFrame({
        "pin": sales["pin"],
        "t1": prev["sale_date"],
        "t2": sales["sale_date"],
        "p1": prev["sale_price"].astype("Float64"),
        "p2": sales["sale_price"].astype("Float64"),
        "class1": prev["class"],
        "class2": sales["class"],
        "latitude": sales["latitude"],
        "longitude": sales["longitude"],
        "chicago_community_area_num": sales["chicago_community_area_num"],
    })[have_prev]

    pairs["log_relative"] = np.log(pairs["p2"].astype(float)) - np.log(pairs["p1"].astype(float))
    pairs["holding_days"] = (pairs["t2"] - pairs["t1"]).dt.days
    pairs["same_class"] = (pairs["class1"].astype(str).str.strip()
                           == pairs["class2"].astype(str).str.strip())
    if min_holding_days is not None:
        pairs = pairs[pairs["holding_days"] >= min_holding_days]
    return pairs[PAIR_COLUMNS].reset_index(drop=True)
