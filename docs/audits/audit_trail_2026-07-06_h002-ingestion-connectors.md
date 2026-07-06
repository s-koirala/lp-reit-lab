# Audit trail — H002 auxiliary ingestion connectors (2026-07-06)

Audit-remediate loop over the H002 open-data ingestion layer: CPS
attendance-boundary vintages (SY0607–SY2526, elementary + high school),
Chicago building permits ([ydr8-5enu](https://data.cityofchicago.org/resource/ydr8-5enu)),
ISBE Report Card raw files (rc2006–rc2025), plus the shared Socrata pager,
HTTP download path, provenance manifest, and CLI
([scripts/ingest.py](../../scripts/ingest.py)).

Pattern: parallel-specialist ensemble per
[audit-remediate-loop](https://github.com/s-koirala/dotfiles) — round 1 =
quant-auditor + code-reviewer + reproducibility-verifier + format-auditor
(4 parallel branches); round 2 = quant-auditor + code-reviewer verification
pass. Cap 3 rounds; exited after round-2 remediation with only
deferred-by-design minors open.

## Round 1 — findings and dispositions

| ID | Sev | Finding (abbrev.) | Disposition (round 1 remediation) |
|----|-----|-------------------|------------------------------------|
| F-1-1 | critical | 26/40 CPS vintage ids (SY0607–SY1819) are `visualization_canvas_map` wrappers; geospatial export truncates to a 53-byte skeleton | FIXED — re-pinned to parent dataset UIDs resolved via `api/views/{id}.json → displayFormat.visualizationCanvasMetadata.vifs[].series[].dataSource.datasetUid`; wrappers retained in `CPS_BOUNDARY_WRAPPERS` (provenance only); disjointness pinned by test; SY0607 elementary re-pull landed 401 features, byte-stable (sha `533a4a124a6e`) |
| F-1-2 / FA-1-2 | major | ISBE knowability gated on school-year end (June) though the data set releases ~late October → Jul–Oct leak window | FIXED — gate is now the public-release floor (Nov 1 of rc year N; 105 ILCS 5/10-17a Oct-31 statutory preparation deadline + observed 2024-10-30 release); tests assert 2025 NOT knowable at 2025-10-15, knowable at 2025-11-01 |
| F-1-3 | major | No content-to-vintage binding (CPS names unchecked; ISBE 2018 URL undated and mutable) | FIXED — `verify_vintage_binding` asserts upstream dataset name contains SY token + level BEFORE each pull (exit 3 on mismatch); all 20 ISBE data files pinned by sha256 in config (re-pull mismatch fails loudly; restatement = explicit re-pin) |
| F-1-4 | major | No CRS / coordinate-range validation on boundary geometry | FIXED — legacy `crs` member must name CRS84/EPSG:4326; every coordinate must fall in the Cook County lon/lat envelope (projected-CRS tripwire); State-Plane fixture test |
| F-1-10 | major | 35/40 vintage ids unverified upstream | CLOSED — live 40/40 sweep: every pinned id's metadata name matches its school year + level (2026-07-06); binding now also enforced at every pull (F-1-3) |
| CR-1-1 | major | `TransientHTTPError(Exception)` escapes every CLI transport handler on retry exhaustion | FIXED — subclasses `requests.exceptions.RequestException`; taxonomy test |
| CR-1-2..5 | major | Unclosed file handle; `--years` parse outside exit-2 path; ValueError lumped into exit 4; unguarded write/manifest phase | FIXED — context managers; parse inside try; ValueError→3 vs transport→4 split; OSError→4 around serialization + manifest; `_update_manifest` maps JSONDecodeError→OSError |
| RV-1 | major | Query parameters not recorded → pull not replayable from manifest; dev-capped pulls indistinguishable | FIXED — `query` record per entry (since/snapshot/where/order/page size/server count); `--max-*` pulls write NO manifest entries |
| RV-2 | major | Joined sales panel records single source | FIXED — `sources` list (sales + geography spine with per-source `rowsUpdatedAt`) |
| FA-1-1 | major | ISBE comment overclaimed an 18-URL HEAD sweep against 32 pinned URLs | FIXED — comment states the stronger fact: all 32 files downloaded + container-validated, shas pinned |
| minors (19) | minor | Epoch wording drift; RCDTS source; sleep/RFC citations; APPNOTE naming; repo-relative path guard; manifest sort/newline/batching; row-count units; TOCTOU version capture; Last-Modified capture; TypedDict/Literal typing; LandedFile; `_parse_snapshot` reuse; SocrataDomain base; explode_pin10 token semantics (pipe-separated upstream, 14→prefix, 11–13 drop); null-safe id cast; isinstance-dict guard; SchemaErrors assertions; pager/download/CLI test coverage; split arg errors | ALL FIXED in round 1 (see diff); permits additionally pull a second arm (`community_area is null` within bbox) per F-1-5 so geocoding gaps cannot silently unflag renovated pairs |

## Round 2 — verification pass

- code-reviewer: **pass** — all 17 CR-1 fixes verified in place; 11 polish
  minors (exit-2 for wrong cwd, dtype-safe id cast, fail-open version
  handling, batched-manifest failure semantics documented, Literal
  annotations, no-op re-export removed, fast retry test, importlib spec
  asserts, `Any` annotations, isbe empty-knowable→1, count-anchor hardening)
  — ALL applied post-verdict.
- quant-auditor: **remediate** — 1 major + 4 minors; all 8 remediation claims
  otherwise verified live (4 legacy parents re-probed as true datasets;
  `asie-aked` rowsUpdatedAt matches the landed manifest; two-arm permits
  probed full-epoch: 65,857/75,055 null-CA rows recovered by the bbox arm).

| ID | Sev | Finding | Disposition |
|----|-----|---------|-------------|
| F-2-1 | major | `cmd_permits` had the count anchor but no post-pull `rowsUpdatedAt` recheck — count-preserving in-place revisions undetectable | FIXED — post-pull version recheck added (mirrors cook-county); count anchor + version check both required; `_versions_mutated` treats missing observations as UNVERIFIED (warn), never as consistent |
| F-2-2 | minor | Empty-coordinates feature passes vacuously; non-dict feature → AttributeError | FIXED — isinstance guard + RFC 7946 §3.1.6 ring minimum (≥4 positions) |
| F-2-3 | minor | `allow_nan=False` ValueError escaped the CLI as a traceback | FIXED — ValueError→3 handler on the serialization block |
| F-2-4 | minor | `_source_version` fail-open (None==None passes) and silent | FIXED — stderr warnings; None = unverified |
| F-2-5 | minor | sha pins cannot retro-validate the pin-time landing (esp. undated 2018 URL) | **DEFERRED to freeze sweep** — one-time in-file year-marker assertion at parse stage (h002/isbe.py integration test partially covers; freeze audit records it) |

Post-remediation state: `uv run ruff check src scripts tests` clean;
`uv run --extra analysis pytest tests/ -q` → **127 passed** (offline; no
network in any unit test).

## Residual risk

1. **Upstream restatement irreducibility** — Socrata has no time travel; a
   restated dataset cannot reproduce recorded sha256s. Controls make drift
   ATTRIBUTABLE (rowsUpdatedAt pre/post, sha pins, count anchors), not
   reversible. Mitigation at freeze: commit the ingest manifest and archive
   the landed raw snapshots before `data/_manifest.json` checksums freeze.
2. **Null-CA permits without coordinates or `pin_list`** (~9.2k city-wide over
   the epoch; ≤283 carry `pin_list`) are unjoinable to parcels without address
   geocoding — quantify the target-CA share at freeze; largely irreducible.
3. **ISBE pin-time identity** (F-2-5) — year-marker parse assertion queued for
   the freeze sweep.
4. **pin10 building-level permit join** over-flags condo units for
   building/neighbour works — conservative direction (sample loss, not
   contamination); quantified at freeze.
