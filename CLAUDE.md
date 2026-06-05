# lp-reit-lab — Project-Local Rules

Inherits all user-global rules from `~/.claude/CLAUDE.md` plus the imported
cwd-scoped rule file: `rules/quant-project.md` (activated automatically when this
project's path matches the rule's cwd globs).

## Scope

Quant research project. Hypothesis-driven; pre-registered design.md per hypothesis; walk-forward backtest with purge + embargo; Hansen SPA gate over the strategy family.

## Reproducibility contract

Every artifact-producing run in this project emits a 13-field ReproLog at
`logs/reproducibility/repro_log_{run_id}.json` per the
[emit-repro-log](https://github.com/s-koirala/dotfiles/tree/main/claude/skills/emit-repro-log)
skill. All commits use
[/commit-with-provenance](https://github.com/s-koirala/dotfiles/tree/main/claude/commands/commit-with-provenance.md)
with `--role={idea|code|prose|audit|multi}` per ICMJE 2026 disclosure.

Dataset provenance: `data/_manifest.json` (managed by
`~/.claude/scripts/build_data_manifest.py`). Run `--check` mode in CI to
detect drift.

## Quickstart

```bash
uv venv && uv sync
uv run pre-commit install
uv run pytest
```

## Project state

- **Kind:** quant
- **Bootstrap date:** 2026-06-05
- **Python version pin:** `3.11`
- **Bootstrap script HEAD:** `608f5eb13c39` (see `manifest.json`)

## Directory layout

See `manifest.json` for the canonical subdir list. Key conventions:

- `data/{raw,interim,processed,external}/` — read-only raw → analysis-ready
  pipeline; per-file SHA in `data/_manifest.json`.
- `docs/{audits,decisions,literature,methodology,reports,research_notes,templates}/`
  — durable documentation.
- `artifacts/{models,runs}/` — versioned binary outputs.
- `logs/reproducibility/` — ReproLog records + pip-freeze archive.
- `research/`, `reports/` — work-in-progress and final reports.
- `runs/` — top-level run outputs (SKIE-Universe convention; coexists with
  `artifacts/runs/`).

## Identity hygiene

This project's local git config sets `user.email` per the bootstrap. Real-name
identifiers must never appear in committed files unless explicitly intended.
