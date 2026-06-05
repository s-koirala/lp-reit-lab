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
                   row_count: int, source_version: str | None = None) -> dict[str, Any]:
    """Build one manifest record for an ingested file (POSIX path, content-addressed).

    `source_version` binds the snapshot to an observable upstream version (e.g. the
    Socrata `rowsUpdatedAt`) so a drift result can be distinguished from a legitimate
    upstream restatement.
    """
    p = Path(path)
    return {
        "path": p.as_posix(),
        "sha256": sha256_file(p),
        "source_url": source_url,
        "snapshot_date": snapshot_date,
        "source_version": source_version,
        "row_count": int(row_count),
        "bytes": p.stat().st_size,
    }


def write_manifest_atomic(manifest_path: str | Path, data: dict[str, Any]) -> None:
    """Write the manifest atomically (temp file + os.replace) to protect provenance."""
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


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
