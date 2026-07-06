"""CPS attendance-boundary GeoJSON ingestion — one file per school-year vintage.

Point-in-time discipline (H002 design.md §2): the boundary polygon set REVISES
across school years, so every vintage is pulled as its own dated file and the
point-in-polygon side label is later assigned from the vintage in force on the
sale date — never from the "current" layer. Vintage ids live in
`config.CPS_BOUNDARY_VINTAGES` and are PARENT geo datasets (legacy catalog
entries are `visualization_canvas_map` wrappers whose export truncates — audit
F-1-1); access is the geospatial export endpoint.

Content-to-vintage BINDING is validated, not assumed: before the export is
pulled, the dataset's upstream metadata name must contain both the school-year
token and the level (`verify_vintage_binding`), so a transposed id in the
config map fails loudly instead of silently corrupting two school years of
side labels (audit F-1-3). Geometry is validated against RFC 7946 (WGS84
lon/lat: any legacy `crs` member must name CRS84/EPSG:4326) and every
coordinate must fall inside the Cook County bounding box — a vintage delivered
in a projected CRS (State Plane feet) would otherwise mislabel every
boundary_side assignment for its school year (audit F-1-4).

Serialization is CANONICALIZED for byte-reproducibility: features are sorted
by their own canonical JSON encoding (a total order over distinct features)
and keys are sorted before writing. Hashes are therefore canonicalizer-version-
relative (CPython shortest-round-trip float repr), not upstream-byte-relative.
"""

from __future__ import annotations

import json
from typing import Any

import requests

from ..config import (
    CPS_BOUNDARY_VINTAGES,
    BoundaryLevel,
    ChicagoPortalConfig,
    CookCountyBounds,
)
from ..http_client import get_json

_PORTAL = ChicagoPortalConfig()
_BOUNDS = CookCountyBounds()

LEVELS: tuple[BoundaryLevel, ...] = ("elementary", "high_school")
# GeoJSON geometry types a boundary polygon layer may carry (RFC 7946 §3.1).
_POLYGON_TYPES: frozenset[str] = frozenset({"Polygon", "MultiPolygon"})
# RFC 7946 §4: coordinates are WGS84; a legacy `crs` member (deprecated) is
# acceptable only when it names the equivalent CRS84 / EPSG:4326.
_ACCEPTED_CRS: frozenset[str] = frozenset({
    "urn:ogc:def:crs:OGC:1.3:CRS84",
    "urn:ogc:def:crs:EPSG::4326",
    "EPSG:4326",
})


def school_years() -> list[str]:
    """Configured vintages, ascending (SYxxyy labels sort lexicographically)."""
    return sorted(CPS_BOUNDARY_VINTAGES)


def sy_start_year(school_year: str) -> int:
    """Calendar year in which vintage SYxxyy's school year begins (20xx)."""
    return 2000 + int(school_year[2:4])


def resource_id_for(school_year: str, level: BoundaryLevel) -> str:
    """Vintage dataset id (KeyError on an unconfigured vintage is intentional)."""
    return CPS_BOUNDARY_VINTAGES[school_year][level]


def verify_vintage_binding(session: requests.Session, school_year: str, level: BoundaryLevel,
                           *, app_token: str | None = None) -> dict[str, Any]:
    """Assert the upstream dataset name matches the claimed vintage; return metadata.

    The name check binds content to the config map's label (both the SY digit
    token and the level must appear), so id transposition fails loudly. The
    returned metadata carries `rowsUpdatedAt` — fetched BEFORE the data pull so
    the recorded source_version cannot postdate the bytes it describes.
    """
    resource_id = resource_id_for(school_year, level)
    headers = {"X-App-Token": app_token} if app_token else None
    meta = get_json(session, _PORTAL.metadata_url(resource_id), headers=headers)
    name = str(meta.get("name", "")).lower().replace("_", " ")
    sy_token = school_year[2:]  # "0607"
    level_token = "elementary" if level == "elementary" else "high school"
    if sy_token not in name.replace(" ", "") or level_token not in name:
        raise ValueError(
            f"{level} {school_year} ({resource_id}): upstream name {meta.get('name')!r} "
            "does not match the claimed vintage/level — config map corrupt?"
        )
    return meta


def fetch_boundary_geojson(session: requests.Session, school_year: str, level: BoundaryLevel,
                           *, app_token: str | None = None) -> dict[str, Any]:
    """Pull one vintage's FeatureCollection via the geospatial export endpoint."""
    resource_id = resource_id_for(school_year, level)
    headers = {"X-App-Token": app_token} if app_token else None
    return get_json(session, _PORTAL.geospatial_export_url(resource_id), headers=headers)


# A GeoJSON position is [lon, lat(, alt)] — at least 2 elements (RFC 7946 §3.1.1).
_POSITION_MIN_LEN = 2
# A linear ring closes on itself: 4+ positions (RFC 7946 §3.1.6).
_RING_MIN_POSITIONS = 4


def _walk_coords(node: Any):
    """Yield (lon, lat) leaves of a GeoJSON coordinate array of any nesting depth."""
    if (isinstance(node, list) and len(node) >= _POSITION_MIN_LEN
            and all(isinstance(v, int | float) for v in node[:_POSITION_MIN_LEN])):
        yield node[0], node[1]
        return
    if isinstance(node, list):
        for child in node:
            yield from _walk_coords(child)


def validate_feature_collection(geojson: Any, *, school_year: str, level: str) -> None:
    """Structural + geodetic gate (RFC 7946): FeatureCollection, >=1 feature,
    polygonal, WGS84 coordinates inside the Cook County bbox, non-empty
    properties with at least one school-referencing key.

    Property NAMES vary across vintages (school_nm / school_id / ...), so the
    check requires a key containing "school" rather than a fixed name — a
    structural invariant of the layer family, not a hand-set schema. The bbox
    check is the projected-CRS tripwire: State-Plane feet coordinates (~1e6)
    can never fall inside the lon/lat envelope.
    """
    label = f"{level} {school_year}"
    if not isinstance(geojson, dict) or geojson.get("type") != "FeatureCollection":
        raise ValueError(f"{label}: not a FeatureCollection")
    crs = geojson.get("crs")
    if crs is not None:
        props = crs.get("properties") if isinstance(crs, dict) else None
        crs_name = str((props or {}).get("name", ""))
        if crs_name not in _ACCEPTED_CRS:
            raise ValueError(f"{label}: non-WGS84 crs member {crs_name!r} (RFC 7946 §4)")
    features = geojson.get("features") or []
    if not features:
        raise ValueError(f"{label}: zero features")
    for i, feat in enumerate(features):
        if not isinstance(feat, dict):
            raise ValueError(f"{label}: feature {i} is not an object")
        geom = feat.get("geometry") or {}
        if geom.get("type") not in _POLYGON_TYPES:
            raise ValueError(
                f"{label}: feature {i} geometry is {geom.get('type')!r}, "
                f"expected one of {sorted(_POLYGON_TYPES)}"
            )
        n_positions = 0
        for lon, lat in _walk_coords(geom.get("coordinates", [])):
            n_positions += 1
            if not (_BOUNDS.lon_min <= lon <= _BOUNDS.lon_max
                    and _BOUNDS.lat_min <= lat <= _BOUNDS.lat_max):
                raise ValueError(
                    f"{label}: feature {i} coordinate ({lon}, {lat}) outside the "
                    "Cook County lon/lat envelope — projected CRS or corrupt geometry"
                )
        if n_positions < _RING_MIN_POSITIONS:
            raise ValueError(
                f"{label}: feature {i} has {n_positions} positions, below the "
                f"RFC 7946 §3.1.6 linear-ring minimum of {_RING_MIN_POSITIONS}"
            )
        props = feat.get("properties") or {}
        if not any("school" in str(k).lower() for k in props):
            raise ValueError(f"{label}: feature {i} has no school-referencing property")


def canonical_geojson_bytes(geojson: dict[str, Any]) -> bytes:
    """Canonical serialization: feature order + key order made deterministic.

    Features are sorted by their own compact sorted-key JSON encoding — a total
    order over distinct features that needs no assumption about which property
    names a vintage carries. Compact separators + sorted keys + trailing newline
    make the output byte-stable for content addressing; allow_nan=False keeps
    the file strictly RFC 8259-parseable (bare NaN/Infinity tokens are not JSON).
    """
    body = dict(geojson)
    body["features"] = sorted(
        geojson.get("features", []),
        key=lambda f: json.dumps(f, sort_keys=True, separators=(",", ":"),
                                 allow_nan=False),
    )
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)
    return (text + "\n").encode("utf-8")
