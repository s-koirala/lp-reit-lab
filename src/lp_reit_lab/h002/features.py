"""Pair-level H002 feature assembly — the geometric/permits layer.

Joins each repeat-sale pair to: its attendance-area school under the vintage
in force at EACH sale (design.md §2 point-in-time rule), a geometric
stability indicator (same school at t1 and t2 — redistricted pairs are
excluded from the confirmatory set, §1.2), the nearest boundary segment
ADJACENT TO THE PAIR'S OWN SCHOOL under the t2 vintage (the boundary the unit
"faces"; t2 = the purchase decision being priced), the signed distance to it,
and the renovation flag (§3/§4).

The ISBE quality join (which side of the segment is "top-ISBE", label
stability across the holding interval) attaches downstream via the
RCDTS↔boundary-school crosswalk — a freeze-time artifact
(methodology_isbe-quality-recipe_2026-07-06.md §4); this module deliberately
carries the segment and school keys it needs and nothing about quality, so
the geometric layer can be validated and counted independently.
"""

from __future__ import annotations

import math

import pandas as pd

from .boundaries import BoundaryVintage


def _school_segment_distance(vintage: BoundaryVintage, school: str,
                             latitude: float, longitude: float,
                             ) -> tuple[tuple[str, str] | None, float]:
    """Nearest segment INVOLVING the given school, and its metric distance."""
    best_key, best_d = None, math.inf
    for key in vintage.segment_keys:
        if school not in key:
            continue
        d = vintage.distance_to_segment_m(key, latitude, longitude)
        if d < best_d:
            best_key, best_d = key, d
    return best_key, best_d


def attach_geometry(pairs: pd.DataFrame,
                    vintages: dict[str, BoundaryVintage]) -> pd.DataFrame:
    """Add school labels (per-sale vintage), stability, segment, and distance.

    `pairs` must carry vintage_t1/vintage_t2 (school_year.attach_vintages).
    `vintages` maps SY label -> loaded BoundaryVintage for ONE level. Pairs
    whose vintage is unavailable (pre-SY0607) get null labels and
    `geom_stable=False`.
    """
    school_t1: list[str | None] = []
    school_t2: list[str | None] = []
    segment: list[tuple[str, str] | None] = []
    dist_m: list[float] = []
    for row in pairs.itertuples(index=False):
        lat, lon = row.latitude, row.longitude
        v1 = vintages.get(row.vintage_t1) if row.vintage_t1 else None
        v2 = vintages.get(row.vintage_t2) if row.vintage_t2 else None
        s1 = v1.assign_school(lat, lon) if (v1 and pd.notna(lat)) else None
        s2 = v2.assign_school(lat, lon) if (v2 and pd.notna(lat)) else None
        school_t1.append(s1)
        school_t2.append(s2)
        if v2 and s2:
            seg, d = _school_segment_distance(v2, s2, lat, lon)
        else:
            seg, d = None, math.nan
        segment.append(seg)
        dist_m.append(d if seg else math.nan)
    out = pairs.copy()
    out["school_t1"] = school_t1
    out["school_t2"] = school_t2
    out["geom_stable"] = [
        s1 is not None and s1 == s2 for s1, s2 in zip(school_t1, school_t2, strict=True)
    ]
    out["segment"] = segment
    out["dist_to_boundary_m"] = dist_m
    return out


def buffer_counts(features: pd.DataFrame, bandwidths_m: list[float]) -> pd.DataFrame:
    """Usable-pair counts per candidate bandwidth (the §8 power inputs).

    Usable = geometrically stable, renovation-clean (if the flag column is
    present), inside the buffer. Reported per bandwidth with segment counts
    (G_segment) and mean pairs per segment (m_bar) — the design-effect
    parameters of the power analysis.
    """
    rows = []
    base = features[features["geom_stable"]]
    if "reno_permit_flag" in base.columns:
        base = base[~base["reno_permit_flag"]]
    for bw in bandwidths_m:
        in_buffer = base[base["dist_to_boundary_m"] <= bw]
        n_segments = in_buffer["segment"].nunique()
        rows.append({
            "bandwidth_m": bw,
            "n_pairs": int(len(in_buffer)),
            "g_segment": int(n_segments),
            "m_bar": float(len(in_buffer) / n_segments) if n_segments else math.nan,
        })
    return pd.DataFrame(rows)
