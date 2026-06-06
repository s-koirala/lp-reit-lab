# Audit trail — P5: forecast/MC artifact schema + SPA stub

- **Date:** 2026-06-06
- **Artifact:** `web/src/lib/forecast/artifact.ts`, `web/src/components/ForecastPanel.tsx`, `web/src/routes/property.$id.tsx`, `docs/methodology/methodology_forecast-artifact_2026-06-06.md`.
- **Loop:** audit-remediate — 2 rounds (cap 3). Auditor: format-auditor (right-sized: P5 is a stub whose dominant risk is honesty/overclaim, not numerical method — there is no fitted model to audit).
- **Acceptance:** define the forecast/MC artifact schema (contract) + a SPA view rendering a clearly-labelled illustrative sample. The real compiler is **deferred** (pre-registration-governed; needs real data).

## Deliverables

- **Schema/contract:** `ForecastArtifact` (v0.1.0) — `status: "sample"|"fitted"`, `appreciationPath` (p10/p50/p90 bands), `monteCarlo` (`runs`/`generatedAt` null for samples), method/disclaimer.
- **Sample + stub:** `buildSampleForecast()` compounds the property's appreciation band (deterministic, status "sample"); `ForecastPanel` renders it in the deal memo with an "Illustrative sample · not fitted" badge + disclaimer + a band chart + outcome tiles.
- **Governance doc:** the four deferral gates (real data; pre-registration of H001–H004 + prospective power analysis; multiple-testing gate; walk-forward/purge/embargo) and the swap-when-it-lands procedure.

## Round 1 findings + disposition (format-auditor)

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | major | Outcome tiles (the 6 most quotable numbers) carried no inline not-fitted qualifier — screenshot-in-isolation could read as real | **Fixed:** a "no Monte-Carlo run — bands compound the appreciation estimate" caption attached directly to the tile block |
| 2 | major | The `monteCarlo`-framed sample bands are deterministic (no simulation); `runs=null` encoded it in data but not visibly | **Fixed:** same tile caption makes the no-simulation state explicit on-screen (schema keeps `monteCarlo` for the real artifact) |
| 3 | minor | `horizonYears=5` unjustified | **Fixed:** comment anchoring it to the appreciation5y CAGR window |
| 4 | minor | band color `oklch(0.55 0.12 220)` hardcoded (== `--ring`) | **Fixed:** → `var(--ring)` |
| 5 | minor | Hoenig & Heisey cited author-year only | **Fixed:** DOI link added |
| 6 | minor | doc status line used invalid `/ … /` markdown | **Fixed:** → blockquote |

format-auditor: governance framing correct & complete (prospective power, not post-hoc; MT gate; no-look-ahead); identity hygiene clean; Fair-Housing framing intact; sample math directionally correct; no fabricated "fitted" parameters.

## Verification (final, whole project)

WEB: `tsc` 0 · `lint` 0 errors · `test` 13/13 · `build` 0 · `bun install --frozen-lockfile` no drift.
PY: `pytest` 54 · `ruff` 0 · `wcag --assert` 0 · engine-fixtures `--check` clean.

## Residual / deferred

- The real forecast/MC compiler is **deferred** by design (pre-registration-governed) — this phase ships only the schema + an illustrative stub.
- `var(--ring)` band token: the same blue literal still appears in the P2/P3 deal-memo charts; a full chart-color tokenization is a deferred DRY cleanup.
- Not committed (loop scope); new files (`forecast/artifact.ts`, `ForecastPanel.tsx`, the methodology doc) staged atomically.
