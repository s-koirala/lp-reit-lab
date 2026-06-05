"""Manifest tests: deterministic hashing + drift detection."""

import json

from lp_reit_lab.ingest import manifest


def test_sha256_is_deterministic(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("pin,price\n12345678901234,500000\n", encoding="utf-8")
    assert manifest.sha256_file(f) == manifest.sha256_file(f)


def test_manifest_entry_fields(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("x\n1\n", encoding="utf-8")
    entry = manifest.manifest_entry(f, source_url="https://example/resource.json",
                                    snapshot_date="2026-06-05", row_count=1)
    assert entry["sha256"] == manifest.sha256_file(f)
    assert entry["source_url"].startswith("https://")
    assert entry["row_count"] == 1
    assert entry["path"].endswith("a.csv")


def test_check_drift_detects_change(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("original\n", encoding="utf-8")
    entry = manifest.manifest_entry(f, source_url="u", snapshot_date="2026-06-05", row_count=1)
    man = tmp_path / "_manifest.json"
    man.write_text(json.dumps({"files": [entry]}), encoding="utf-8")
    assert manifest.check_drift(man) == []          # unchanged
    f.write_text("tampered\n", encoding="utf-8")
    assert manifest.check_drift(man) == [(entry["path"], "CHANGED")]


def test_write_manifest_atomic(tmp_path):
    p = tmp_path / "sub" / "m.json"
    manifest.write_manifest_atomic(p, {"files": [{"path": "x"}]})
    assert json.loads(p.read_text(encoding="utf-8"))["files"][0]["path"] == "x"


def test_manifest_entry_records_source_version(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("x\n1\n", encoding="utf-8")
    entry = manifest.manifest_entry(f, source_url="u", snapshot_date="2026-06-05",
                                    row_count=1, source_version="1700000000")
    assert entry["source_version"] == "1700000000"
