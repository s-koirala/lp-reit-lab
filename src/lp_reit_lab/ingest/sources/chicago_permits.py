"""Chicago building-permits ingestion (`ydr8-5enu`) for the H002 renovation flag.

Pulls permits between `config.PERMITS_EPOCH` (2006-01-01; probed coverage min
2006-01-03) and the snapshot date, in TWO arms: (a) rows labelled with a target
community area (6/7/8), and (b) rows whose `community_area` is NULL (upstream
geocoding gaps) but whose lat/lon falls inside the Cook County bbox — dropping
arm (b) would silently under-flag renovations at target parcels and let
renovated pairs contaminate the constant-quality sample (audit F-1-5); the
definitive target-area membership comes from the parcel join at analysis time.

The pull EXCLUDES all `contact_*` columns (owner/contractor personal names) by
construction — see `config.PERMIT_SELECT_COLS` — because the H002
`reno_permit_flag` (design.md §3) needs only dates, permit type, reported cost,
and the parcel key. `pin_list` carries ' | '-joined 10-digit PIN prefixes
(CCAO `pin10`; probed live 2026-07-06 — pipe-separated, single-PIN cells are
exactly 10 digits), the permit->parcel join key; `explode_pin10` normalizes it.

The snapshot upper bound on `issue_date` is enforced server-side in `$where`
AND re-validated by the pandera gate (schemas.building_permits_schema) — a
no-look-ahead guarantee by validation, not convention.
"""

from __future__ import annotations

import re

import pandas as pd
import requests

from ..config import (
    PERMIT_SELECT_COLS,
    PERMITS_EPOCH,
    TARGET_COMMUNITY_AREAS,
    ChicagoPortalConfig,
    CookCountyBounds,
)
from ..socrata import paged

_PORTAL = ChicagoPortalConfig()
_BOUNDS = CookCountyBounds()
# One pin10 token: exactly 10 digits, not embedded in a longer digit run.
_PIN10_TOKEN_RE = re.compile(r"^\d{10}$")
_PIN14_TOKEN_RE = re.compile(r"^\d{14}$")
_SPLIT_RE = re.compile(r"[|;,\s]+")

_PANEL_COLS = list(PERMIT_SELECT_COLS)


def permit_where_clauses(since: str, snapshot: str) -> list[str]:
    """The two SoQL arms of a permits pull (CA-labelled + null-CA-in-bbox)."""
    window = f"issue_date >= '{since}' AND issue_date <= '{snapshot}'"
    cas = ",".join(f"'{c}'" for c in TARGET_COMMUNITY_AREAS)
    bbox = (f"latitude >= {_BOUNDS.lat_min} AND latitude <= {_BOUNDS.lat_max} "
            f"AND longitude >= {_BOUNDS.lon_min} AND longitude <= {_BOUNDS.lon_max}")
    return [
        f"{window} AND community_area in({cas})",
        f"{window} AND community_area is null AND {bbox}",
    ]


def fetch_permits(session: requests.Session, *, since: str = PERMITS_EPOCH,
                  snapshot: str, app_token: str | None = None,
                  max_rows: int | None = None) -> pd.DataFrame:
    """Permits with `since <= issue_date <= snapshot`, both arms (deterministic pages)."""
    url = _PORTAL.resource_url(_PORTAL.building_permits_id)
    rows: list[dict] = []
    for where in permit_where_clauses(since, snapshot):
        remaining = None if max_rows is None else max_rows - len(rows)
        if remaining is not None and remaining <= 0:
            break
        rows.extend(paged(session, url,
                          select=",".join(PERMIT_SELECT_COLS), where=where, order=":id",
                          app_token=app_token, page_size=_PORTAL.page_size,
                          courtesy_sleep_s=_PORTAL.courtesy_sleep_s, max_rows=remaining))
    return pd.DataFrame(rows, columns=_PANEL_COLS)


def assemble_permits(raw: pd.DataFrame) -> pd.DataFrame:
    """Coerce types and sort deterministically for byte-reproducible serialization.

    Sort key (issue_date, id): `id` is the dataset's unique row id, so the sort
    is a total order and re-pulls serialize identically. Numerics are coerced
    (SODA returns numbers as JSON strings); `reported_cost` stays float64
    (owner-declared, no cents convention); ids and `pin_list` stay strings.
    """
    if raw.empty:
        return pd.DataFrame(columns=_PANEL_COLS)
    permits = raw.copy()
    for col in ("issue_date", "application_start_date"):
        permits[col] = pd.to_datetime(permits[col], errors="coerce")
    for col in ("reported_cost", "latitude", "longitude"):
        permits[col] = pd.to_numeric(permits[col], errors="coerce")
    # Negative declared costs are upstream data-entry artifacts (observed live:
    # -1000 on one row of the 2026-07-06 pull); a cost cannot be negative, so
    # they are nulled rather than failing the whole pull or silently passing.
    permits.loc[permits["reported_cost"] < 0, "reported_cost"] = None
    # Null-safe id cast: a blind astype(str) would turn NaN into the literal
    # "nan" and slip past the schema's nullable=False gate (audit CR-1-13);
    # map() sidesteps dtype-upcast setitem fragility under pandas 3 (CR-2-2).
    permits["id"] = permits["id"].map(lambda v: str(v) if pd.notna(v) else None)
    return permits.sort_values(["issue_date", "id"], kind="stable").reset_index(drop=True)


def explode_pin10(pin_list: str | float | None) -> list[str]:
    """PIN10 join keys from a raw `pin_list` cell; malformed tokens are dropped.

    Cells join one or more PINs with ' | ' (probed upstream format; the split
    also tolerates ';'/','). Token semantics: exactly 10 digits -> kept; a full
    14-digit PIN -> its pin10 prefix (documented truncation); anything else
    (11-13 digits, non-numeric) -> dropped rather than truncated into a
    plausible-looking wrong key (audit CR-1-12/F-1-6). Null/NaN -> [].
    """
    if pin_list is None or (isinstance(pin_list, float) and pd.isna(pin_list)):
        return []
    out: list[str] = []
    for token in _SPLIT_RE.split(str(pin_list).strip()):
        if _PIN10_TOKEN_RE.match(token):
            out.append(token)
        elif _PIN14_TOKEN_RE.match(token):
            out.append(token[:10])
    return out
