"""Point-in-time leakage canaries for the H002 join pipeline (design §11.1.5).

Pattern per the pit-canary skill: inject a KNOWN future-knowing input and
assert the pipeline's gates reject it (or that the point-in-time mapping
never selects it). Each canary targets one revision/vintage leakage surface
named in design.md §3: the boundary point-in-polygon join, the ISBE label
window, and the permit flag window.

These tests are load-bearing for the pre-registration freeze: a green run
certifies that no feature computable at time t consumes data published
after t under the registered conventions (Sep-1 boundary in-force rule,
Nov-1 ISBE release floor, strict t1<issue<t2 permit window).
"""

import pandas as pd
import pandera.errors
import pytest

from lp_reit_lab.h002 import permits_flag, school_year
from lp_reit_lab.ingest.schemas import property_sales_schema
from lp_reit_lab.ingest.sources import cps_boundaries, isbe_report_card


def test_canary_boundary_vintage_never_postdates_sale():
    """The vintage in force at a sale must have STARTED on/before the sale date."""
    dates = pd.date_range("2006-09-01", "2026-05-31", freq="17D")
    for d in dates:
        sy = school_year.vintage_in_force(d)
        if sy is None:
            assert d < pd.Timestamp("2006-09-01")
            continue
        start_year = cps_boundaries.sy_start_year(sy)
        # Sep-1 in-force convention: the school year had begun by the sale date
        assert pd.Timestamp(f"{start_year}-09-01") <= d, (d, sy)
        # and the vintage is stale by at most one school year (ends Aug 31 next)
        assert d <= pd.Timestamp(f"{start_year + 1}-08-31"), (d, sy)


def test_canary_future_vintage_injection_is_never_selected():
    """A sale one day before the SY2526 in-force date must map to SY2425."""
    assert school_year.vintage_in_force(pd.Timestamp("2025-08-31")) == "SY2425"
    assert school_year.vintage_in_force(pd.Timestamp("2025-09-01")) == "SY2526"


def test_canary_isbe_year_unpublished_at_snapshot_is_refused():
    """rc year N injected before its Nov-1 release must be rejected as unknowable."""
    # the school year has ENDED (data exists at ISBE) but is not public yet:
    # the exact window the round-1 audit caught as a leak (F-1-2)
    assert 2025 not in isbe_report_card.years_knowable_at("2025-07-15")
    assert 2025 not in isbe_report_card.years_knowable_at("2025-10-30")
    assert 2025 in isbe_report_card.years_knowable_at("2025-11-01")


def test_canary_isbe_knowable_set_is_monotone_in_snapshot():
    """Later snapshots can only ADD knowable years (no retroactive unknowing)."""
    snaps = ["2010-01-01", "2015-06-30", "2020-11-01", "2026-07-06"]
    prev: set[int] = set()
    for s in snaps:
        cur = set(isbe_report_card.years_knowable_at(s))
        assert prev <= cur, s
        prev = cur


def test_canary_permit_on_or_after_second_sale_never_flags():
    """A permit issued ON t2 (or later) is future work relative to the priced
    interval and must not contaminate the pair's constant-quality flag."""
    pair = pd.DataFrame({"pin": ["14324220251001"],
                         "t1": [pd.Timestamp("2010-01-01")],
                         "t2": [pd.Timestamp("2015-06-01")]})
    for issue in ("2015-06-01", "2015-06-02", "2026-01-01"):
        major = pd.DataFrame({
            "permit_type": ["PERMIT - RENOVATION/ALTERATION"],
            "reported_cost": [100_000.0],
            "issue_date": [pd.Timestamp(issue)],
            "pin_list": ["1432422025"],
        })
        flags = permits_flag.flag_pairs(pair, permits_flag.major_permits(major))
        assert not flags.iloc[0], issue


def test_canary_sales_schema_rejects_future_dated_rows():
    """The ingest gate itself: a sale dated after the snapshot cannot enter."""
    future_row = pd.DataFrame({
        "pin": ["14324220251001"], "sale_date": [pd.Timestamp("2026-07-07")],
        "sale_price": pd.array([500_000], dtype="Int64"), "class": ["299"],
        "latitude": [41.91], "longitude": [-87.65],
    })
    with pytest.raises(pandera.errors.SchemaErrors):
        property_sales_schema("2026-07-06").validate(future_row, lazy=True)
