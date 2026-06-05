"""CLI: regenerate the synthetic listing set + a provenance sidecar.

Writes a CSV (gitignored data/interim) plus a small manifest recording seed,
SHA-256, git HEAD, and row count. The synthetic set is reproducible from the
seed, so the data itself is not committed (research memo §9, §11).

Usage:  uv run python scripts/generate_synthetic.py --n 150 --seed 20260605
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy
import pandas

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lp_reit_lab.synthetic import SYNTHETIC_NOTICE, generate_listings  # noqa: E402


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic LP listings (UI scaffolding).")
    parser.add_argument("--n", type=int, default=150)
    parser.add_argument("--seed", type=int, default=20260605)
    parser.add_argument("--out", type=Path, default=Path("data/interim/synthetic_listings.csv"))
    args = parser.parse_args(argv)

    frame = generate_listings(args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)

    sha = hashlib.sha256(args.out.read_bytes()).hexdigest()
    manifest = {
        "notice": SYNTHETIC_NOTICE,
        "n": args.n,
        "seed": args.seed,
        "output": args.out.as_posix(),
        "sha256": sha,
        "git_head": _git_head(),
        "rows": int(len(frame)),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "note": ("Lightweight provenance subset; the full 13-field ReproLog "
                 "(emit-repro-log) is required for non-synthetic artifact runs (memo §11)."),
    }
    # Manifest goes to a tracked location (data/processed/_provenance is un-ignored);
    # the CSV itself stays gitignored and is regenerable from the seed.
    prov_dir = Path("data/processed/_provenance")
    prov_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = prov_dir / f"{args.out.stem}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {len(frame)} rows -> {args.out.as_posix()} "
          f"(sha256={sha[:12]}; manifest {manifest_path.as_posix()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
