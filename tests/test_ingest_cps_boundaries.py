"""CPS boundary connector unit tests (no network): vintage map, canonicalization,
structural validation."""

import json
import re

import pytest

from lp_reit_lab.ingest.config import CPS_BOUNDARY_VINTAGES, CPS_BOUNDARY_WRAPPERS
from lp_reit_lab.ingest.sources import cps_boundaries

_SOCRATA_ID = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$")


def _feature(name: str, ring: list[list[float]]) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {"school_nm": name},
    }


def _collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


_RING_A = [[-87.65, 41.91], [-87.64, 41.91], [-87.64, 41.92], [-87.65, 41.91]]
_RING_B = [[-87.66, 41.93], [-87.65, 41.93], [-87.65, 41.94], [-87.66, 41.93]]


def test_vintage_map_covers_sy0607_through_sy2526_both_levels():
    years = cps_boundaries.school_years()
    assert years[0] == "SY0607" and years[-1] == "SY2526"
    assert len(years) == 20
    for sy in years:
        assert set(CPS_BOUNDARY_VINTAGES[sy]) == {"elementary", "high_school"}


def test_wrappers_cover_exactly_the_legacy_vintages_and_never_overlap_parents():
    assert sorted(CPS_BOUNDARY_WRAPPERS) == cps_boundaries.school_years()[:13]
    parent_ids = {CPS_BOUNDARY_VINTAGES[sy][lv]
                  for sy in CPS_BOUNDARY_VINTAGES for lv in ("elementary", "high_school")}
    wrapper_ids = {CPS_BOUNDARY_WRAPPERS[sy][lv]
                   for sy in CPS_BOUNDARY_WRAPPERS for lv in ("elementary", "high_school")}
    assert not parent_ids & wrapper_ids  # a wrapper id pinned as a parent truncates


def test_sy_start_year():
    assert cps_boundaries.sy_start_year("SY0607") == 2006
    assert cps_boundaries.sy_start_year("SY2526") == 2025


def test_vintage_ids_wellformed_and_unique():
    ids = [CPS_BOUNDARY_VINTAGES[sy][lvl]
           for sy in CPS_BOUNDARY_VINTAGES for lvl in ("elementary", "high_school")]
    assert all(_SOCRATA_ID.match(i) for i in ids)
    assert len(ids) == len(set(ids))  # a copy-paste duplicate would corrupt a vintage


def test_canonical_bytes_invariant_to_feature_order():
    a = _collection([_feature("A", _RING_A), _feature("B", _RING_B)])
    b = _collection([_feature("B", _RING_B), _feature("A", _RING_A)])
    assert cps_boundaries.canonical_geojson_bytes(a) == cps_boundaries.canonical_geojson_bytes(b)


def test_canonical_bytes_parse_back_losslessly():
    gj = _collection([_feature("A", _RING_A)])
    parsed = json.loads(cps_boundaries.canonical_geojson_bytes(gj))
    assert parsed["features"][0]["properties"]["school_nm"] == "A"
    assert parsed["features"][0]["geometry"]["type"] == "Polygon"


def test_validation_accepts_multipolygon():
    gj = _collection([{
        "type": "Feature",
        "geometry": {"type": "MultiPolygon", "coordinates": [[[ _RING_A ]]]},
        "properties": {"SCHOOL_ID": "610001"},
    }])
    cps_boundaries.validate_feature_collection(gj, school_year="SY2425", level="elementary")


_RING_STATE_PLANE = [[1170324.1, 1911620.4], [1170400.0, 1911620.4],
                     [1170400.0, 1911700.0], [1170324.1, 1911620.4]]


@pytest.mark.parametrize("broken, msg", [
    ({"type": "GeometryCollection"}, "not a FeatureCollection"),
    ([{"error": "not found"}], "not a FeatureCollection"),   # non-dict payload
    (_collection([]), "zero features"),
    (_collection([{"type": "Feature", "geometry": {"type": "Point", "coordinates": [0, 0]},
                   "properties": {"school_nm": "A"}}]), "geometry"),
    (_collection([{"type": "Feature",
                   "geometry": {"type": "Polygon", "coordinates": [_RING_A]},
                   "properties": {"objectid": 1}}]), "school-referencing"),
    (_collection([_feature("A", _RING_STATE_PLANE)]), "outside the"),  # projected CRS
])
def test_validation_rejects_structural_breaks(broken, msg):
    with pytest.raises(ValueError, match=msg):
        cps_boundaries.validate_feature_collection(broken, school_year="SY2425",
                                                   level="elementary")


def test_validation_accepts_crs84_member_and_rejects_state_plane_crs():
    ok = _collection([_feature("A", _RING_A)])
    ok["crs"] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}
    cps_boundaries.validate_feature_collection(ok, school_year="SY2425",
                                               level="elementary")
    bad = _collection([_feature("A", _RING_A)])
    bad["crs"] = {"type": "name", "properties": {"name": "EPSG:3435"}}  # IL State Plane E
    with pytest.raises(ValueError, match="non-WGS84"):
        cps_boundaries.validate_feature_collection(bad, school_year="SY2425",
                                                   level="elementary")


def test_resource_id_lookup_raises_on_unknown_vintage():
    with pytest.raises(KeyError):
        cps_boundaries.resource_id_for("SY0506", "elementary")
