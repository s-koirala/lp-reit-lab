# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- Established the web lint/format baseline: `.gitattributes` `eol=lf` for web source
  types, Prettier across `web/`, and eslint-ignored the generated `routeTree.gen.ts`.
- Superseded the **interactive-screener** portion of ADR-0002 (Streamlit) with
  **ADR-0003**; ADR-0002's Quarto-report, free-OSM-tile, and DRY shared-engine
  decisions remain in force.

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
