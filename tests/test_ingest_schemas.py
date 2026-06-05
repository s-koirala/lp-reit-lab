"""pandera schema tests — including the no-look-ahead (future-date) gate."""

import pandas as pd
import pandera.errors
import pytest

from lp_reit_lab.ingest.schemas import property_sales_schema

_SNAPSHOT = "2026-06-05"


def _valid_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "pin": ["12345678901234"],
        "sale_date": [pd.Timestamp("2020-01-01")],
        "sale_price": [500_000],
        "class": ["203"],
        "latitude": [41.92],
        "longitude": [-87.65],
    })


def test_valid_frame_passes():
    property_sales_schema(_SNAPSHOT).validate(_valid_frame())


def test_future_sale_date_rejected_no_look_ahead():
    df = _valid_frame()
    df.loc[0, "sale_date"] = pd.Timestamp("2030-01-01")  # after snapshot
    with pytest.raises(pandera.errors.SchemaError):
        property_sales_schema(_SNAPSHOT).validate(df)


def test_bad_pin_rejected():
    df = _valid_frame()
    df.loc[0, "pin"] = "123"  # not 14 digits
    with pytest.raises(pandera.errors.SchemaError):
        property_sales_schema(_SNAPSHOT).validate(df)


def test_nonpositive_price_rejected():
    df = _valid_frame()
    df.loc[0, "sale_price"] = -1
    with pytest.raises(pandera.errors.SchemaError):
        property_sales_schema(_SNAPSHOT).validate(df)


def test_out_of_county_latitude_rejected():
    df = _valid_frame()
    df.loc[0, "latitude"] = 0.0  # outside Cook County envelope
    with pytest.raises(pandera.errors.SchemaError):
        property_sales_schema(_SNAPSHOT).validate(df)


def test_same_day_accepted_next_day_rejected():
    df = _valid_frame()
    df.loc[0, "sale_date"] = pd.Timestamp(_SNAPSHOT)  # == snapshot: inclusive, accepted
    property_sales_schema(_SNAPSHOT).validate(df)
    df.loc[0, "sale_date"] = pd.Timestamp(_SNAPSHOT) + pd.Timedelta(days=1)  # after: rejected
    with pytest.raises(pandera.errors.SchemaError):
        property_sales_schema(_SNAPSHOT).validate(df)
