"""ISBE report-card connector unit tests (no network): release-date gating,
container validation (ZIP + OLE2), config integrity, sha pinning."""

import re

import pytest

from lp_reit_lab.ingest.config import ISBE_REPORT_CARD_FILES
from lp_reit_lab.ingest.manifest import manifest_entry
from lp_reit_lab.ingest.sources import isbe_report_card

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def test_configured_years_contiguous_2006_2025():
    years = isbe_report_card.report_card_years()
    assert years == list(range(2006, 2026))


def test_every_year_has_https_isbe_data_url_and_sha_pin():
    for year, spec in ISBE_REPORT_CARD_FILES.items():
        assert spec["data"] and spec["data"].startswith("https://www.isbe.net/"), year
        assert _SHA256_RE.match(spec["sha256"]), year
        if spec["layout"] is not None:
            assert spec["layout"].startswith("https://www.isbe.net/"), year


def test_sha_pins_unique():
    shas = [spec["sha256"] for spec in ISBE_REPORT_CARD_FILES.values()]
    assert len(shas) == len(set(shas))  # duplicate pins = copy-paste corruption


def test_zip_era_has_layouts_xlsx_era_does_not():
    for year, spec in ISBE_REPORT_CARD_FILES.items():
        assert (spec["layout"] is not None) == (year <= 2017), year


def test_2015_2017_pin_the_assessment_variants():
    # The base rc{15,16,17}.zip files EXCLUDE assessment data (discovery memo);
    # a silent regression to them would gut the quality signal.
    for year in (2015, 2016, 2017):
        assert "assessment" in str(ISBE_REPORT_CARD_FILES[year]["data"]), year


def test_years_knowable_gates_on_public_release_not_school_year_end():
    # rc year N releases ~late October of year N (105 ILCS 5/10-17a: prepared
    # by Oct 31); knowable only from Nov 1 (audit F-1-2).
    assert 2025 in isbe_report_card.years_knowable_at("2026-07-06")
    assert 2025 not in isbe_report_card.years_knowable_at("2025-07-01")
    assert 2025 not in isbe_report_card.years_knowable_at("2025-10-15")
    assert 2025 in isbe_report_card.years_knowable_at("2025-11-01")


def test_validate_zip_container(tmp_path):
    good = tmp_path / "good.xlsx"
    good.write_bytes(b"PK\x03\x04" + b"\x00" * 16)
    isbe_report_card.validate_zip_container(good)

    html = tmp_path / "soft404.xlsx"
    html.write_bytes(b"<!DOCTYPE html><html>error</html>")
    with pytest.raises(ValueError, match="not a ZIP container"):
        isbe_report_card.validate_zip_container(html)


def test_validate_ole2_container(tmp_path):
    good = tmp_path / "layout.xls"
    good.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 8)
    isbe_report_card.validate_ole2_container(good)

    html = tmp_path / "soft404.xls"
    html.write_bytes(b"<!DOCTYPE html>")
    with pytest.raises(ValueError, match="not a OLE2"):
        isbe_report_card.validate_ole2_container(html)


def test_manifest_entry_accepts_null_row_count(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "blob.bin"
    f.write_bytes(b"PK\x03\x04data")
    entry = manifest_entry(f.relative_to(tmp_path), source_url="https://example.org/x",
                           snapshot_date="2026-07-06", row_count=None)
    assert entry["row_count"] is None
    assert entry["bytes"] == 8
