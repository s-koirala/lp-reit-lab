"""H002 pipeline unit tests (no network): pair construction, vintage calendar,
boundary geometry, renovation flag."""

import json
import math

import numpy as np
import pandas as pd
import pytest

from lp_reit_lab.h002 import boundaries, features, pairs, permits_flag, school_year


def _panel(rows):
    frame = pd.DataFrame(rows, columns=["pin", "class", "sale_date", "sale_price",
                                        "latitude", "longitude",
                                        "chicago_community_area_num"])
    frame["sale_date"] = pd.to_datetime(frame["sale_date"])
    return frame


# Distinct BUILDINGS (pin10 differs): the permit join is building-level, so
# same-building unit pins would legitimately share flags.
_PIN_A = "14324220251001"
_PIN_B = "15012340001002"


def test_build_pairs_consecutive_log_relative():
    panel = _panel([
        (_PIN_A, "299", "2010-01-01", 100_000, 41.92, -87.65, "7"),
        (_PIN_A, "299", "2015-01-01", 150_000, 41.92, -87.65, "7"),
        (_PIN_A, "299", "2020-01-01", 225_000, 41.92, -87.65, "7"),
        (_PIN_B, "299", "2012-06-01", 300_000, 41.93, -87.66, "7"),  # single sale
    ])
    out = pairs.build_pairs(panel)
    assert len(out) == 2  # two consecutive pairs for A, none for B
    assert out["log_relative"].tolist() == pytest.approx(
        [math.log(1.5), math.log(1.5)])
    assert out.loc[0, "holding_days"] == (pd.Timestamp("2015-01-01")
                                          - pd.Timestamp("2010-01-01")).days


def test_build_pairs_drops_nonresidential_and_ambiguous_same_day():
    panel = _panel([
        (_PIN_A, "599", "2010-01-01", 100_000, 41.92, -87.65, "7"),   # non-2xx
        (_PIN_A, "599", "2015-01-01", 130_000, 41.92, -87.65, "7"),
        (_PIN_B, "299", "2010-05-01", 100_000, 41.93, -87.66, "7"),   # same-day dup
        (_PIN_B, "299", "2010-05-01", 900_000, 41.93, -87.66, "7"),
        (_PIN_B, "299", "2018-05-01", 400_000, 41.93, -87.66, "7"),
    ])
    out = pairs.build_pairs(panel)
    assert out.empty  # 599 excluded; B's first date ambiguous -> only one clean sale


def test_build_pairs_flags_class_change_and_min_holding():
    panel = _panel([
        (_PIN_A, "211", "2010-01-01", 100_000, 41.92, -87.65, "7"),
        (_PIN_A, "299", "2010-03-01", 120_000, 41.92, -87.65, "7"),  # 59 days, reclass
    ])
    out = pairs.build_pairs(panel)
    assert len(out) == 1 and not out.loc[0, "same_class"]
    assert pairs.build_pairs(panel, min_holding_days=90).empty


def test_vintage_in_force_september_convention():
    assert school_year.vintage_in_force(pd.Timestamp("2010-09-01")) == "SY1011"
    assert school_year.vintage_in_force(pd.Timestamp("2010-08-31")) == "SY0910"
    assert school_year.vintage_in_force(pd.Timestamp("2005-06-15")) is None  # pre-SY0607
    assert school_year.vintage_in_force(pd.Timestamp("2006-09-01")) == "SY0607"


def test_attach_vintages_columns():
    frame = pd.DataFrame({"t1": [pd.Timestamp("2005-01-01")],
                          "t2": [pd.Timestamp("2012-10-01")]})
    out = school_year.attach_vintages(frame)
    assert out.loc[0, "vintage_t1"] is None
    assert out.loc[0, "vintage_t2"] == "SY1213"


def _square(x0, y0, x1, y1):
    return [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]


def _write_vintage(tmp_path, school_year_label="SY2425", level="elementary"):
    """Two adjacent unit squares sharing the edge lon=-87.65 (real Chicago coords)."""
    features = [
        {"type": "Feature",
         "geometry": {"type": "Polygon",
                      "coordinates": _square(-87.66, 41.90, -87.65, 41.92)},
         "properties": {"school_id": "WEST"}},
        {"type": "Feature",
         "geometry": {"type": "Polygon",
                      "coordinates": _square(-87.65, 41.90, -87.64, 41.92)},
         "properties": {"school_id": "EAST"}},
    ]
    path = tmp_path / f"{level}_{school_year_label}.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}),
                    encoding="utf-8")
    return tmp_path


def test_load_vintage_assignment_and_segment(tmp_path):
    vintage = boundaries.load_vintage(_write_vintage(tmp_path), "SY2425", "elementary")
    assert vintage.key_property == "school_id"
    assert set(vintage.school_keys) == {"WEST", "EAST"}
    assert vintage.assign_school(41.91, -87.655) == "WEST"
    assert vintage.assign_school(41.91, -87.645) == "EAST"
    assert vintage.assign_school(41.99, -87.655) is None      # outside both
    assert list(vintage.segments) == [("EAST", "WEST")]


def test_nearest_segment_metric_distance(tmp_path):
    vintage = boundaries.load_vintage(_write_vintage(tmp_path), "SY2425", "elementary")
    key, dist_m = vintage.nearest_segment(41.91, -87.655)
    assert key == ("EAST", "WEST")
    # 0.005 deg of longitude from the shared edge at ~41.8N: ~111320*cos(41.8)*0.005
    expected = 111_320 * math.cos(math.radians(41.8)) * 0.005
    assert dist_m == pytest.approx(expected, rel=0.01)


def test_flag_pairs_between_sales_only():
    pair_frame = pd.DataFrame({
        "pin": [_PIN_A, _PIN_B],
        "t1": [pd.Timestamp("2010-01-01"), pd.Timestamp("2010-01-01")],
        "t2": [pd.Timestamp("2015-01-01"), pd.Timestamp("2015-01-01")],
    })
    permits = pd.DataFrame({
        "permit_type": ["PERMIT - RENOVATION/ALTERATION",
                        "PERMIT - RENOVATION/ALTERATION",
                        "PERMIT - ELECTRIC WIRING"],
        "reported_cost": [50_000.0, 50_000.0, 5_000.0],
        "issue_date": [pd.Timestamp("2012-06-01"),   # inside A's window
                       pd.Timestamp("2015-01-01"),   # ON B's sale day -> not flagged
                       pd.Timestamp("2012-06-01")],  # minor type -> not flagged
        "pin_list": [_PIN_A[:10], _PIN_B[:10], _PIN_B[:10]],
    })
    major = permits_flag.major_permits(permits)
    flags = permits_flag.flag_pairs(pair_frame, major)
    assert flags.tolist() == [True, False]


def test_attach_geometry_and_buffer_counts(tmp_path):
    raw_dir = _write_vintage(tmp_path, "SY1011", "elementary")
    _write_vintage(tmp_path, "SY1516", "elementary")
    vintages = {sy: boundaries.load_vintage(raw_dir, sy, "elementary")
                for sy in ("SY1011", "SY1516")}
    pair_frame = pd.DataFrame({
        "pin": [_PIN_A, _PIN_B],
        "t1": [pd.Timestamp("2010-10-01"), pd.Timestamp("2010-10-01")],
        "t2": [pd.Timestamp("2015-10-01"), pd.Timestamp("2015-10-01")],
        "latitude": [41.91, 41.99],       # A inside WEST; B outside all polygons
        "longitude": [-87.6501, -87.655],  # A ~8m west of the shared edge
        "vintage_t1": ["SY1011", "SY1011"],
        "vintage_t2": ["SY1516", "SY1516"],
    })
    out = features.attach_geometry(pair_frame, vintages)
    assert out.loc[0, "school_t1"] == out.loc[0, "school_t2"] == "WEST"
    assert bool(out.loc[0, "geom_stable"])
    assert out.loc[0, "segment"] == ("EAST", "WEST")
    assert out.loc[0, "dist_to_boundary_m"] < 20
    assert not bool(out.loc[1, "geom_stable"])   # never assigned
    counts = features.buffer_counts(out, [10.0, 400.0])
    assert counts.loc[0, "n_pairs"] == 1 and counts.loc[1, "n_pairs"] == 1
    assert counts.loc[0, "g_segment"] == 1


def test_major_permits_cost_floor_and_pin_explosion():
    permits = pd.DataFrame({
        "permit_type": ["PERMIT - NEW CONSTRUCTION"] * 2,
        "reported_cost": [np.nan, 1_000_000.0],
        "issue_date": [pd.Timestamp("2012-01-01")] * 2,
        "pin_list": ["1432422025 | 1432422026", "1432422027"],
    })
    no_floor = permits_flag.major_permits(permits)
    assert sorted(no_floor["pin10"]) == ["1432422025", "1432422026", "1432422027"]
    floored = permits_flag.major_permits(permits, min_reported_cost=100_000)
    assert floored["pin10"].tolist() == ["1432422027"]  # NaN cost fails the floor
