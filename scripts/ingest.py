"""CLI: pull an open-data source into data/raw, validate, and record provenance.

Raw bytes land under data/raw/ (gitignored, regenerable); a content-addressed,
atomically-written provenance record goes to
data/processed/_provenance/ingest_manifest.json (tracked). Validation uses the
pandera schema (no-look-ahead gate). Run from the repo root.

Exit codes (uniform across subcommands): 0 = ok, 1 = empty result,
2 = user/argument error, 3 = validation failure (schema, structural gate,
count-anchor or version-consistency mismatch), 4 = transport failure.

Provenance rules: dev-capped pulls (--max-*) NEVER write manifest entries (a
truncated pull must not masquerade as a full one); each entry records the
effective query so the pull is replayable from the manifest alone; joined
artifacts list every upstream source; Socrata versions (`rowsUpdatedAt`) are
captured BEFORE the pull and re-checked after (mid-pull upstream mutation
fails loudly). Manifest updates are batched once per command; on any non-zero
exit NO manifest entries are written, so files landed by a failed run stay
unprovenanced until a successful re-run overwrites them (raw/ is gitignored
and regenerable, so the orphan cost is a re-run, not lost provenance).

Usage:
  uv run python scripts/ingest.py cook-county --year 2024 --since 2015-01-01 \
      [--snapshot YYYY-MM-DD] [--max-pins N] [--max-sales N]
  uv run python scripts/ingest.py cps-boundaries [--school-years SY0607,SY0708] \
      [--levels elementary,high_school] [--snapshot YYYY-MM-DD]
  uv run python scripts/ingest.py permits [--since 2006-01-01] [--snapshot YYYY-MM-DD] \
      [--max-rows N]
  uv run python scripts/ingest.py isbe [--years 2018,2019] [--snapshot YYYY-MM-DD]
  uv run python scripts/ingest.py manifest-check
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandera.errors  # noqa: E402
import requests  # noqa: E402

from lp_reit_lab.ingest.config import (  # noqa: E402
    PERMITS_EPOCH,
    ChicagoPortalConfig,
    SocrataConfig,
    SocrataDomain,
)
from lp_reit_lab.ingest.http_client import build_session, get_json  # noqa: E402
from lp_reit_lab.ingest.manifest import (  # noqa: E402
    check_drift,
    manifest_entry,
    write_bytes_atomic,
    write_manifest_atomic,
)
from lp_reit_lab.ingest.schemas import (  # noqa: E402
    building_permits_schema,
    property_sales_schema,
)
from lp_reit_lab.ingest.socrata import soql_count  # noqa: E402
from lp_reit_lab.ingest.sources import (  # noqa: E402
    chicago_permits,
    cook_county,
    cps_boundaries,
    isbe_report_card,
)

_MANIFEST = Path("data/processed/_provenance/ingest_manifest.json")

_TRANSPORT_ERRORS = (requests.exceptions.RequestException, OSError)


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _require_repo_root() -> None:
    if not (Path.cwd() / "pyproject.toml").exists():
        _err("run from the repo root (pyproject.toml not found in cwd)")
        raise SystemExit(2)  # user error per the module exit-code contract


def _parse_snapshot(raw: str | None) -> str:
    snapshot = raw or datetime.now(UTC).date().isoformat()
    date.fromisoformat(snapshot)
    return snapshot


def _source_version(session: requests.Session, soc: SocrataDomain,
                    resource_id: str) -> str | None:
    """Socrata `rowsUpdatedAt` — binds the snapshot to an observable dataset version.

    Returns None (with a stderr warning) when the metadata endpoint is
    unreachable or carries no version — callers must treat None as
    UNVERIFIED, never as "consistent" (audit F-2-4/CR-2-3).
    """
    try:
        meta = get_json(session, soc.metadata_url(resource_id))
    except (requests.exceptions.RequestException, ValueError):
        _err(f"warning: version signal unavailable for {resource_id}; "
             "consistency check degraded")
        return None
    value = meta.get("rowsUpdatedAt") if isinstance(meta, dict) else None
    return None if value is None else str(value)


def _versions_mutated(pre: str | None, post: str | None) -> bool:
    """True only when BOTH observations exist and differ; None = unverified."""
    if pre is None or post is None:
        if pre != post or pre is None:
            _err("warning: upstream version unverifiable (missing observation); "
                 "binding degrades to sha/count controls")
        return False
    return pre != post


def _update_manifest(entries: list[dict[str, Any]]) -> None:
    """Merge entries into the manifest (replace-by-path), one atomic write."""
    if not entries:
        return
    if _MANIFEST.exists():
        try:
            data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise OSError(f"corrupt manifest at {_MANIFEST.as_posix()}: {exc}") from exc
    else:
        data = {"files": []}
    new_paths = {e["path"] for e in entries}
    files = [f for f in data.get("files", []) if f.get("path") not in new_paths]
    files.extend(entries)
    data["files"] = files
    write_manifest_atomic(_MANIFEST, data)


def _csv_bytes(panel) -> bytes:
    """Serialize a frame to CSV bytes (deterministic; written atomically)."""
    return panel.to_csv(index=False, lineterminator="\n").encode("utf-8")


def cmd_cook_county(args: argparse.Namespace) -> int:
    _require_repo_root()
    soc = SocrataConfig()
    token = os.environ.get("SOCRATA_APP_TOKEN")   # optional; raises the rate limit
    try:
        snapshot = _parse_snapshot(args.snapshot)
        date.fromisoformat(args.since)
    except ValueError as exc:
        _err(f"invalid ISO date: {exc}")
        return 2
    dev_capped = args.max_pins is not None or args.max_sales is not None

    session = build_session()
    pre_versions = {
        "universe": _source_version(session, soc, soc.parcel_universe_id),
        "sales": _source_version(session, soc, soc.parcel_sales_id),
    }
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
    except _TRANSPORT_ERRORS as exc:
        _err(f"ingestion failed: {exc}")
        return 4
    if panel.empty:
        _err("0 sales after assembly; nothing written")
        return 1
    post_versions = {
        "universe": _source_version(session, soc, soc.parcel_universe_id),
        "sales": _source_version(session, soc, soc.parcel_sales_id),
    }
    if not dev_capped and any(
        _versions_mutated(pre_versions[k], post_versions[k]) for k in pre_versions
    ):
        _err(f"upstream version changed mid-pull: {pre_versions} -> {post_versions}; "
             "re-run for a consistent snapshot")
        return 3

    try:
        out_dir = Path("data/raw/cook_county") / f"snapshot={snapshot}"
        csv_path = out_dir / "sales_panel.csv"
        write_bytes_atomic(csv_path, _csv_bytes(panel))
        if not dev_capped:
            entry = manifest_entry(
                csv_path, source_url=soc.resource_url(soc.parcel_sales_id),
                snapshot_date=snapshot, row_count=int(len(panel)),
                source_version=pre_versions["sales"],
                query={"since": args.since, "snapshot": snapshot, "year": args.year,
                       "geography": "chicago_community_area_num in (6,7,8)",
                       "arms_length_filters": "CCAO sale_filter_* legacy flags",
                       "order": ":id", "page_size": soc.page_size},
                sources=[
                    {"url": soc.resource_url(soc.parcel_sales_id),
                     "resource_id": soc.parcel_sales_id,
                     "source_version": pre_versions["sales"], "role": "sales"},
                    {"url": soc.resource_url(soc.parcel_universe_id),
                     "resource_id": soc.parcel_universe_id,
                     "source_version": pre_versions["universe"],
                     "role": f"geography spine (tax year {args.year})"},
                ],
            )
            _update_manifest([entry])
            sha_note = f"sha256={entry['sha256'][:12]}"
        else:
            sha_note = "DEV-CAPPED: no manifest entry"
    except OSError as exc:
        _err(f"write failed: {exc}")
        return 4
    print(f"ingested {len(panel)} sales across {universe['pin'].nunique()} parcels "
          f"-> {csv_path.as_posix()} ({sha_note}, source_version={pre_versions['sales']})")
    return 0


def cmd_cps_boundaries(args: argparse.Namespace) -> int:
    _require_repo_root()
    portal = ChicagoPortalConfig()
    token = os.environ.get("SOCRATA_APP_TOKEN")
    try:
        snapshot = _parse_snapshot(args.snapshot)
    except ValueError as exc:
        _err(f"invalid ISO date: {exc}")
        return 2
    years = ([t.strip() for t in args.school_years.split(",")] if args.school_years
             else cps_boundaries.school_years())
    levels = ([t.strip() for t in args.levels.split(",")] if args.levels
              else list(cps_boundaries.LEVELS))
    unknown_years = [y for y in years if y not in cps_boundaries.school_years()]
    if unknown_years:
        _err(f"unknown school years: {unknown_years}")
        return 2
    unknown_levels = [lv for lv in levels if lv not in cps_boundaries.LEVELS]
    if unknown_levels:
        _err(f"unknown levels: {unknown_levels} (expected {list(cps_boundaries.LEVELS)})")
        return 2
    snapshot_year = int(snapshot[:4])
    # A vintage cannot be knowable before its school year begins (boundaries
    # publish ahead of the fall term); coarse floor = Jan 1 of the SY start year.
    not_knowable = [y for y in years if cps_boundaries.sy_start_year(y) > snapshot_year]
    if not_knowable:
        _err(f"vintages {not_knowable} not knowable at snapshot {snapshot}")
        return 2

    session = build_session()
    out_dir = Path("data/raw/cps_boundaries") / f"snapshot={snapshot}"
    entries: list[dict[str, Any]] = []
    for school_year in years:
        for level in levels:
            resource_id = cps_boundaries.resource_id_for(school_year, level)
            try:
                meta = cps_boundaries.verify_vintage_binding(
                    session, school_year, level, app_token=token
                )
                geojson = cps_boundaries.fetch_boundary_geojson(
                    session, school_year, level, app_token=token
                )
                cps_boundaries.validate_feature_collection(
                    geojson, school_year=school_year, level=level
                )
            except ValueError as exc:
                _err(f"{level} {school_year} ({resource_id}) validation failed: {exc}")
                return 3
            except _TRANSPORT_ERRORS as exc:
                _err(f"{level} {school_year} ({resource_id}) failed: {exc}")
                return 4
            version = meta.get("rowsUpdatedAt")
            try:
                path = out_dir / f"{level}_{school_year}.geojson"
                # canonicalization raises ValueError on non-finite floats
                # (allow_nan=False) -> validation exit, not a traceback (F-2-3)
                write_bytes_atomic(path, cps_boundaries.canonical_geojson_bytes(geojson))
                entries.append(manifest_entry(
                    path, source_url=portal.geospatial_export_url(resource_id),
                    snapshot_date=snapshot, row_count=len(geojson["features"]),
                    source_version=None if version is None else str(version),
                    query={"school_year": school_year, "level": level,
                           "upstream_name": meta.get("name"),
                           "serialization": "canonical (sorted features/keys)"},
                ))
            except ValueError as exc:
                _err(f"{level} {school_year} serialization failed: {exc}")
                return 3
            except OSError as exc:
                _err(f"write failed: {exc}")
                return 4
            print(f"{level} {school_year}: {len(geojson['features'])} features "
                  f"-> {path.as_posix()} (sha256={entries[-1]['sha256'][:12]})")
    try:
        _update_manifest(entries)
    except OSError as exc:
        _err(f"manifest update failed: {exc}")
        return 4
    print(f"cps-boundaries: {len(entries)} vintage files landed under {out_dir.as_posix()}")
    return 0


def cmd_permits(args: argparse.Namespace) -> int:
    _require_repo_root()
    portal = ChicagoPortalConfig()
    token = os.environ.get("SOCRATA_APP_TOKEN")
    try:
        snapshot = _parse_snapshot(args.snapshot)
        date.fromisoformat(args.since)
    except ValueError as exc:
        _err(f"invalid ISO date: {exc}")
        return 2
    dev_capped = args.max_rows is not None

    session = build_session()
    url = portal.resource_url(portal.building_permits_id)
    pre_version = _source_version(session, portal, portal.building_permits_id)
    try:
        wheres = chicago_permits.permit_where_clauses(args.since, snapshot)
        expected = (None if dev_capped else
                    sum(soql_count(session, url, where=w, app_token=token)
                        for w in wheres))
        raw = chicago_permits.fetch_permits(
            session, since=args.since, snapshot=snapshot,
            app_token=token, max_rows=args.max_rows,
        )
        panel = chicago_permits.assemble_permits(raw)
        if panel.empty:
            _err("0 permits returned; nothing written")
            return 1
        building_permits_schema(snapshot).validate(panel, lazy=True)
    except pandera.errors.SchemaErrors as exc:
        _err(f"schema validation failed:\n{exc.failure_cases}")
        return 3
    except ValueError as exc:
        _err(f"validation failed: {exc}")
        return 3
    except _TRANSPORT_ERRORS as exc:
        _err(f"ingestion failed: {exc}")
        return 4
    # Count anchor catches inserts/deletes; the post-pull version recheck
    # catches count-PRESERVING in-place revisions (audit F-2-1) — both needed.
    post_version = _source_version(session, portal, portal.building_permits_id)
    if not dev_capped:
        if len(panel) != expected:
            _err(f"count anchor mismatch: server count {expected} != assembled "
                 f"{len(panel)} (upstream mutated mid-pull); re-run")
            return 3
        if _versions_mutated(pre_version, post_version):
            _err(f"upstream version changed mid-pull: {pre_version} -> {post_version}; "
                 "re-run for a consistent snapshot")
            return 3

    try:
        out_dir = Path("data/raw/chicago_permits") / f"snapshot={snapshot}"
        csv_path = out_dir / "building_permits.csv"
        write_bytes_atomic(csv_path, _csv_bytes(panel))
        if not dev_capped:
            entry = manifest_entry(
                csv_path, source_url=url, snapshot_date=snapshot,
                row_count=int(len(panel)), source_version=pre_version,
                query={"since": args.since, "snapshot": snapshot,
                       "where_arms": wheres, "order": ":id",
                       "page_size": portal.page_size, "server_count": expected},
            )
            _update_manifest([entry])
            sha_note = f"sha256={entry['sha256'][:12]}"
        else:
            sha_note = "DEV-CAPPED: no manifest entry"
    except OSError as exc:
        _err(f"write failed: {exc}")
        return 4
    print(f"ingested {len(panel)} permits -> {csv_path.as_posix()} "
          f"({sha_note}, source_version={pre_version})")
    return 0


def cmd_isbe(args: argparse.Namespace) -> int:
    _require_repo_root()
    try:
        snapshot = _parse_snapshot(args.snapshot)
        years = ([int(y) for y in args.years.split(",")] if args.years else None)
    except ValueError as exc:
        _err(f"invalid argument: {exc}")
        return 2
    knowable = isbe_report_card.years_knowable_at(snapshot)
    if years is None:
        years = knowable
    if not years:
        _err(f"no report-card years knowable at snapshot {snapshot}")
        return 1
    not_knowable = [y for y in years if y not in knowable]
    if not_knowable:
        _err(f"report-card years {not_knowable} not knowable at snapshot {snapshot} "
             "(released ~Nov 1 of the rc year, or year unconfigured)")
        return 2

    session = build_session()
    out_dir = Path("data/raw/isbe_report_card") / f"snapshot={snapshot}"
    entries: list[dict[str, Any]] = []
    for rc_year in years:
        try:
            files = isbe_report_card.fetch_report_card(session, rc_year, out_dir)
        except ValueError as exc:
            _err(f"rc{rc_year} validation failed: {exc}")
            return 3
        except _TRANSPORT_ERRORS as exc:
            _err(f"rc{rc_year} failed: {exc}")
            return 4
        for f in files:
            try:
                entry = manifest_entry(
                    f.path, source_url=f.url, snapshot_date=snapshot,
                    row_count=None, source_version=f.last_modified,
                )
            except OSError as exc:
                _err(f"manifest entry failed: {exc}")
                return 4
            if entry["sha256"] != f.sha256:
                _err(f"rc{rc_year}: on-disk sha {entry['sha256'][:12]} != streamed "
                     f"sha {f.sha256[:12]} — disk corruption?")
                return 3
            entries.append(entry)
            print(f"rc{rc_year}: {f.path.name} ({f.n_bytes} bytes, "
                  f"sha256={f.sha256[:12]}, last_modified={f.last_modified})")
    try:
        _update_manifest(entries)
    except OSError as exc:
        _err(f"manifest update failed: {exc}")
        return 4
    print(f"isbe: {len(entries)} files landed under {out_dir.as_posix()}")
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

    cb = sub.add_parser("cps-boundaries",
                        help="Pull CPS attendance-boundary GeoJSON vintages.")
    cb.add_argument("--school-years", type=str, default=None,
                    help="Comma-joined SY labels (e.g. SY0607,SY0708); default all.")
    cb.add_argument("--levels", type=str, default=None,
                    help="Comma-joined levels (elementary,high_school); default both.")
    cb.add_argument("--snapshot", type=str, default=None,
                    help="As-of date (ISO); default today (UTC).")
    cb.set_defaults(func=cmd_cps_boundaries)

    pm = sub.add_parser("permits", help="Pull Chicago building permits (target CAs).")
    pm.add_argument("--since", type=str, default=PERMITS_EPOCH,
                    help="Earliest issue date (ISO); default dataset epoch.")
    pm.add_argument("--snapshot", type=str, default=None,
                    help="As-of date (ISO); default today (UTC). No-look-ahead bound.")
    pm.add_argument("--max-rows", type=int, default=None, help="Dev cap on rows pulled.")
    pm.set_defaults(func=cmd_permits)

    ib = sub.add_parser("isbe", help="Download ISBE Report Card public data sets.")
    ib.add_argument("--years", type=str, default=None,
                    help="Comma-joined rc years (e.g. 2018,2019); default all knowable.")
    ib.add_argument("--snapshot", type=str, default=None,
                    help="As-of date (ISO); default today (UTC). Gates knowable years.")
    ib.set_defaults(func=cmd_isbe)

    mc = sub.add_parser("manifest-check", help="Fail on data drift vs the ingest manifest.")
    mc.set_defaults(func=cmd_manifest_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
