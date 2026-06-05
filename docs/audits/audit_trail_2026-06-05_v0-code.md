# Audit Trail — v0 deliverable code

| Field | Value |
|---|---|
| Artifact | `src/lp_reit_lab/**`, `app/streamlit_app.py`, `scripts/generate_synthetic.py`, `config/*.yaml`, `tests/**` |
| Pattern | audit-remediate-loop (parallel-specialist ensemble), 3-round cap |
| Round | 1 (exited — both majors per auditor remediated; residual minors dispositioned) |
| Auditors | code-reviewer, quant-auditor, reproducibility-verifier (parallel) |
| Date | 2026-06-05 |
| Gate state | ruff (E,F,W,I,N,B,UP,SIM,PL) clean; 28 pytest pass (finance vs numpy-financial; Streamlit AppTest smoke) |

## Major findings — all remediated
| ID | Auditor | Issue | Disposition |
|---|---|---|---|
| CR-major-1 | code-reviewer | `reversion()` exit-cap method produced a spurious **negative sale price for non-positive projected NOI** (reachable for cash-flow-negative LP draws) | **Fixed** — fall back to appreciation-based terminal value when NOI≤0; record `terminal_basis`; test added |
| CR-major-2 | code-reviewer | `irr()` had a dead `value is not None` guard (npf.irr never returns None) + undocumented multiple-root behavior | **Fixed** — dropped the dead clause; docstring now discloses smallest-magnitude-root selection and points to NPV for ranking |
| QN-major-1 | quant-auditor | Property tax grown smoothly vs the documented **triennial** Cook County reassessment | **Fixed** — documented as a deliberate smoothing approximation in `opex_for_year`/module docstrings |
| QN-major-2 | quant-auditor | Synthetic universe is ~99.6% NO-GO → GO/WATCH scoring path untested end-to-end; integration assertion tautological | **Fixed** — added end-to-end GO test, a WATCH test, and a test locking the "intentionally mostly NO-GO" calibration; synthetic docstring annotated |

## Minor findings — dispositions
| ID | Issue | Disposition |
|---|---|---|
| CR-min, QN-F1-5 | `remaining_balance` lacked the guards its sibling has (0/0 path) | **Fixed** — `ValueError` on years≤0 / loan<0 |
| CR-min | `equity_multiple` had no zero-denominator guard | **Fixed** — returns NaN when total equity in ≤ 0 |
| QN-F1-3 | Fixed-cost inflation conflated with rent growth | **Fixed** — added cited `cost_inflation_annual` config field (CPI proxy), decoupled |
| QN-F1-4 | HOA + utilities double-count trap (water bundled in HOA) | **Fixed** — `operating_expenses` docstring states caller owns dedup (inert at config default) |
| QN-F1-7 | Unused `upfront_rehab` param implied unsupported capability | **Fixed** — removed; documented to add rehab to both bases together with real data |
| QN-F1-8 | `_LIGHT_SCORE` map hardcoded despite "no magic numbers" claim | **Fixed** — moved to `config/scoring.yaml::composite.light_scores` |
| QN-F1-6 | Interior remaining-balance not benchmarked | **Fixed** — month-84 test vs `numpy_financial.fv` |
| QN-F1-9 | `rules_of_thumb` config unconsumed | **Fixed** — annotated as reserved for the UI/report Tier-3 layer |
| RV-min-1 | Provenance sidecar written to gitignored `data/interim/` | **Fixed** — moved to tracked `data/processed/_provenance/`; corrected `.gitignore` negation (`data/processed/*`) |
| RV-min-2 | Manifest stored OS-native (Windows) path | **Fixed** — `as_posix()` |
| RV-min-4 | Manifest omitted toolchain versions | **Fixed** — records numpy + pandas versions |
| CR-min | `load_yaml` returned None on empty file vs `dict` contract | **Fixed** — raises `ValueError` on non-mapping |
| CR-min | `collections.namedtuple` weaker than typed alternative | **Fixed** — `typing.NamedTuple` for `_Hood` |

## Accepted residual (non-gating)
- **TypedDict return types** for `evaluate_property`/`score_property` (code-reviewer): hygiene, non-gating; deferred.
- **Config-coupled math tests** (QN-F1-10): math tests load live `config/*.yaml`; acceptable for v0, pin to fixtures before real-data work.
- **Full 13-field ReproLog** (RV-min-3): the synthetic-generation manifest is a documented lightweight subset; full ReproLog via emit-repro-log is required for non-synthetic (artifact-producing) runs.
- **`main()` without `__name__` guard** in the Streamlit entrypoint: standard for `streamlit run`; kept so AppTest exercises the full script.

## Residual risk
Core finance math is benchmarked to machine precision vs numpy-financial; the
remediated negative-NOI reversion, IRR root disclosure, and division guards close
the reachable correctness gaps. Remaining exposure is intrinsic to v0 scope: the
deliverable runs on synthetic data (no econometric models fit), and full
reproducibility/ReproLog + TypedDict hardening land before real-data ingestion.
