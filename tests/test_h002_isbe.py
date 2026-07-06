"""Tests for the ISBE Report Card parser + quality-rank builder (H002).

Offline unit tests run on tiny synthetic fixtures built in tmp_path
(fake layout workbook + semicolon-delimited zip for the zip era; fake
public-data-set workbooks for the 2018+ era) per the recipe in
docs/methodology/methodology_isbe-quality-recipe_2026-07-06.md.
One opt-in integration test parses three real vintages from the snapshot.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from openpyxl import Workbook

from lp_reit_lab.h002.isbe import hazen_rank, load_school_quality

REAL_SNAPSHOT = Path("data/raw/isbe_report_card/snapshot=2026-07-06")

# CPS district prefix (config.CPS_RCDTS_DISTRICT_PREFIX) + school suffixes.
CPS = "150162990"


# --------------------------------------------------------------------------
# Fixture builders
# --------------------------------------------------------------------------


def _write_layout(path: Path, sheet: str, rows: list[tuple]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    for row in rows:
        ws.append(row)
    wb.save(path)


def _write_zip(path: Path, member: str, lines: list[list[str]]) -> None:
    payload = "\n".join(";".join(fields) for fields in lines) + "\n"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(member, payload)


def _write_workbook(path: Path, sheet: str, header: list[str], rows: list[list]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(header)
    for row in rows:
        ws.append(row)
    wb.save(path)


@pytest.fixture
def zip_era_dir(tmp_path: Path) -> Path:
    """Synthetic rc2014 vintage: layout + semicolon txt with drifted fields.

    Layout mimics the real structure (field number in col A, assessment
    group in col B, position range / width / description / format after) and
    plants THREE decoys around the true composite: the prior-year (2013)
    restatement, an ISAT-group repeat, and a section-header prose row —
    resolution must land on field #6 (ALL TESTS x 2014) by description+group
    match, not on any hard-coded position.
    """
    raw = tmp_path / "raw"
    raw.mkdir()
    layout_rows = [
        (1, None, None, "1-16", 16, "SCHOOL ID (R-C-D-T-S)", "A15"),
        (2, None, None, "17-18", 2, "SCHOOL TYPE CODE (0,1,2,C)", "A1"),
        (3, None, None, "19-19", 1, "Blank", "A0"),
        (4, None, None, "20-53", 34, "SCHOOL NAME", "A33"),
        ("OVERALL ACHIEVEMENT PERFORMANCE (ISAT/PSAE/IAA)", None, None, None, None, None, None),
        (5, "ALL TESTS", "2013-COMPOSITE", "54-59", 6,
         "2013 SCHOOL COMPOSITE PERCENT FOR MEETS & EXCEEDS(read and math) ", "F5.1"),
        (6, "ALL TESTS", "2014-COMPOSITE", "60-65", 6,
         "2014 SCHOOL COMPOSITE PERCENT FOR MEETS & EXCEEDS(read and math) ", "F5.1"),
        (7, "ISAT", "2014-COMPOSITE", "66-71", 6,
         "2014 SCHOOL COMPOSITE PERCENT FOR MEETS & EXCEEDS(read and math) ", "F5.1"),
    ]
    _write_layout(raw / "rc2014_RC14_layout.xlsx", "RC14", layout_rows)

    # fields: rcdts; type; blank; name; 2013 decoy; 2014 composite; ISAT decoy
    lines = [
        [f"{CPS}250001", "2", "", "Alpha Elem School      ", " 11.1", " 91.8", " 22.2"],
        [f"{CPS}250002", "2", "", "Beta Elem School       ", " 11.1", " 50.0", " 22.2"],
        [f"{CPS}250003", "2", "", "Gamma Elem School      ", " 11.1", " 75.0", " 22.2"],
        [f"{CPS}250004", "2", "", "Delta Elem School      ", " 11.1", "     ", " 22.2"],
        [f"{CPS}250005", "0", "", "Epsilon High School    ", " 11.1", " 72.8", " 22.2"],
        [f"{CPS}250006", "1", "", "Zeta Middle School     ", " 11.1", " 60.0", " 22.2"],
        [f"{CPS}25007C", "C", "", "Eta Charter School     ", " 11.1", " 60.0", " 22.2"],
        [f"{CPS}250000", "2", "", "District Office        ", " 11.1", " 60.0", " 22.2"],
        ["340491010262002", "2", "", "Suburban Elem School   ", " 11.1", " 60.0", " 22.2"],
    ]
    _write_zip(raw / "rc2014_rc14.zip", "rc14.txt", lines)
    return raw


WB_HEADER = ["RCDTS", "Type", "School Name", "School Type",
             "% ELA Proficiency", "% Math Proficiency"]


@pytest.fixture
def workbook_era_dir(tmp_path: Path) -> Path:
    """Synthetic rc2018 (Total-% naming) + rc2019 + assessment-less rc2020."""
    raw = tmp_path / "raw"
    raw.mkdir()
    _write_workbook(
        raw / "rc2018_Report-Card-Public-Data-Set.xlsx",
        "ELA and Math",
        ["RCDTS", "Type", "School Name", "School Type",
         "ELA Proficiency Total %", "Math Proficiency Total %"],
        [
            [f"{CPS}250000", "District", "", "", "33.3", "33.3"],
            [f"{CPS}251111", "School", "Elem One", "ELEMENTARY", "40.0", "60.0"],
            [f"{CPS}252222", "School", "Elem Two", "ELEMENTARY", "20.0", "*"],
            [f"{CPS}253333", "School", "HS One", "HIGH SCHOOL", "30.0", "50.0"],
            [f"{CPS}25444C", "School", "Charter One", "CHARTER SCH", "50.0", "50.0"],
            [f"{CPS}255555", "School", "PreK One", "PreK", "", ""],
            ["340491010262002", "School", "Suburban Elem", "ELEMENTARY", "80.0", "80.0"],
        ],
    )
    _write_workbook(
        raw / "rc2019_2019-Report-Card-Public-Data-Set.xlsx",
        "ELA Math Science",
        WB_HEADER,
        [
            [f"{CPS}250000", "District", "", "", "33.3", "33.3"],
            ["15-016-2990-25-1111", "School", "Elem One", "ELEMENTARY", "30.0", "50.0"],
            [f"{CPS}252222", "School", "Elem Two", "ELEMENTARY", "60.0", "80.0"],
            [f"{CPS}253333", "School", "HS One", "HIGH SCHOOL", "25.0", "35.0"],
        ],
    )
    # COVID-waiver vintage: sheet exists, proficiency columns absent.
    _write_workbook(
        raw / "rc2020_2020-Report-Card-Public-Data-Set.xlsx",
        "ELA Math Science",
        ["RCDTS", "Type", "School Name", "School Type", "% EL students"],
        [[f"{CPS}251111", "School", "Elem One", "ELEMENTARY", "5.0"]],
    )
    return raw


# --------------------------------------------------------------------------
# Hazen rank
# --------------------------------------------------------------------------


def test_hazen_rank_is_i_minus_half_over_n() -> None:
    ranks = hazen_rank(pd.Series([10.0, 30.0, 20.0, 40.0]))
    assert ranks.tolist() == [(1 - 0.5) / 4, (3 - 0.5) / 4, (2 - 0.5) / 4, (4 - 0.5) / 4]


def test_hazen_rank_ties_get_mid_ranks() -> None:
    ranks = hazen_rank(pd.Series([10.0, 20.0, 20.0, 30.0]))
    # tied mid-rank r = 2.5 -> (2.5 - 0.5) / 4 for both middle values
    assert ranks.tolist() == [(1 - 0.5) / 4, 0.5, 0.5, (4 - 0.5) / 4]


def test_hazen_rank_excludes_nan_from_n() -> None:
    ranks = hazen_rank(pd.Series([10.0, np.nan, 20.0]))
    assert np.isnan(ranks.iloc[1])
    assert ranks.iloc[0] == (1 - 0.5) / 2
    assert ranks.iloc[2] == (2 - 0.5) / 2


# --------------------------------------------------------------------------
# Zip era end-to-end
# --------------------------------------------------------------------------


def test_layout_description_resolution_beats_decoys(zip_era_dir: Path) -> None:
    """Metric must come from the ALL TESTS x current-year field, not the
    prior-year restatement (11.1) or the per-assessment repeat (22.2)."""
    frame = load_school_quality(zip_era_dir)
    alpha = frame.loc[frame["school_name"] == "Alpha Elem School"].iloc[0]
    assert alpha["metric_value"] == pytest.approx(91.8)
    assert not (frame["metric_value"] == 11.1).any()
    assert not (frame["metric_value"] == 22.2).any()


def test_semicolon_parse_strips_space_padding(zip_era_dir: Path) -> None:
    frame = load_school_quality(zip_era_dir)
    assert "Epsilon High School" in set(frame["school_name"])  # padded name stripped
    eps = frame.loc[frame["school_name"] == "Epsilon High School"].iloc[0]
    assert eps["metric_value"] == pytest.approx(72.8)  # ' 72.8' parsed
    assert eps["level"] == "high_school"
    assert eps["rcdts"] == f"{CPS}250005"


def test_cps_filter_and_row_type_filters(zip_era_dir: Path) -> None:
    frame = load_school_quality(zip_era_dir)
    names = set(frame["school_name"])
    assert "Suburban Elem School" not in names  # non-CPS RCDTS prefix
    assert "Zeta Middle School" not in names  # type code 1 (recipe §4.4)
    assert "Eta Charter School" not in names  # type code C (recipe §2.1)
    assert "District Office" not in names  # school suffix 0000 aggregate
    assert all(frame["rcdts"].str.startswith(CPS))


def test_zip_era_hazen_ranks_within_level_pools(zip_era_dir: Path) -> None:
    frame = load_school_quality(zip_era_dir)
    elem = frame[frame["level"] == "elementary"].set_index("school_name")
    # Delta's blank metric is excluded from n -> n = 3 ranked elems.
    assert elem.loc["Beta Elem School", "quality_rank"] == pytest.approx((1 - 0.5) / 3)
    assert elem.loc["Gamma Elem School", "quality_rank"] == pytest.approx((2 - 0.5) / 3)
    assert elem.loc["Alpha Elem School", "quality_rank"] == pytest.approx((3 - 0.5) / 3)
    # High-school pool is separate: single school -> (1 - 0.5) / 1.
    hs = frame[frame["level"] == "high_school"]
    assert hs["quality_rank"].tolist() == [pytest.approx(0.5)]


def test_ferpa_blank_metric_is_nan_and_unranked(zip_era_dir: Path) -> None:
    frame = load_school_quality(zip_era_dir)
    delta = frame.loc[frame["school_name"] == "Delta Elem School"].iloc[0]
    assert np.isnan(delta["metric_value"])
    assert np.isnan(delta["quality_rank"])


def test_in_force_window_dates(zip_era_dir: Path) -> None:
    frame = load_school_quality(zip_era_dir)
    assert (frame["rc_year"] == 2014).all()
    assert (frame["in_force_start"] == pd.Timestamp("2014-11-01")).all()
    assert (frame["in_force_end"] == pd.Timestamp("2015-10-31")).all()
    assert (frame["metric_regime"] == "ISAT/PSAE").all()
    assert not frame["stale"].any()


# --------------------------------------------------------------------------
# Workbook era end-to-end
# --------------------------------------------------------------------------


def test_workbook_metric_is_unweighted_subject_mean(workbook_era_dir: Path) -> None:
    frame = load_school_quality(workbook_era_dir, years=[2018])
    row = frame.loc[frame["school_name"] == "Elem One"].iloc[0]
    assert row["metric_value"] == pytest.approx(50.0)  # mean(40, 60), recipe §1.3
    assert row["metric_regime"] == "PARCC"


def test_workbook_ferpa_star_is_nan_and_excluded_from_n(workbook_era_dir: Path) -> None:
    frame = load_school_quality(workbook_era_dir, years=[2018])
    two = frame.loc[frame["school_name"] == "Elem Two"].iloc[0]
    assert np.isnan(two["metric_value"])  # '*' in math -> composite missing (§4.1)
    assert np.isnan(two["quality_rank"])
    one = frame.loc[frame["school_name"] == "Elem One"].iloc[0]
    assert one["quality_rank"] == pytest.approx((1 - 0.5) / 1)  # pool n=1 after exclusions


def test_workbook_filters_district_charter_prek_noncps(workbook_era_dir: Path) -> None:
    frame = load_school_quality(workbook_era_dir, years=[2018])
    names = set(frame["school_name"])
    assert names == {"Elem One", "Elem Two", "HS One"}


def test_dashed_rcdts_normalized(workbook_era_dir: Path) -> None:
    frame = load_school_quality(workbook_era_dir, years=[2019])
    one = frame.loc[frame["school_name"] == "Elem One"].iloc[0]
    assert one["rcdts"] == f"{CPS}251111"  # 15-016-2990-25-1111 compacted


def test_covid_carry_forward_rows_are_stale_copies_of_prior_vintage(
    workbook_era_dir: Path,
) -> None:
    frame = load_school_quality(workbook_era_dir, years=[2019, 2020])
    rc19 = frame[frame["rc_year"] == 2019].set_index("rcdts")
    rc20 = frame[frame["rc_year"] == 2020].set_index("rcdts")
    # Same schools, same metrics, same ranks — the rc2019 label stays in force.
    assert set(rc20.index) == set(rc19.index)
    for rcdts in rc19.index:
        assert rc20.loc[rcdts, "metric_value"] == rc19.loc[rcdts, "metric_value"]
        assert rc20.loc[rcdts, "quality_rank"] == rc19.loc[rcdts, "quality_rank"]
    assert not rc19["stale"].any()
    assert rc20["stale"].all()
    assert (rc20["metric_regime"] == "IAR+SAT").all()  # source vintage's regime
    assert (rc20["in_force_start"] == pd.Timestamp("2020-11-01")).all()
    assert (rc20["in_force_end"] == pd.Timestamp("2021-10-31")).all()


def test_covid_vintage_pulls_carry_source_even_if_not_requested(
    workbook_era_dir: Path,
) -> None:
    frame = load_school_quality(workbook_era_dir, years=[2020])
    assert set(frame["rc_year"]) == {2020}
    assert frame["stale"].all()
    assert len(frame) == 3  # the three rc2019 CPS schools


# --------------------------------------------------------------------------
# Opt-in integration test against the real snapshot
# --------------------------------------------------------------------------


@pytest.mark.skipif(
    not REAL_SNAPSHOT.exists(),
    reason="real ISBE snapshot not present (offline CI)",
)
def test_real_snapshot_three_years() -> None:
    frame = load_school_quality(REAL_SNAPSHOT, years=[2014, 2018, 2024])
    for year, regime in [(2014, "ISAT/PSAE"), (2018, "PARCC"), (2024, "IAR+SAT")]:
        sub = frame[frame["rc_year"] == year]
        ranked = sub[sub["quality_rank"].notna()]
        assert len(ranked) > 300, f"rc{year}: only {len(ranked)} ranked CPS schools"
        assert set(sub["level"]) == {"elementary", "high_school"}
        assert (sub["metric_regime"] == regime).all()
        assert ranked["quality_rank"].between(0, 1, inclusive="neither").all()
        assert ranked["metric_value"].between(0, 100).all()
        # Hazen invariants per level pool: ranks bounded by the endpoint
        # positions (ties at an extreme pull the endpoint inward via
        # mid-ranks) and mean rank exactly 0.5 (mid-ranks preserve the
        # rank sum: mean of (r - 0.5)/n = ((n+1)/2 - 0.5)/n = 0.5).
        for _level, pool in ranked.groupby("level"):
            n = len(pool)
            assert pool["quality_rank"].min() >= 0.5 / n
            assert pool["quality_rank"].max() <= (n - 0.5) / n
            assert pool["quality_rank"].mean() == pytest.approx(0.5)
    # Recipe §6 row-level anchor: Lincoln Elem 91.8 composite in rc2014.
    lincoln = frame[(frame["rc_year"] == 2014) & (frame["rcdts"] == f"{CPS}252314")]
    assert lincoln["metric_value"].iloc[0] == pytest.approx(91.8)
