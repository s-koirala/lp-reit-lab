"""CLI exit-code contract tests (no network): 0=ok, 1=empty, 2=user error,
3=validation, 4=transport. Connectors are monkeypatched; the contract under
test is scripts/ingest.py's error routing."""

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

from lp_reit_lab.ingest.http_client import TransientHTTPError

_REPO = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("ingest_cli", _REPO / "scripts" / "ingest.py")
assert _SPEC is not None and _SPEC.loader is not None, "scripts/ingest.py not found"
ingest_cli = importlib.util.module_from_spec(_SPEC)
sys.modules["ingest_cli"] = ingest_cli
_SPEC.loader.exec_module(ingest_cli)


@pytest.fixture()
def repo_cwd(tmp_path, monkeypatch):
    """A fake repo root so _require_repo_root passes and writes stay in tmp."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_unknown_school_year_is_user_error(repo_cwd):
    rc = ingest_cli.main(["cps-boundaries", "--school-years", "SY9999"])
    assert rc == 2


def test_bad_snapshot_is_user_error(repo_cwd):
    rc = ingest_cli.main(["permits", "--snapshot", "not-a-date"])
    assert rc == 2


def test_isbe_non_integer_years_is_user_error(repo_cwd):
    rc = ingest_cli.main(["isbe", "--years", "2018,20I9"])
    assert rc == 2


def test_isbe_unknowable_year_is_user_error(repo_cwd):
    rc = ingest_cli.main(["isbe", "--years", "2026", "--snapshot", "2026-07-06"])
    assert rc == 2


@pytest.fixture()
def offline_permits_env(repo_cwd, monkeypatch):
    """Silence the network-touching pre-steps of cmd_permits."""
    monkeypatch.setattr(ingest_cli, "soql_count", lambda *a, **k: 0)
    monkeypatch.setattr(ingest_cli, "_source_version", lambda *a, **k: None)
    return repo_cwd


def test_permits_transport_failure_maps_to_4(offline_permits_env, monkeypatch):
    def boom(*a, **k):
        raise requests.exceptions.ConnectionError("down")

    monkeypatch.setattr(ingest_cli.chicago_permits, "fetch_permits", boom)
    rc = ingest_cli.main(["permits", "--snapshot", "2026-07-06"])
    assert rc == 4


def test_permits_retry_exhaustion_maps_to_4_not_traceback(offline_permits_env, monkeypatch):
    def exhausted(*a, **k):
        raise TransientHTTPError("503 for http://x")

    monkeypatch.setattr(ingest_cli.chicago_permits, "fetch_permits", exhausted)
    rc = ingest_cli.main(["permits", "--snapshot", "2026-07-06"])
    assert rc == 4


def test_permits_empty_pull_maps_to_1(offline_permits_env, monkeypatch):
    cols = list(ingest_cli.chicago_permits._PANEL_COLS)
    monkeypatch.setattr(ingest_cli.chicago_permits, "fetch_permits",
                        lambda *a, **k: pd.DataFrame(columns=cols))
    rc = ingest_cli.main(["permits", "--snapshot", "2026-07-06"])
    assert rc == 1


def test_cps_structural_validation_failure_maps_to_3(repo_cwd, monkeypatch):
    monkeypatch.setattr(ingest_cli.cps_boundaries, "verify_vintage_binding",
                        lambda *a, **k: {"name": "stub", "rowsUpdatedAt": 1})
    monkeypatch.setattr(ingest_cli.cps_boundaries, "fetch_boundary_geojson",
                        lambda *a, **k: {"type": "FeatureCollection", "features": []})
    rc = ingest_cli.main(["cps-boundaries", "--school-years", "SY2425",
                          "--levels", "elementary", "--snapshot", "2026-07-06"])
    assert rc == 3


def test_cps_future_vintage_is_user_error(repo_cwd):
    rc = ingest_cli.main(["cps-boundaries", "--school-years", "SY2526",
                          "--levels", "elementary", "--snapshot", "2024-07-06"])
    assert rc == 2


def test_isbe_bad_container_maps_to_3(repo_cwd, monkeypatch):
    def bad_container(*a, **k):
        raise ValueError("x: not a ZIP container")

    monkeypatch.setattr(ingest_cli.isbe_report_card, "fetch_report_card", bad_container)
    rc = ingest_cli.main(["isbe", "--years", "2018", "--snapshot", "2026-07-06"])
    assert rc == 3
