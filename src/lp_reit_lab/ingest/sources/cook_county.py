"""Cook County Assessor Socrata ingestion: geography spine → sales → panel.

Geography is filtered on `chicago_community_area_num` in the Parcel Universe
(`nj4t-kc8j`) — NOT township, which does not coincide with community areas. The
Sales dataset (`wvhk-k5uv`) has no geography, so sales are pulled **by PIN batch**
(server-side `pin in(...)`) for the target PIN set, never county-wide. PINs are
validated to 14 digits before interpolation (SoQL-literal safety). Pulls use a
unique `$order` (`:id`) so offset pagination is a *total* order, and the panel is
sorted before serialization so re-pulls are byte-reproducible. Arms-length sales are
reconstructed with the dataset's legacy filter flags.
"""

from __future__ import annotations

import re
import time
from collections.abc import Sequence
from typing import Any

import pandas as pd
import requests

from ..config import TARGET_COMMUNITY_AREAS, Assessment, CookCountyBounds, SocrataConfig
from ..http_client import get_json

_SOC = SocrataConfig()
_BOUNDS = CookCountyBounds()
_PIN_RE = re.compile(r"^\d{14}$")

# NOTE: _GEO_COLS must NOT include `class` — the Sales select already carries `class`,
# and a duplicate would trigger pandas merge suffixing (class_x/class_y), breaking the
# schema's required `class` column.
_GEO_COLS = [
    "pin", "zip_code", "lat", "lon", "chicago_community_area_num",
    "chicago_community_area_name", "census_tract_geoid",
]
_SALES_SELECT = "pin,year,class,sale_date,sale_price,doc_no"
# Canonical assembled-panel columns (lat/lon renamed to latitude/longitude).
_PANEL_COLS = [
    "pin", "year", "class", "sale_date", "sale_price", "doc_no",
    "zip_code", "latitude", "longitude", "chicago_community_area_num",
    "chicago_community_area_name", "census_tract_geoid",
]

_SALES_BASE_WHERE = (
    f"sale_price > {_BOUNDS.min_arms_length_price} "
    "AND is_multisale = false AND sale_filter_deed_type = false "
    "AND sale_filter_less_than_10k = false AND sale_filter_same_sale_within_365 = false"
)


def _valid_pins(pins: Sequence[str]) -> list[str]:
    """Keep only well-formed 14-digit PINs (SoQL-literal safety; deduped, order-stable)."""
    return [p for p in dict.fromkeys(str(x) for x in pins) if _PIN_RE.match(p)]


def _paged(session: requests.Session, url: str, *, select: str, where: str, order: str,
           app_token: str | None = None, page_size: int = _SOC.page_size,
           max_rows: int | None = None) -> list[dict[str, Any]]:
    """Deterministic offset pagination (`$order` must be a total order); optional cap."""
    headers = {"X-App-Token": app_token} if app_token else None
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        limit = page_size if max_rows is None else min(page_size, max_rows - len(rows))
        if limit <= 0:
            break
        params = {"$select": select, "$where": where, "$order": order,
                  "$limit": limit, "$offset": offset}
        page = get_json(session, url, params=params, headers=headers)
        rows.extend(page)
        if len(page) < limit:
            break
        offset += len(page)
        time.sleep(_SOC.courtesy_sleep_s)
    return rows


def fetch_parcel_universe(session: requests.Session, year: int, *,
                          app_token: str | None = None,
                          max_rows: int | None = None) -> pd.DataFrame:
    """Target-geography parcels (the spine) for a tax year."""
    cas = ",".join(f"'{c}'" for c in TARGET_COMMUNITY_AREAS)
    where = f"year={year} AND chicago_community_area_num in({cas})"
    select = (
        "pin,pin10,year,class,zip_code,lat,lon,chicago_community_area_num,"
        "chicago_community_area_name,township_code,nbhd_code,ward_num,census_tract_geoid"
    )
    rows = _paged(session, _SOC.resource_url(_SOC.parcel_universe_id),
                  select=select, where=where, order=":id",
                  app_token=app_token, max_rows=max_rows)
    return pd.DataFrame.from_records(rows)


def fetch_sales_for_pins(session: requests.Session, pins: Sequence[str],
                         since: str = "2015-01-01", *, app_token: str | None = None,
                         chunk_size: int | None = None,
                         max_rows: int | None = None) -> pd.DataFrame:
    """Arms-length residential sales since `since` for the given PIN set (batched).

    Returns a column-bearing frame even when empty (so downstream `["pin"]` access is
    safe). PINs are sanitized to 14 digits before interpolation into `$where`.
    """
    chunk = chunk_size or _SOC.pin_chunk
    url = _SOC.resource_url(_SOC.parcel_sales_id)
    valid = _valid_pins(pins)
    rows: list[dict[str, Any]] = []
    for start in range(0, len(valid), chunk):
        batch = valid[start:start + chunk]
        pin_list = ",".join(f"'{p}'" for p in batch)
        where = f"sale_date >= '{since}' AND {_SALES_BASE_WHERE} AND pin in({pin_list})"
        remaining = None if max_rows is None else max_rows - len(rows)
        rows.extend(_paged(session, url, select=_SALES_SELECT, where=where, order=":id",
                           app_token=app_token, max_rows=remaining))
        if max_rows is not None and len(rows) >= max_rows:
            break
    return pd.DataFrame(rows, columns=_SALES_SELECT.split(","))


def assemble_panel(universe: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    """Restrict sales to the target PIN set, attach parcel geography, sort deterministically.

    Geography (time-invariant) is joined on PIN only (sale tax-year ≠ geography
    snapshot year). lat/lon are renamed (not duplicated) to latitude/longitude.
    Numerics are coerced (SODA returns numbers as JSON strings); PIN/class stay strings.
    The stable sort makes the serialized CSV byte-reproducible across pulls.
    """
    if sales.empty:
        return pd.DataFrame(columns=_PANEL_COLS)
    geo = universe[[c for c in _GEO_COLS if c in universe.columns]].drop_duplicates("pin")
    target = sales[sales["pin"].isin(geo["pin"])].copy()
    panel = target.merge(geo, on="pin", how="left").rename(
        columns={"lat": "latitude", "lon": "longitude"}
    )
    panel["sale_price"] = pd.to_numeric(panel["sale_price"], errors="coerce").astype("Int64")
    panel["sale_date"] = pd.to_datetime(panel["sale_date"], errors="coerce")
    for col in ("latitude", "longitude"):
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce")
    sort_cols = [c for c in ("pin", "sale_date", "sale_price", "doc_no") if c in panel.columns]
    return panel.sort_values(sort_cols, kind="stable").reset_index(drop=True)


def assessed_to_market(assessed_value: float, assessment: Assessment | None = None) -> float:
    """Implied fair-market value from a Class-2 assessed value: market = AV / LOA.

    A downstream utility (the raw panel carries no assessed value). The equalizer and
    exemptions apply to EAV (the tax bill), NOT to this AV→market back-out; the result
    is the assessor's target market value (mechanical inverse of the level of
    assessment), not an independent appraisal.
    """
    a = assessment or Assessment()
    if a.level_of_assessment <= 0:
        raise ValueError("level_of_assessment must be positive")
    return assessed_value / a.level_of_assessment
