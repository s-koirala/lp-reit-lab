"""Chicago permits connector unit tests (no network): assembly determinism,
schema gate, PIN10 extraction semantics, PII exclusion, dual-arm query."""

import pandas as pd
import pandera.errors
import pytest

from lp_reit_lab.ingest.config import PERMIT_SELECT_COLS
from lp_reit_lab.ingest.schemas import building_permits_schema
from lp_reit_lab.ingest.sources import chicago_permits


def _raw(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=list(PERMIT_SELECT_COLS))


def _row(permit_id: str, issue: str, **overrides) -> dict:
    base = {
        "id": permit_id, "permit_": f"100{permit_id}",
        "permit_type": "PERMIT - RENOVATION/ALTERATION",
        "review_type": "STANDARD", "application_start_date": issue, "issue_date": issue,
        "work_description": "INTERIOR ALTERATION", "reported_cost": "150000",
        "pin_list": "1432422025", "community_area": "7", "census_tract": "719",
        "ward": "43", "latitude": "41.91", "longitude": "-87.65",
    }
    base.update(overrides)
    return base


def test_assemble_sorts_deterministically_and_coerces():
    shuffled = _raw([_row("2", "2020-05-01"), _row("1", "2019-01-01"), _row("3", "2019-01-01")])
    panel = chicago_permits.assemble_permits(shuffled)
    assert list(panel["id"]) == ["1", "3", "2"]  # (issue_date, id) total order
    assert pd.api.types.is_datetime64_any_dtype(panel["issue_date"])
    assert panel.loc[0, "reported_cost"] == pytest.approx(150000.0)


def test_assemble_empty_keeps_columns():
    panel = chicago_permits.assemble_permits(_raw([]))
    assert panel.empty
    assert "issue_date" in panel.columns


def test_assemble_null_id_stays_null_and_fails_schema():
    # astype(str) would smuggle NaN through as the string "nan" (audit CR-1-13)
    panel = chicago_permits.assemble_permits(_raw([_row("1", "2019-01-01",
                                                        id=None)]))
    assert panel["id"].isna().all()
    with pytest.raises(pandera.errors.SchemaErrors, match="id"):
        building_permits_schema("2026-07-06").validate(panel, lazy=True)


def test_schema_passes_assembled_panel():
    panel = chicago_permits.assemble_permits(_raw([_row("1", "2019-01-01")]))
    building_permits_schema("2026-07-06").validate(panel, lazy=True)


def test_assemble_nulls_negative_reported_cost():
    # observed upstream: reported_cost=-1000 on a live row; entry artifact -> null
    panel = chicago_permits.assemble_permits(_raw([_row("1", "2019-01-01",
                                                        reported_cost="-1000")]))
    assert panel["reported_cost"].isna().all()
    building_permits_schema("2026-07-06").validate(panel, lazy=True)


def test_schema_accepts_null_community_area_bbox_arm():
    panel = chicago_permits.assemble_permits(_raw([_row("1", "2019-01-01",
                                                        community_area=None)]))
    building_permits_schema("2026-07-06").validate(panel, lazy=True)


def test_schema_rejects_future_issue_date():
    panel = chicago_permits.assemble_permits(_raw([_row("1", "2026-07-07")]))
    with pytest.raises(pandera.errors.SchemaErrors, match="issue_date"):
        building_permits_schema("2026-07-06").validate(panel, lazy=True)


def test_schema_rejects_out_of_target_community_area():
    panel = chicago_permits.assemble_permits(_raw([_row("1", "2019-01-01",
                                                        community_area="22")]))
    with pytest.raises(pandera.errors.SchemaErrors, match="community_area"):
        building_permits_schema("2026-07-06").validate(panel, lazy=True)


def test_where_clauses_cover_labelled_and_null_ca_arms():
    arms = chicago_permits.permit_where_clauses("2006-01-01", "2026-07-06")
    assert len(arms) == 2
    assert "community_area in('6','7','8')" in arms[0]
    assert "community_area is null" in arms[1] and "latitude >=" in arms[1]
    for arm in arms:
        assert "issue_date >= '2006-01-01'" in arm
        assert "issue_date <= '2026-07-06'" in arm


@pytest.mark.parametrize("cell, expected", [
    ("1432422025", ["1432422025"]),
    ("1430400081 | 1430400082", ["1430400081", "1430400082"]),  # live upstream format
    ("1432422025;1432422026", ["1432422025", "1432422026"]),
    ("1432422025, 1432422026", ["1432422025", "1432422026"]),
    ("14324220250000", ["1432422025"]),   # full PIN14 -> documented pin10 prefix
    ("14324220251", []),                  # 11 digits: dropped, never truncated
    (None, []),
    (float("nan"), []),
    ("garbage", []),
])
def test_explode_pin10(cell, expected):
    assert chicago_permits.explode_pin10(cell) == expected


def test_select_excludes_contact_pii_columns():
    assert not any(c.startswith("contact_") for c in PERMIT_SELECT_COLS)
