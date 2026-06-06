# Audit trail — P2: TS deterministic-DCF mirror + parity gate

- **Date:** 2026-06-06
- **Artifact:** `web/src/lib/engine/` (TS finance engine), `scripts/export_web_engine_fixtures.py` (oracle/exporter), `web/src/lib/data/properties.ts` (adapter), parity test + drift guards.
- **Loop:** audit-remediate — 2 rounds (cap 3). Exit: zero critical+major.
- **Acceptance:** replace the magic-number `computeMetrics` mock with a TypeScript mirror of the Python finance engine (`src/lp_reit_lab/finance`), parity-gated by golden vectors (rtol from observed residual); no real data/models required (deterministic engine already exists).

## Design

The Python engine is the single source of truth. `export_web_engine_fixtures.py` generates **both** the TS runtime config (`config.generated.json`) and the parity oracle (`__fixtures__/golden_vectors.json`) from `config/{assumptions,scoring}.yaml` + the engine — so no YAML/engine value is hand-copied into TS (the P1 "duplicated literals" lesson). Drift is gated by a pre-commit hook + `tests/test_web_engine_fixtures.py`. IRR is excluded from the parity contract (numpy_financial root selection is non-reproducible for sign-changing cash-flow-negative streams; the engine's own docstring favours NPV); NPV, equity multiple, pro forma, reversion, single-period metrics, carry stack, and scoring are all gated. Observed max parity residual **6.6e-16** (~3 ULP); RTOL 1e-9 (matches the Python `rel=1e-9` discipline).

## Round 1 — auditors: quant-auditor, code-reviewer, reproducibility-verifier, format-auditor

(`literature-check` skipped: P2 introduces no new method claims — it mirrors the already-cited, already-audited Python engine.)

| # | Sev | Source | Finding | Disposition |
|---|---|---|---|---|
| 1 | major | quant | Appreciation terminal-basis branch (NOI≤0 reversion fallback) not exercised by any golden vector (all 10 → exit-cap) | **Fixed:** added an NOI-negative case (2.0M/1.4k/1.5k); `terminal_basis` now {exit-cap×10, appreciation×1}, parity-tested |
| 2 | major | code-reviewer | `netRentYield === capRate` shown under two labels; "after carrying costs" caption misreads cap rate as net-of-debt | **Fixed:** deal memo → single "Going-in cap rate (NOI÷price, pre-debt)"; screener table → distinct Cap + CoC columns; masthead → "Avg cap rate, operating pre-debt" |
| 3 | major | code-reviewer | `computeMetrics` throws on non-positive inputs; no guard in index/neighborhoods/map render paths (fragile for P3/P4 real data) | **Fixed:** fail-closed guard returns a NO-GO sentinel for non-positive price/rent |
| 4 | major | repro | Pre-commit drift hook `files:` regex omitted `scoring.py`/`config.py` (real oracle inputs) | **Fixed:** regex broadened to all engine inputs |
| 5 | minor | quant | NaN/null representation (equity_multiple NaN vs Python null) untested | **Fixed:** test harmonizes null/NaN |
| 6 | minor | quant | Pure-relative tolerance lacks an absolute floor for near-zero fields | **Fixed:** combined `|a-e| ≤ atol + rtol·|e|` (atol=1e-9) |
| 7 | minor | code-reviewer | `SCORING` double-cast (`as unknown as`) hid a `rules_of_thumb` structural mismatch | **Fixed:** added optional `rules_of_thumb` to `ScoringBands`; single cast |
| 8 | minor | code-reviewer | dead `unleveredCfs` computed but unused | **Fixed:** removed (unlevered IRR is Python-only) |
| 9 | minor | code-reviewer | test casts erase typed surface → silent coverage loss on rename | **Fixed:** per-key existence assertion added |
| 10 | minor | code-reviewer | 0-GO landing state unexplained | **Fixed:** masthead caveat ("appreciation-led; most screen NO-GO by design") |
| 11 | minor | repro | generated JSON written CRLF on Windows vs eol=lf | **Fixed:** byte-exact LF read/write |
| 12 | minor | format | `blendedScore` ranking weights unjustified magic numbers | **Fixed:** provisional comment; config migration flagged for P4/P5 |
| 13 | minor | format | methodology §01/§02 "90%/80%" intervals vs ±6%/±8% synthetic bands; §01–04 read as live | **Fixed:** band copy corrected; live-vs-planned lede added |
| — | minor | repro | dist is SSR (no index.html) vs "static" deploy target | **Deferred** (deploy concern; logged P1) |

Identity hygiene: clean. All numeric constants confirmed vs the (already-audited) Python engine; max residual 6.6e-16.

## Round 2 — confirmation: quant-auditor

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 2-1 | minor | Appreciation-branch coverage now present but not *pinned* — a future CASES edit could silently de-cover it | **Fixed:** both sides assert both terminal bases are represented (`engine.test.ts` + `tests/test_web_engine_fixtures.py`) |

Confirmed: parity 13/13, residual 6.6e-16, appreciation `sale_price` spot-checked vs Python (5.4e-16), no regression, de-dup semantics correct, guard inert for valid inputs.

## Verification (final)

`bunx tsc --noEmit` 0 · `bun run lint` 0 errors · `bun run test` 13/13 · `bun run build` 0 → dist/client+server · `uv run pytest -q` 54 · `uv run ruff check` 0 · exporter `--check` deterministic (byte-identical twice).

## Residual / deferred

- `blendedScore` ranking weights: migrate to a cited `config/scoring.yaml` `ranking` block (P4/P5).
- SSR-vs-static dist: deploy-time concern (Cloudflare nitro preset), not P2.
- IRR remains Python-only by design.
- Not committed (loop scope); the new `web/src/lib/engine/` tree + scripts/tests must be staged atomically.
