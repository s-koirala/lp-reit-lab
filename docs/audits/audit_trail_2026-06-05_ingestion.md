# Audit Trail — ingestion layer (Cook County Assessor)

| Field | Value |
|---|---|
| Artifact | `src/lp_reit_lab/ingest/**`, `scripts/ingest.py`, `tests/test_ingest_*.py` |
| Pattern | audit-remediate-loop (parallel-specialist ensemble), 3-round cap |
| Round | 1 (exited — all 4 criticals + 8 majors remediated; residuals dispositioned) |
| Auditors | code-reviewer, quant-auditor, reproducibility-verifier (parallel) |
| Date | 2026-06-05 |
| Gate state | ruff clean; 52 pytest pass; live connectivity verified (`:id` order, real CCAO rows) |

## Critical — all remediated
| Issue | Disposition |
|---|---|
| `assemble_panel` `KeyError` on empty sales (`from_records([])` is column-less) | **Fixed** — `fetch_sales_for_pins` builds a column-bearing frame; `assemble_panel` early-returns a canonical empty panel; test added |
| SoQL injection — Socrata PINs + free-form `--since` interpolated into `$where` unescaped | **Fixed** — `_valid_pins` drops non-`^\d{14}$` PINs before interpolation; CLI validates `--since`/`--snapshot` via `date.fromisoformat`; test added |
| Non-unique sales `$order` (`sale_date`) → unstable pagination + non-deterministic CSV byte order (breaks SHA idempotency) | **Fixed** — `$order=:id` (total order) for sales + universe; panel stably sorted before `to_csv`; CSV pinned (`lineterminator="\n"`, utf-8) |
| Ingest manifest disjoint from the hook-watched `data/_manifest.json` (ingestion outside the drift gate) | **Fixed/Documented** — docstrings reconciled; ADR-0001 documents the raw-pull manifest vs committed-dataset manifest split; CI wiring of `manifest-check` noted as follow-on |

## Major — all remediated
| Issue | Disposition |
|---|---|
| `Int64` (connector) vs `int64` (schema) dtype divergence; no end-to-end schema test | **Fixed** — schema `sale_price` → `Int64`; added `assemble_panel → property_sales_schema` integration test |
| `lat`/`latitude` duplicate columns | **Fixed** — `rename` (drop `lat`/`lon`); test asserts no duplicates |
| CLI: no exception handling, ambiguous exit codes, empty-panel path | **Fixed** — try/except (`SchemaErrors`, `RequestException`, `OSError`) → stderr + distinct exit codes (1–4); empty-panel branch |
| Wall-clock-only snapshot; no replay; no source-version binding | **Fixed** — `--snapshot/--as-of` arg; manifest records Socrata `rowsUpdatedAt` as `source_version` |
| No-look-ahead gate: same-day/NaT/`doc_no` | **Fixed** — inclusive same-day documented + boundary test; `nullable=False` rejects NaT; `doc_no` carried for downstream dedup |
| `deflate` cpi_base unguarded; `price_per_sqft` NaN sqft passes | **Fixed** — positivity guard on cpi_base; `not (sqft>0) or not isfinite` guard; tests added |
| Cents-vs-whole-USD money convention disconnect | **Fixed (documented)** — `money.py` clarified as downstream cents toolkit; ingested `sale_price` stays int64 USD; `__init__` docstring reconciled |

## Minor — fixed
Boundary comment (`> 10000` vs `<= 10000` flag); pagination knobs moved to `config`;
atomic manifest write (temp + `os.replace`); `_update_manifest` typed; CCAO filter-flag
citation; `class`-collision guard comment; `manifest-check` asserts repo-root cwd.

## Accepted residual (round-1; next round / follow-on)
- `doc_no` carried but the gate key remains the (pin, sale_date, sale_price) surrogate
  — promote to a `doc_no`-based key in a later round.
- `source_version` binds the snapshot, but full vintage **replay** of a prior pull still
  depends on the mutable upstream; documented.
- `ingest_manifest.json` is not yet wired into CI (ADR-0001 follow-on).
- `money.py` helpers are not yet consumed by the pipeline (downstream-utility by design).
- Full-geography live pull times out on the public endpoint without `SOCRATA_APP_TOKEN`
  (operational; connector + unit tests verified, read timeout raised to 120s).

## Residual risk
Pure functions, the no-look-ahead gate, and the panel-assembly/SoQL-safety paths are
unit-tested and the connector is live-verified for connectivity; byte-level re-pull
idempotency now holds within an upstream vintage (`:id` order + pinned CSV + sort),
with `source_version` distinguishing drift from legitimate CCAO restatement.
