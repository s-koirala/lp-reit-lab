"""Content-addressed provenance manifest for ingested files.

Writes/reads an ingestion-specific manifest (default
`data/processed/_provenance/ingest_manifest.json`, tracked) recording {path, sha256,
source_url, snapshot_date, source_version, row_count, bytes} per raw API pull. This
is distinct from the committed-dataset `data/_manifest.json` managed by
`build_data_manifest.py`; raw API pulls are gitignored + regenerable, so their
provenance lives here (see ADR-0001). Stored paths are repo-relative POSIX, so
`check_drift` must run from the repo root.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_CHUNK = 1 << 20  # 1 MiB streaming read — bounded memory, not a tunable threshold


def sha256_file(path: str | Path) -> str:
    """Stream a file through SHA-256 and return the hex digest."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_entry(path: str | Path, *, source_url: str, snapshot_date: str,
                   row_count: int | None, source_version: str | None = None,
                   query: dict[str, Any] | None = None,
                   sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build one manifest record for an ingested file (POSIX path, content-addressed).

    `source_version` binds the snapshot to an observable upstream version (e.g. the
    Socrata `rowsUpdatedAt`, or an HTTP Last-Modified) so a drift result can be
    distinguished from a legitimate upstream restatement. `row_count` units: CSV
    data rows for tabular pulls, GeoJSON feature count for boundary files, and
    None for opaque binary artifacts (e.g. a raw ISBE workbook) whose row
    semantics belong to the analysis stage. `query` records the effective
    request parameters ($select/$where/$order, caps) so the pull is replayable
    from the manifest alone; `sources` lists every upstream dataset feeding a
    JOINED artifact ([{url, resource_id, source_version, role}, ...]) when one
    `source_url` cannot carry the full lineage.
    """
    p = Path(path)
    if p.is_absolute():
        # Absolute paths would embed the local user dir (an OS-username leak)
        # into a tracked file of a public pseudonymous repo.
        raise ValueError(f"manifest paths must be repo-relative, got {p}")
    entry: dict[str, Any] = {
        "path": p.as_posix(),
        "sha256": sha256_file(p),
        "source_url": source_url,
        "snapshot_date": snapshot_date,
        "source_version": source_version,
        "row_count": None if row_count is None else int(row_count),
        "bytes": p.stat().st_size,
    }
    if query is not None:
        entry["query"] = query
    if sources is not None:
        entry["sources"] = sources
    return entry


def write_manifest_atomic(manifest_path: str | Path, data: dict[str, Any]) -> None:
    """Write the manifest atomically (temp file + os.replace) to protect provenance.

    Canonical serialization: `files` sorted by path (re-pulls do not reshuffle
    entry order into spurious diffs) and a trailing newline (end-of-file-fixer
    hooks would otherwise mutate a committed manifest). NOT safe for concurrent
    ingest commands — read-modify-write callers can lose updates; run ingest
    commands sequentially.
    """
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if "files" in data:
        data = {**data, "files": sorted(data["files"], key=lambda f: f.get("path", ""))}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def write_bytes_atomic(path: str | Path, payload: bytes) -> None:
    """Write a landed artifact via .tmp sibling + os.replace (same-dir rename)."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, dest)


def check_drift(manifest_path: str | Path) -> list[tuple[str, str]]:
    """Return [(path, "MISSING"|"CHANGED")] for files diverging from the manifest.

    Paths are repo-relative; run from the repo root.
    """
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    drift: list[tuple[str, str]] = []
    for entry in data.get("files", []):
        p = Path(entry["path"])
        if not p.exists():
            drift.append((entry["path"], "MISSING"))
        elif sha256_file(p) != entry["sha256"]:
            drift.append((entry["path"], "CHANGED"))
    return drift
