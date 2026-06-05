# lp-reit-lab

Data pipeline and statistical models for evaluating Lincoln Park (Chicago) residential investment property on two axes: **long-run appreciation** and **net rental yield**.

A reproducible research toolkit for screening residential real estate in Lincoln Park and adjacent North Side Chicago neighborhoods (Lakeview, Old Town, DePaul, Sheffield/Wrightwood Neighbors, RANCH Triangle) as buy-and-hold investments. It ingests assessor, market, transit, school, and amenity data; fits hedonic price/rent models, a repeat-sales appreciation index, and a time-on-market survival model; and assembles a full carrying-cost stack to estimate cap rate, cash-on-cash, and tenant-fit for each candidate property. Hypotheses are pre-registered and FDR-corrected.

**Primary tenant thesis:** stable, dual-income, upper-middle-class families seeking 3BR+ units.

**Deliverables:** the shared finance/data **engine** (`src/lp_reit_lab`) plus parameterized, reproducible Quarto reports (per-property deal memos, neighborhood profiles, longitudinal market analyses), designed for a statistically-literate non-specialist via progressive disclosure (headline go/no-go → drill-down evidence). The interactive user-facing screener is a React/TypeScript SPA **vendored into [web/](web/)** (consolidated into this repo per [ADR-0003](docs/decisions/ADR-0003.md)): it renders precomputed Python-engine artifacts plus a parity-gated TypeScript mirror of the deterministic cash-flow math, and deploys statically (upstream provenance: [web/PROVENANCE.md](web/PROVENANCE.md)).

> **Fair Housing boundary.** Familial status is a protected class under the Fair Housing Act (42 U.S.C. §3604; 1988 Fair Housing Amendments Act). The "family tenant" thesis here is strictly **market-demand analysis** — which unit configurations and locations the market rewards with higher rent, occupancy, and appreciation — and is **never** a tenant-screening, steering, or advertising instrument. See the research memo under [docs/research_notes/](docs/research_notes/) for the compliance boundary.

## Status

| Field | Value |
|---|---|
| Kind | `quant` |
| Python | `3.11` |
| License | `MIT` |
| Bootstrap date | `2026-06-05` |
| Dotfiles HEAD | `608f5eb13c39` |

## Layout

```
lp-reit-lab/
├── src/                  # source-layout package
├── tests/                # pytest suite
├── scripts/              # one-shot entrypoints
├── notebooks/            # exploratory (stripped via nbstripout)
├── data/
│   ├── raw/              # read-only vendor pulls (gitignored)
│   ├── interim/          # lossy transforms (gitignored)
│   ├── processed/        # analysis-ready (gitignored)
│   └── external/         # reference data
├── docs/
│   ├── audits/           # audit-remediate-loop trails
│   ├── decisions/        # ADRs (Nygard/MADR)
│   ├── literature/       # primary-source PDFs + notes
│   ├── methodology/      # method memos, derivations
│   ├── reports/          # stakeholder-facing reports
│   ├── research_notes/   # dated memos
│   └── templates/        # reusable doc templates
├── artifacts/
│   ├── models/           # versioned model binaries
│   └── runs/             # run aggregate outputs
├── runs/                 # top-level run outputs (SKIE-Universe convention)
├── research/             # hypothesis-register / analysis-stage subdirs
├── reports/              # rendered reports
├── config/               # validated configs (pydantic / yaml)
├── logs/
│   └── reproducibility/  # ReproLog records + pip-freeze archive
├── outputs/              # scratch outputs (NOT artifacts)
├── web/                  # React/TS front-end SPA (vendored; see web/PROVENANCE.md)
├── CLAUDE.md             # project-local Claude rules
├── CHANGELOG.md          # Keep-a-Changelog 1.1.0
├── CITATION.cff          # CFF v1.2.0
├── LICENSE
├── pyproject.toml        # PEP 621
├── .gitignore
├── .pre-commit-config.yaml
└── manifest.json         # bootstrap reproducibility anchor
```

## Setup

```bash
# Create venv from project pyproject.toml
uv venv && uv sync

# Install pre-commit hooks (seed-guard, citation-cff)
uv run pre-commit install

# Run tests
uv run pytest

# Check data manifest integrity
python ~/.claude/scripts/build_data_manifest.py --check
```

## Running the v0 (synthetic data)

> **The v0 Streamlit screener has been retired** ([ADR-0003](docs/decisions/ADR-0003.md)).
> The user-facing UI is now the React/TypeScript SPA vendored under [web/](web/), which
> renders precomputed Python-engine artifacts. The shared finance/data engine
> (`src/lp_reit_lab`), the synthetic generator, and the Quarto report remain active.

```bash
# Sync env (runtime + dev tools), then (optionally) regenerate synthetic listings
uv sync --extra dev
uv run python scripts/generate_synthetic.py --n 150 --seed 20260605

# Per-property deal memo (requires the Quarto CLI: https://quarto.org)
quarto render reports/property_memo.qmd -P property_id:SYN-0001 --to html
```

> The v0 runs on **synthetic** data (`src/lp_reit_lab/synthetic.py`), calibrated to
> published area aggregates — **not real listings**. See the
> [market-scoping memo](docs/research_notes/research_market-scoping_2026-06-05.md)
> for methodology, data sources, and the Fair Housing compliance boundary
> (market-demand analysis only — never tenant screening/steering).

## Reproducibility

This project follows the 13-field ReproLog contract documented at
`~/.claude/skills/emit-repro-log/SKILL.md`. Every artifact-producing run
records:

- git HEAD
- pip freeze SHA-256 (full 64-hex, archived under `logs/reproducibility/env/`)
- dataset checksums from `data/_manifest.json`
- RNG seed
- model commit hash

Commits use `/commit-with-provenance --role=<role>` which emits
`Repro-Log-Path:` and `Repro-Log-SHA256:` trailers per ICMJE 2026 AI-assistance
disclosure.

## Citation

See [CITATION.cff](CITATION.cff) (CFF v1.2.0) for machine-readable citation
metadata. To add a reference to the bibliography:

```bash
# Via /cite-add slash command (resolves via CrossRef MCP)
/cite-add 10.1093/jamiaopen/ooy012
```

## Architecture decisions

See [docs/decisions/](docs/decisions/) for ADR records (Nygard/MADR format).
New decisions via `/adr-new "<title>"`.

## License

See [LICENSE](LICENSE).
