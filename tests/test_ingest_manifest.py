"""Manifest tests: deterministic hashing, drift detection, provenance fields,
repo-relative path guard, canonical serialization."""

import json

import pytest

from lp_reit_lab.ingest import manifest


@pytest.fixture()
def rel_cwd(tmp_path, monkeypatch):
    """Run in tmp_path so manifest entries can use repo-relative paths."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _touch(rel_cwd, name: str, text: str = "x\n1\n"):
    f = rel_cwd / name
    f.write_text(text, encoding="utf-8")
    return f.relative_to(rel_cwd)


def test_sha256_is_deterministic(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("pin,price\n12345678901234,500000\n", encoding="utf-8")
    assert manifest.sha256_file(f) == manifest.sha256_file(f)


def test_manifest_entry_fields(rel_cwd):
    rel = _touch(rel_cwd, "a.csv")
    entry = manifest.manifest_entry(rel, source_url="https://example/resource.json",
                                    snapshot_date="2026-06-05", row_count=1)
    assert entry["sha256"] == manifest.sha256_file(rel)
    assert entry["source_url"].startswith("https://")
    assert entry["row_count"] == 1
    assert entry["path"] == "a.csv"


def test_manifest_entry_rejects_absolute_path(rel_cwd):
    f = rel_cwd / "a.csv"
    f.write_text("x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="repo-relative"):
        manifest.manifest_entry(f, source_url="u", snapshot_date="2026-06-05", row_count=1)


def test_manifest_entry_optional_query_and_sources(rel_cwd):
    rel = _touch(rel_cwd, "a.csv")
    entry = manifest.manifest_entry(
        rel, source_url="u", snapshot_date="2026-06-05", row_count=1,
        query={"since": "1999-01-01"},
        sources=[{"url": "u1", "role": "sales"}, {"url": "u2", "role": "spine"}],
    )
    assert entry["query"]["since"] == "1999-01-01"
    assert [s["role"] for s in entry["sources"]] == ["sales", "spine"]
    bare = manifest.manifest_entry(rel, source_url="u", snapshot_date="2026-06-05",
                                   row_count=1)
    assert "query" not in bare and "sources" not in bare


def test_check_drift_detects_change(rel_cwd):
    rel = _touch(rel_cwd, "a.csv", "original\n")
    entry = manifest.manifest_entry(rel, source_url="u", snapshot_date="2026-06-05",
                                    row_count=1)
    man = rel_cwd / "_manifest.json"
    man.write_text(json.dumps({"files": [entry]}), encoding="utf-8")
    assert manifest.check_drift(man) == []          # unchanged
    (rel_cwd / "a.csv").write_text("tampered\n", encoding="utf-8")
    assert manifest.check_drift(man) == [(entry["path"], "CHANGED")]


def test_write_manifest_atomic_sorts_and_terminates(tmp_path):
    p = tmp_path / "sub" / "m.json"
    manifest.write_manifest_atomic(p, {"files": [{"path": "z"}, {"path": "a"}]})
    text = p.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert [f["path"] for f in json.loads(text)["files"]] == ["a", "z"]


def test_write_bytes_atomic(tmp_path):
    dest = tmp_path / "sub" / "blob.csv"
    manifest.write_bytes_atomic(dest, b"a,b\n1,2\n")
    assert dest.read_bytes() == b"a,b\n1,2\n"
    assert not list((tmp_path / "sub").glob("*.tmp"))


def test_manifest_entry_records_source_version(rel_cwd):
    rel = _touch(rel_cwd, "a.csv")
    entry = manifest.manifest_entry(rel, source_url="u", snapshot_date="2026-06-05",
                                    row_count=1, source_version="1700000000")
    assert entry["source_version"] == "1700000000"
