# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **H002 pre-registration FROZEN (2026-07-06)** via `/preregister`: the repeat-sales
  `boundary_side × period` DiD design
  ([design.md](research/01_hypothesis_register/H002/design.md), sha256
  `2ff817cb9fb6…`, immutable) with every `# TBD-at-freeze` resolved **outcome-blind**
  (§11.2 freeze-resolution record): elementary-only confirmatory universe,
  `q_top=10` (ISBE-Exemplary decile), qualification gap `G* = G_noise = 4.944`
  percentile pts (Kane–Staiger noise floor; Fisher/Jenks `G_break = 36.170` retained
  as the registered strong-gap sensitivity — revision rationale in the recipe §2.2),
  250 m boundary band, 182-day minimum holding (S&P CS convention after the
  registered changepoint rule failed on the realized distribution, documented),
  registered seed `20260706`. Binding full-fidelity power run (`WILD_B=399`,
  `N_REP=2000`, realized cluster structure): `n_required_for_power_80 = 1,105/side`
  vs realized low-side 1,718 — futility gate passes. Freeze ReproLog
  `repro_log_ac27dca8402e43a5846c26e1102b61d5.json`; multiple-testing family
  register H002 → `designed`. Freeze audited by quant + format specialists (the
  G* revision adjudicated "not outcome-adaptive").
- **H002 auxiliary ingestion connectors** (`src/lp_reit_lab/ingest/`): CPS
  attendance-boundary GeoJSON vintages SY0607–SY2526 × {elementary, high school}
  (pinned to per-school-year PARENT datasets — the catalog's legacy
  `visualization_canvas_map` wrapper ids truncate to a 53-byte skeleton; vintage
  name-binding asserted on every pull; CRS84 + Cook-bbox geometry gates), Chicago
  building permits `ydr8-5enu` (dual-arm pull: target community areas + null-CA
  rows inside the county bbox; count anchor + pre/post `rowsUpdatedAt` consistency
  checks), ISBE Report Card raw files rc2006–rc2025 (non-templatable canonical URLs
  pinned incl. the 2015–2017 `*-assessment` variants; per-file sha256 pins; Nov-1
  public-release knowability gate per 105 ILCS 5/10-17a), a shared deterministic
  Socrata pager, and provenance-manifest upgrades (replayable query records,
  dual-source lineage for joined artifacts, repo-relative path guard, dev-capped
  pulls excluded from provenance). Two audit-remediate rounds
  ([audit trail](docs/audits/audit_trail_2026-07-06_h002-ingestion-connectors.md)).
- **H002 feature/join pipeline** (`src/lp_reit_lab/h002/`): repeat-sale pair
  construction (CCAO class-2xx filter, same-day-deed dedup, class-change flag),
  Sep-1 school-year vintage calendar, STRtree boundary geometry (point-in-polygon
  side labels under the vintage in force per sale, adjacency segments = the design
  §5 cluster unit, local-equirectangular metric distances), building-permit
  renovation flags (building-level `pin10` join, frozen major-type set), and a
  20-vintage ISBE report-card parser (era-specific composite proficiency →
  within-year Hazen ranks per the
  [recipe memo](docs/methodology/methodology_isbe-quality-recipe_2026-07-06.md);
  COVID rc2020 carry-forward with staleness flag). Plus a **point-in-time leakage
  canary suite** (`tests/test_h002_pit_canary.py`) over every vintage/label/permit
  join surface (design §11.1 item 5).
- **Real-data landing (snapshot 2026-07-06, all keyless):** CCAO sales panel —
  137,189 arms-length sales / 124,745 parcels (community areas 6/7/8,
  byte-reproducible re-pull) — plus 40 boundary vintages, 116k+ permits, and 32
  ISBE files (437 MB). Validated per the validate-data skill
  ([report](data/validation_h002-freeze-inputs_2026-07-06.md); invariants in
  [data/expectations.yaml](data/expectations.yaml)); checksums frozen in
  [data/_manifest.json](data/_manifest.json). Boundary-school ↔ ISBE RCDTS
  crosswalk 55/55 matched, zero forced (Oscar Mayer verified top-decile);
  price-free freeze-evidence artifacts committed under `data/interim/` by explicit
  gitignore exception.
- **CITATION.cff:** 8 H002 method references mirrored via CrossRef (Black 1999;
  Bayer, Ferreira & McMillan 2007; Bailey–Muth–Nourse 1963; Cameron–Gelbach–Miller
  2008; Webb 2023; Conley 1999; Benjamini–Hochberg 1995; Bogin & Nguyen-Hoang 2014)
  with anti-fabrication guards enforced.
- `shapely`, `openpyxl`, `xlrd` (and previously `statsmodels`) as the `analysis`
  optional-dependency group.
- Open-data **ingestion layer** (`src/lp_reit_lab/ingest/`, ADR-0001): a Cook County
  Assessor Socrata connector (geography spine via `chicago_community_area_num`, batched
  `pin in(...)` sales), pandera no-look-ahead validation, integer-cents money + CPI
  deflation utilities, a content-addressed provenance manifest with source-version
  binding, and a `scripts/ingest.py` CLI. Audited via a 3-specialist loop
  (`docs/audits/audit_trail_2026-06-05_ingestion.md`).
- **Front-end consolidation (P0):** vendored the `north-side-property-compass`
  React/TypeScript SPA into `web/` (upstream `bff9b480cbf7`; provenance in
  `web/PROVENANCE.md`), stripped the Lovable telemetry sink and `.lovable/`
  scaffolding, and recorded the UI architecture in **ADR-0003** (React static SPA +
  precomputed Python artifacts + parity-gated TS deterministic-DCF mirror) with a
  plan memo (`docs/methodology/methodology_react-merge_2026-06-05.md`). Audited via a
  3-specialist loop (`docs/audits/audit_trail_2026-06-05_react-merge-p0.md`).
- **Web design-system pass (P1):** WCAG 2.1 AA verdict **text** tokens
  (`--*-strong`, computed by `scripts/wcag_contrast_audit.py` and pre-commit-gated),
  a light/dark theme toggle (no flash-of-wrong-theme), app-wide tabular figures, and
  an 8pt spacing token. De-Lovabled the Vite config (removed `@lovable.dev/*`; standard
  plugin stack; Cloudflare/Nitro opt-in via `NITRO_PRESET`).
- **Parity-gated TypeScript finance engine (P2):** `web/src/lib/engine/` mirrors the
  Python `evaluate_property` + `score_property`; the runtime config and golden-vector
  oracle are **generated** from the canonical `config/*.yaml` + engine by
  `scripts/export_web_engine_fixtures.py` (drift-gated by a pre-commit hook +
  `tests/test_web_engine_fixtures.py`); Vitest cross-checks TS↔Python within `rtol=1e-9`
  (observed max residual 6.6e-16). Replaced the magic-number `computeMetrics` mock.
- **Map + search (P3):** a `react-leaflet` map on free CARTO/OSM tiles (lazy,
  SSR-safe, theme-reactive) and a `@tanstack/react-table` screener with free-text
  search + sortable columns. Submarkets carry real WGS84 centroids; properties carry
  synthetic lat/lng (engine/parity unaffected).
- **Data contract + provenance (P4):** a single `DATA_SOURCE` / `DATA_PROVENANCE`
  swap boundary (`web/src/lib/data/source.ts`), per-section provenance captions +
  empty states, and a contract README (`web/src/lib/data/README.md`).
- **Forecast / Monte-Carlo artifact stub (P5):** the `ForecastArtifact` schema +
  a clearly-labelled illustrative sample rendered in the deal memo. The real
  compiler is **deferred** (pre-registration-governed) —
  `docs/methodology/methodology_forecast-artifact_2026-06-06.md`.
- Web test/tooling: Vitest; deps `leaflet`, `react-leaflet`, `@tanstack/react-table`.
  Each phase audited via the audit-remediate loop
  (`docs/audits/audit_trail_2026-06-06_{ui-p1-design-system,p2-dcf-mirror,p3-map-table,p4-data-contract,p5-forecast-stub}.md`).

### Changed
- The H002 power-analysis **rehearsal figures** (239/side at the assumed ρ=0.05,
  m̄=20) are retired: the binding full-fidelity run's freeze addendum in
  [power_analysis_2026-06-22.md](research/01_hypothesis_register/H002/power_analysis_2026-06-22.md)
  (1,105/side under realized cluster-structure priors) supersedes them.
- Established the web lint/format baseline: `.gitattributes` `eol=lf` for web source
  types, Prettier across `web/`, and eslint-ignored the generated `routeTree.gen.ts`.
- Superseded the **interactive-screener** portion of ADR-0002 (Streamlit) with
  **ADR-0003**; ADR-0002's Quarto-report, free-OSM-tile, and DRY shared-engine
  decisions remain in force.

### Fixed
- Identity hygiene (public pseudonymous repo): the user-level manifest builder now
  emits portable retriever ids — absolute Windows paths had embedded the OS
  username in every entry of the committed [data/_manifest.json](data/_manifest.json)
  — and session-trail `cwd` fields were relativized. Caught by the freeze-gate
  format audit before the freeze commit shipped.

### Removed
- Retired the v0 Streamlit screener (`app/streamlit_app.py`) and its smoke test;
  the user-facing UI is being replaced by the independent
  [north-side-property-compass](https://github.com/s-koirala/north-side-property-compass)
  app (merged separately). The shared finance/data engine (`src/lp_reit_lab`),
  synthetic generator, config, and Quarto report are unchanged.

## [0.0.1] - 2026-06-05

### Added
- Initial bootstrap via `/bootstrap-project --kind=quant`.
- Directory tree per SKIE-Universe canonical layout.
- `manifest.json` recording `bootstrap_script_git_head=608f5eb13c39`.
- Pre-commit hooks registered: ruff, nbstripout, nbqa, seed-guard, citation-cff, data-manifest-check.
- Market-scoping research memo (`docs/research_notes/research_market-scoping_2026-06-05.md`)
  — cited data-source register, econometric methods (hedonic, repeat-sales, DOM
  survival, spatial), the professional KPI hierarchy, and the Fair Housing
  compliance boundary. Audited via a 3-specialist audit-remediate loop; trails
  under `docs/audits/`.
- Architecture decisions: `docs/decisions/ADR-0001.md` (open/free-first data
  architecture) and `ADR-0002.md` (Streamlit + Quarto + OpenStreetMap stack).
- Hypothesis register seeded (H001–H004, status `proposed`) in `hypothesis_backlog.md`.
- v0 investment-screening **engine** on synthetic data (`src/lp_reit_lab`): finance
  module (NOI, cap rate, cash-on-cash, DSCR, GRM, OER, break-even occupancy, LTV,
  DCF pro forma, levered/unlevered IRR, NPV, capital-calls equity multiple),
  one-way sensitivity/tornado tables (`sensitivity.py`), config-driven assumptions
  and scoring bands (`config/`), a seeded synthetic data generator, and a
  parameterized Quarto deal memo (`reports/property_memo.qmd`).
- Test suite benchmarked against `numpy-financial` and closed-form references;
  `ruff` clean.
- Governance: extended `rules/quant-project.md` globs so quant time-series rules
  and the `quant-auditor` engage for this project path.
