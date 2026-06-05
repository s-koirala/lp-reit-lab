"""Cook County connector unit tests (no network): join logic + AV→market math."""

import pandas as pd
import pytest

from lp_reit_lab.ingest.config import Assessment
from lp_reit_lab.ingest.schemas import property_sales_schema
from lp_reit_lab.ingest.sources import cook_county


def _universe() -> pd.DataFrame:
    return pd.DataFrame({
        "pin": ["11111111111111", "22222222222222"],
        "year": ["2024", "2024"],
        "zip_code": ["60614", "60657"],
        "lat": ["41.92", "41.94"],
        "lon": ["-87.65", "-87.65"],
        "chicago_community_area_num": ["7", "6"],
        "chicago_community_area_name": ["LINCOLN PARK", "LAKE VIEW"],
        "census_tract_geoid": ["17031070100", "17031060100"],
    })


def _sales() -> pd.DataFrame:
    return pd.DataFrame({
        # one in-target PIN, one PIN outside the target universe
        "pin": ["11111111111111", "99999999999999"],
        "year": ["2019", "2019"],
        "class": ["203", "203"],
        "sale_date": ["2019-05-01", "2019-06-01"],
        "sale_price": ["750000", "400000"],
        "doc_no": ["DOC1", "DOC2"],
    })


def test_assemble_panel_restricts_and_joins_geography():
    panel = cook_county.assemble_panel(_universe(), _sales())
    # only the in-target PIN survives
    assert list(panel["pin"]) == ["11111111111111"]
    # geography attached + numerics coerced
    assert panel.loc[0, "chicago_community_area_name"] == "LINCOLN PARK"
    assert panel.loc[0, "sale_price"] == 750000
    assert panel.loc[0, "latitude"] == pytest.approx(41.92)
    assert pd.api.types.is_datetime64_any_dtype(panel["sale_date"])


def test_assessed_to_market_class2():
    # Class 2 LOA = 10% -> market = AV / 0.10
    assert cook_county.assessed_to_market(50_000) == pytest.approx(500_000)
    assert cook_county.assessed_to_market(50_000, Assessment()) == pytest.approx(500_000)


def _empty_sales() -> pd.DataFrame:
    return pd.DataFrame(columns=["pin", "year", "class", "sale_date", "sale_price", "doc_no"])


def test_assemble_panel_empty_sales_no_keyerror():
    panel = cook_county.assemble_panel(_universe(), _empty_sales())
    assert panel.empty
    assert "pin" in panel.columns


def test_assemble_panel_renames_latlon_without_duplicates():
    panel = cook_county.assemble_panel(_universe(), _sales())
    assert {"latitude", "longitude"} <= set(panel.columns)
    assert "lat" not in panel.columns and "lon" not in panel.columns


def test_valid_pins_drops_malformed():
    assert cook_county._valid_pins(
        ["11111111111111", "123", "x'; DROP--", "22222222222222"]
    ) == ["11111111111111", "22222222222222"]


def test_assemble_panel_passes_schema_end_to_end():
    panel = cook_county.assemble_panel(_universe(), _sales())
    property_sales_schema("2026-06-05").validate(panel, lazy=True)
