"""pandera validation schemas for ingested Cook County data.

The `sale_date` upper bound is the snapshot date, so future-dated rows are rejected
at the gate — a no-look-ahead guarantee enforced by validation, not convention. The
bound is inclusive: a sale dated exactly on the snapshot day is accepted (CCAO
sale_date is date-only, so same-day completeness is acceptable; revisit if an
intraday-timestamped source is added). `nullable=False` on `sale_date` also rejects
coerced NaT. PIN is a 14-digit zero-padded string (Socrata drops leading zeros if
treated numerically), never an int. `sale_price` matches the connector's nullable
`Int64` (whole-dollar USD).
"""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

from .config import PERMITS_EPOCH, TARGET_COMMUNITY_AREAS, CookCountyBounds

_B = CookCountyBounds()


def property_sales_schema(snapshot_date: str | pd.Timestamp) -> pa.DataFrameSchema:
    """Schema for the joined sales panel, bounded by the data snapshot date.

    `strict=False`: the panel carries joined geography columns we don't all model.
    `unique` is the surrogate key (pin, sale_date, sale_price); the CCAO deed
    identifier `doc_no` is carried in the panel for stricter downstream dedup but is
    not the gate key here (it can be null on legacy rows).
    """
    snap = pd.Timestamp(snapshot_date)
    return pa.DataFrameSchema(
        columns={
            "pin": pa.Column(
                str, checks=pa.Check.str_matches(r"^\d{14}$"), nullable=False
            ),
            "sale_date": pa.Column(
                "datetime64[ns]",
                checks=pa.Check.in_range(pd.Timestamp(_B.sales_epoch_start), snap),
                nullable=False,   # also rejects coerced NaT
                coerce=True,
            ),
            "sale_price": pa.Column(
                "Int64", checks=pa.Check.greater_than(0), nullable=False, coerce=True
            ),
            "class": pa.Column(str, nullable=False),
            "doc_no": pa.Column(str, nullable=True, required=False),
            "latitude": pa.Column(
                "float64",
                checks=pa.Check.in_range(_B.lat_min, _B.lat_max),
                nullable=True,
                coerce=True,
            ),
            "longitude": pa.Column(
                "float64",
                checks=pa.Check.in_range(_B.lon_min, _B.lon_max),
                nullable=True,
                coerce=True,
            ),
        },
        strict=False,
        unique=["pin", "sale_date", "sale_price"],
        report_duplicates="all",
        name="cook_county_property_sales",
    )


def building_permits_schema(snapshot_date: str | pd.Timestamp) -> pa.DataFrameSchema:
    """Schema for the assembled Chicago building-permits panel.

    `issue_date` is bounded by [PERMITS_EPOCH, snapshot] — the same
    validation-enforced no-look-ahead gate as the sales panel. `id` is the
    dataset's unique row id (the deterministic-sort key). `community_area` is
    NULLABLE (the null-CA bbox arm keeps geocoding-gap permits, audit F-1-5)
    but any non-null value must be a target area — a defense against silently
    changed upstream filter semantics.
    """
    snap = pd.Timestamp(snapshot_date)
    return pa.DataFrameSchema(
        columns={
            "id": pa.Column(str, nullable=False, coerce=True),
            "permit_": pa.Column(str, nullable=True, coerce=True),
            "permit_type": pa.Column(str, nullable=True, coerce=True),
            "issue_date": pa.Column(
                "datetime64[ns]",
                checks=pa.Check.in_range(pd.Timestamp(PERMITS_EPOCH), snap),
                nullable=False,
                coerce=True,
            ),
            "application_start_date": pa.Column(
                "datetime64[ns]", nullable=True, coerce=True
            ),
            "reported_cost": pa.Column(
                "float64", checks=pa.Check.greater_than_or_equal_to(0),
                nullable=True, coerce=True,
            ),
            "pin_list": pa.Column(str, nullable=True, coerce=True),
            "community_area": pa.Column(
                str, checks=pa.Check.isin(sorted(TARGET_COMMUNITY_AREAS)),
                nullable=True, coerce=True,
            ),
            "latitude": pa.Column(
                "float64", checks=pa.Check.in_range(_B.lat_min, _B.lat_max),
                nullable=True, coerce=True,
            ),
            "longitude": pa.Column(
                "float64", checks=pa.Check.in_range(_B.lon_min, _B.lon_max),
                nullable=True, coerce=True,
            ),
        },
        strict=False,
        unique=["id"],
        report_duplicates="all",
        name="chicago_building_permits",
    )
