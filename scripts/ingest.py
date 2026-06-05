"""CLI: pull an open-data source into data/raw, validate, and record provenance.

Raw bytes land under data/raw/ (gitignored, regenerable); a content-addressed,
atomically-written provenance record goes to
data/processed/_provenance/ingest_manifest.json (tracked). Validation uses the
pandera schema (no-look-ahead gate). Run from the repo root.

Usage:
  uv run python scripts/ingest.py cook-county --year 2024 --since 2015-01-01 \
      [--snapshot YYYY-MM-DD] [--max-pins N] [--max-sales N]
  uv run python scripts/ingest.py manifest-check
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandera.errors  # noqa: E402
import requests  # noqa: E402

from lp_reit_lab.ingest.config import SocrataConfig  # noqa: E402
from lp_reit_lab.ingest.http_client import build_session, get_json  # noqa: E402
from lp_reit_lab.ingest.manifest import (  # noqa: E402
    check_drift,
    manifest_entry,
    write_manifest_atomic,
)
from lp_reit_lab.ingest.schemas import property_sales_schema  # noqa: E402
from lp_reit_lab.ingest.sources import cook_county  # noqa: E402

_MANIFEST = Path("data/processed/_provenance/ingest_manifest.json")


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _require_repo_root() -> None:
    if not (Path.cwd() / "pyproject.toml").exists():
        raise SystemExit("run from the repo root (pyproject.toml not found in cwd)")


def _source_version(session: requests.Session, soc: SocrataConfig, resource_id: str) -> str | None:
    """Socrata `rowsUpdatedAt` — binds the snapshot to an observable dataset version."""
    try:
        meta = get_json(session, soc.metadata_url(resource_id))
    except (requests.exceptions.RequestException, ValueError):
        return None
    value = meta.get("rowsUpdatedAt") if isinstance(meta, dict) else None
    return None if value is None else str(value)


def _update_manifest(entry: dict[str, object]) -> None:
    if _MANIFEST.exists():
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    else:
        data = {"files": []}
    files = [f for f in data.get("files", []) if f.get("path") != entry["path"]]
    files.append(entry)
    data["files"] = files
    write_manifest_atomic(_MANIFEST, data)


def cmd_cook_county(args: argparse.Namespace) -> int:
    _require_repo_root()
    soc = SocrataConfig()
    token = os.environ.get("SOCRATA_APP_TOKEN")   # optional; raises the rate limit
    snapshot = args.snapshot or datetime.now(UTC).date().isoformat()
    try:
        date.fromisoformat(args.since)
        date.fromisoformat(snapshot)
    except ValueError as exc:
        _err(f"invalid ISO date: {exc}")
        return 2

    session = build_session()
    try:
        universe = cook_county.fetch_parcel_universe(
            session, args.year, app_token=token, max_rows=args.max_pins
        )
        if universe.empty:
            _err("no parcels returned for the target geography")
            return 1
        sales = cook_county.fetch_sales_for_pins(
            session, universe["pin"].tolist(), args.since,
            app_token=token, max_rows=args.max_sales,
        )
        panel = cook_county.assemble_panel(universe, sales)
        property_sales_schema(snapshot).validate(panel, lazy=True)
    except pandera.errors.SchemaErrors as exc:
        _err(f"schema validation failed:\n{exc.failure_cases}")
        return 3
    except (requests.exceptions.RequestException, OSError) as exc:
        _err(f"ingestion failed: {exc}")
        return 4

    if panel.empty:
        _err("0 sales after assembly; nothing written")
        return 1

    out_dir = Path("data/raw/cook_county") / f"snapshot={snapshot}"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "sales_panel.csv"
    panel.to_csv(csv_path, index=False, lineterminator="\n", encoding="utf-8")

    version = _source_version(session, soc, soc.parcel_sales_id)
    entry = manifest_entry(
        csv_path, source_url=soc.resource_url(soc.parcel_sales_id),
        snapshot_date=snapshot, row_count=int(len(panel)), source_version=version,
    )
    _update_manifest(entry)
    print(f"ingested {len(panel)} sales across {universe['pin'].nunique()} parcels "
          f"-> {csv_path.as_posix()} (sha256={entry['sha256'][:12]}, source_version={version})")
    return 0


def cmd_manifest_check(_: argparse.Namespace) -> int:
    _require_repo_root()
    if not _MANIFEST.exists():
        print(f"no manifest at {_MANIFEST.as_posix()}")
        return 0
    drift = check_drift(_MANIFEST)
    for path, reason in drift:
        _err(f"DRIFT {reason}: {path}")
    return 1 if drift else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open-data ingestion CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    cc = sub.add_parser("cook-county", help="Pull Cook County Assessor sales panel.")
    cc.add_argument("--year", type=int, default=2024, help="Parcel-universe tax year.")
    cc.add_argument("--since", type=str, default="2015-01-01", help="Earliest sale date (ISO).")
    cc.add_argument("--snapshot", type=str, default=None,
                    help="As-of date (ISO); default today (UTC). Bounds the no-look-ahead gate.")
    cc.add_argument("--max-pins", type=int, default=None, help="Dev cap on parcels pulled.")
    cc.add_argument("--max-sales", type=int, default=None, help="Dev cap on sales pulled.")
    cc.set_defaults(func=cmd_cook_county)

    mc = sub.add_parser("manifest-check", help="Fail on data drift vs the ingest manifest.")
    mc.set_defaults(func=cmd_manifest_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
