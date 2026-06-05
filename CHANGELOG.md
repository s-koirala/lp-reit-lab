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
