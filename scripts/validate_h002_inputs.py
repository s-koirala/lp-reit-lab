"""validate-data over the H002 freeze inputs (skill checks 2-5 + report).

Re-asserts the ingest-time gates independently (schema via pandera, PK
uniqueness, date ordering, business rules from data/expectations.yaml) and
emits per-column distribution summaries. No prior snapshot exists, so drift
(PSI/KS) is N/A for this first vintage. Output:
data/validation_h002-freeze-inputs_{date}.md. Exit non-zero on any critical
failure (the downstream gate).
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lp_reit_lab.ingest.config import ISBE_REPORT_CARD_FILES  # noqa: E402
from lp_reit_lab.ingest.manifest import sha256_file  # noqa: E402
from lp_reit_lab.ingest.schemas import (  # noqa: E402
    building_permits_schema,
    property_sales_schema,
)
from lp_reit_lab.ingest.sources import cps_boundaries  # noqa: E402

SNAPSHOT = "2026-07-06"
RAW = Path("data/raw")
# Invariants live in data/expectations.yaml (validate-data skill §5), not here.
EXPECT = yaml.safe_load(Path("data/expectations.yaml").read_text(encoding="utf-8"))
_ARMS_FLOOR = EXPECT["cook_county_sales_panel"]["arms_length_floor"]
_TARGET_CAS = set(EXPECT["cook_county_sales_panel"]["community_areas"])
_N_BOUNDARY_FILES = EXPECT["cps_boundaries"]["files"]
_N_ISBE_FILES = EXPECT["isbe_report_card"]["files"]
_DATE_ORDER_MIN = EXPECT["chicago_permits"]["date_order_min_share"]
failures: list[str] = []
lines: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    lines.append(f"- **{mark}** {name}{': ' + detail if detail else ''}")
    if not ok:
        failures.append(name)


def summarize(frame: pd.DataFrame, cols: list[str]) -> str:
    rows = []
    for c in cols:
        s = frame[c]
        desc = {"col": c, "n": len(s), "missing": int(s.isna().sum()), "dtype": str(s.dtype)}
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s):
            desc["min"], desc["max"] = str(s.min()), str(s.max())
        else:
            desc["top5"] = ", ".join(f"{k}({v})" for k, v in s.value_counts().head(5).items())
        rows.append(desc)
    return "```\n" + pd.DataFrame(rows).to_string(index=False) + "\n```"


# --- 1. sales panel ---------------------------------------------------------
# doc_no is a string identifier that read_csv would re-infer as int64 when a
# panel's values happen to be all-numeric — declare it, like pin/class.
sales = pd.read_csv(RAW / f"cook_county/snapshot={SNAPSHOT}/sales_panel.csv",
                    dtype={"pin": str, "class": str, "doc_no": str,
                           "chicago_community_area_num": str},
                    parse_dates=["sale_date"])
lines.append("## cook_county sales_panel\n")
try:
    property_sales_schema(SNAPSHOT).validate(sales, lazy=True)
    check("sales pandera schema", True, f"{len(sales)} rows")
except Exception as exc:  # pandera SchemaErrors
    check("sales pandera schema", False, str(exc)[:200])
check("sales PK unique (pin, sale_date, sale_price)",
      not sales.duplicated(["pin", "sale_date", "sale_price"]).any())
check("sales arms-length floor", bool((sales["sale_price"] > _ARMS_FLOOR).all()))
check("sales CAs in {6,7,8}",
      set(sales["chicago_community_area_num"].dropna()) <= _TARGET_CAS)
lines.append("\n" + summarize(sales, ["sale_date", "sale_price", "latitude",
                                      "longitude", "class"]) + "\n")

# --- 2. permits --------------------------------------------------------------
permits = pd.read_csv(RAW / f"chicago_permits/snapshot={SNAPSHOT}/building_permits.csv",
                      dtype={"id": str, "community_area": str, "pin_list": str,
                             "census_tract": str, "ward": str},
                      parse_dates=["issue_date", "application_start_date"])
lines.append("## chicago_permits\n")
try:
    building_permits_schema(SNAPSHOT).validate(permits, lazy=True)
    check("permits pandera schema", True, f"{len(permits)} rows")
except Exception as exc:
    check("permits pandera schema", False, str(exc)[:200])
check("permits PK unique (id)", not permits["id"].duplicated().any())
ca = permits["community_area"]
check("permits CA null-or-target", bool(ca.dropna().isin(sorted(_TARGET_CAS)).all()),
      f"null share {ca.isna().mean():.3f}")
check("permits date ordering (application <= issue) where both present",
      bool((permits.dropna(subset=["application_start_date"])["application_start_date"]
            <= permits.dropna(subset=["application_start_date"])["issue_date"]
            ).mean() > _DATE_ORDER_MIN),
      "tolerating <1% upstream entry reversals (expectations.yaml)")
lines.append("\n" + summarize(permits, ["issue_date", "reported_cost", "community_area",
                                        "latitude", "longitude"]) + "\n")

# --- 3. boundaries -----------------------------------------------------------
lines.append("## cps_boundaries\n")
bdir = RAW / f"cps_boundaries/snapshot={SNAPSHOT}"
files = sorted(bdir.glob("*.geojson"))
check("boundary vintage file count", len(files) == _N_BOUNDARY_FILES, f"found {len(files)}")
feature_counts = {}
for f in files:
    gj = json.loads(f.read_text(encoding="utf-8"))
    level, sy = f.stem.rsplit("_", 1)
    try:
        cps_boundaries.validate_feature_collection(gj, school_year=sy, level=level)
        feature_counts[f.stem] = len(gj["features"])
    except ValueError as exc:
        check(f"boundary structural gate {f.stem}", False, str(exc)[:150])
check("boundary structural gates (all 40)", len(feature_counts) == len(files))
elem = {k: v for k, v in feature_counts.items() if k.startswith("elementary")}
hs = {k: v for k, v in feature_counts.items() if k.startswith("high_school")}
lines.append(f"\nelementary features/vintage: min {min(elem.values())}, "
             f"max {max(elem.values())}; high_school: min {min(hs.values())}, "
             f"max {max(hs.values())}\n")

# --- 4. ISBE -----------------------------------------------------------------
lines.append("## isbe_report_card\n")
idir = RAW / f"isbe_report_card/snapshot={SNAPSHOT}"
ifiles = sorted(idir.iterdir())
check("ISBE file count", len(ifiles) == _N_ISBE_FILES, f"found {len(ifiles)}")
pin_ok = all(
    sha256_file(idir / f"rc{y}_{Path(spec['data']).name}") == spec["sha256"]
    for y, spec in ISBE_REPORT_CARD_FILES.items()
)
check("ISBE data files match config sha pins (20/20)", pin_ok)

# --- report ------------------------------------------------------------------
report = Path(f"data/validation_h002-freeze-inputs_{SNAPSHOT}.md")
header = (
    f"# validate-data — H002 freeze inputs ({SNAPSHOT})\n\n"
    f"Generated {datetime.now(UTC).isoformat(timespec='seconds')} by "
    f"[scripts/validate_h002_inputs.py](../scripts/validate_h002_inputs.py). "
    "Provenance: [ingest_manifest.json](processed/_provenance/ingest_manifest.json); "
    "invariants: [expectations.yaml](expectations.yaml). Drift vs prior snapshot: "
    "N/A (first vintage).\n\n"
)
report.write_text(header + "\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(f"report -> {report}")
print("FAILURES:", failures if failures else "none")
sys.exit(1 if failures else 0)
