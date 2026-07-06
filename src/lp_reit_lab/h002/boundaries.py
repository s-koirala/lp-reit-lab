"""CPS attendance-boundary geometry: side assignment, segments, distances.

Implements the H002 design.md §3 modules `boundary_side` (point-in-polygon
against the vintage in force) and `dist_to_boundary` (running variable), plus
the §5 clustering unit: a BOUNDARY SEGMENT is the shared border between two
adjacent attendance polygons, keyed by the sorted pair of school identifiers.

Coordinates are WGS84 (validated at ingest). Distances use a local
equirectangular projection centred on the Cook County bounding-box midpoint
latitude: one degree of latitude spans ~111.0 km and one degree of longitude
~111.32·cos(φ) km (WGS84 arc lengths); over the sub-5-km scales of a boundary
buffer the flat-earth error is <0.1% (small-angle approximation), far inside
the bandwidth-selection tolerance — no geodesic library needed. Geometry is
transformed ONCE into this metric frame so segment distances are isotropic
and STRtree.nearest is exact.

School-key resolution is vintage-robust: property names drift across the 20
vintages (school_id / schoolid / school_nm / ...), so the key property is
resolved per-file by prioritized pattern rather than a hard-coded name, and
the resolved property name is carried on the loaded vintage.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import shapely
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from ..ingest.config import CookCountyBounds

# WGS84 degree arc lengths (meters/degree): meridian ~111,000 m at ~41.9°N,
# parallel 111,320·cos(φ) m. Source: WGS84 ellipsoid arc formulas.
_M_PER_DEG_LAT = 111_000.0
_M_PER_DEG_LON_EQUATOR = 111_320.0
_B = CookCountyBounds()
# Projection reference latitude = bbox midpoint (derived, not hand-set).
_REF_LAT = (_B.lat_min + _B.lat_max) / 2.0
_M_PER_DEG_LON = _M_PER_DEG_LON_EQUATOR * math.cos(math.radians(_REF_LAT))

# Prioritized property-name patterns for the school identifier.
_KEY_PATTERNS = ("school_id", "schoolid", "school_nm", "school_nam", "schoolname",
                 "school_name")


def to_metric(geom):
    """Project WGS84 lon/lat geometry into the local equirectangular metre frame."""
    return shapely.transform(
        geom, lambda coords: coords * (_M_PER_DEG_LON, _M_PER_DEG_LAT)
    )


def metric_point(latitude: float, longitude: float) -> Point:
    return Point(longitude * _M_PER_DEG_LON, latitude * _M_PER_DEG_LAT)


@dataclass(frozen=True)
class BoundaryVintage:
    """One vintage-level layer: keyed school polygons + adjacency segments.

    Polygons are kept in WGS84 for the point-in-polygon side label; segments
    are kept in the metric frame for exact nearest-segment distances.
    """

    school_year: str
    level: str
    key_property: str
    school_keys: list[str]
    school_geoms: list[object]                       # WGS84, parallel to school_keys
    segment_keys: list[tuple[str, str]]
    segment_geoms_m: list[object]                    # metric frame
    _school_tree: STRtree = field(repr=False)
    _segment_tree_m: STRtree | None = field(repr=False)

    @property
    def segments(self) -> dict[tuple[str, str], object]:
        return dict(zip(self.segment_keys, self.segment_geoms_m, strict=True))

    def assign_school(self, latitude: float, longitude: float) -> str | None:
        """School key whose attendance polygon covers the WGS84 point, else None."""
        point = Point(longitude, latitude)
        for idx in self._school_tree.query(point):
            i = int(idx)
            if self.school_geoms[i].covers(point):
                return self.school_keys[i]
        return None

    def nearest_segment(self, latitude: float, longitude: float,
                        ) -> tuple[tuple[str, str] | None, float]:
        """(segment key, metric distance in m) of the closest adjacency segment."""
        if self._segment_tree_m is None:
            return None, math.inf
        point = metric_point(latitude, longitude)
        idx = int(self._segment_tree_m.nearest(point))
        return self.segment_keys[idx], float(self.segment_geoms_m[idx].distance(point))

    def distance_to_segment_m(self, segment_key: tuple[str, str],
                              latitude: float, longitude: float) -> float:
        """Metric distance from a WGS84 point to one named segment."""
        geom = self.segment_geoms_m[self.segment_keys.index(segment_key)]
        return float(geom.distance(metric_point(latitude, longitude)))


def _resolve_key_property(properties: dict) -> str:
    lower = {str(k).lower(): str(k) for k in properties}
    for pattern in _KEY_PATTERNS:
        if pattern in lower:
            return lower[pattern]
    for low, orig in lower.items():
        if "school" in low:
            return orig
    raise ValueError(f"no school-key property among {sorted(properties)}")


def _adjacency_segments(schools: dict[str, object],
                        ) -> tuple[list[tuple[str, str]], list[object]]:
    """Shared borders between adjacent attendance polygons (the §5 clusters).

    Two attendance areas are adjacent when their boundaries intersect in a
    non-trivial line; point-touches (corner contacts) carry no border to live
    on and are excluded. Segments are returned in the metric frame.
    """
    keys = sorted(schools)
    geoms = [schools[k] for k in keys]
    tree = STRtree(geoms)
    seg_keys: list[tuple[str, str]] = []
    seg_geoms: list[object] = []
    for i, key_i in enumerate(keys):
        boundary_i = geoms[i].boundary
        for idx in tree.query(geoms[i]):
            j = int(idx)
            if j <= i:
                continue
            shared = boundary_i.intersection(geoms[j].boundary)
            if shared.is_empty or shared.length == 0:
                continue
            seg_keys.append((key_i, keys[j]))
            seg_geoms.append(to_metric(shared))
    return seg_keys, seg_geoms


def load_vintage(raw_dir: str | Path, school_year: str, level: str) -> BoundaryVintage:
    """Load one landed vintage GeoJSON into keyed polygons + adjacency segments."""
    path = Path(raw_dir) / f"{level}_{school_year}.geojson"
    geojson = json.loads(path.read_text(encoding="utf-8"))
    features = geojson["features"]
    key_prop = _resolve_key_property(features[0]["properties"])
    merged: dict[str, object] = {}
    for feat in features:
        key = str(feat["properties"].get(key_prop, "")).strip()
        geom = shape(feat["geometry"])
        # A school appearing in multiple features unions into one geometry.
        merged[key] = geom if key not in merged else merged[key].union(geom)
    school_keys = sorted(merged)
    school_geoms = [merged[k] for k in school_keys]
    seg_keys, seg_geoms = _adjacency_segments(merged)
    return BoundaryVintage(
        school_year=school_year, level=level, key_property=key_prop,
        school_keys=school_keys, school_geoms=school_geoms,
        segment_keys=seg_keys, segment_geoms_m=seg_geoms,
        _school_tree=STRtree(school_geoms),
        _segment_tree_m=STRtree(seg_geoms) if seg_geoms else None,
    )
