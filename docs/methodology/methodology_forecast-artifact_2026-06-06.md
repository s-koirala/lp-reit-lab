# Forecast / Monte-Carlo artifact — schema + governance (P5)

> **Status:** schema + stub only — the real compiler is deferred (see Governance).

## Contract

The SPA renders **precomputed** forecast/Monte-Carlo artifacts; it never computes
forecasts in the browser (ADR-0003 — forecasting/MC run in the Python venv where
`emit-repro-log` fires). The artifact shape is defined once, in TypeScript, at
[web/src/lib/forecast/artifact.ts](../../web/src/lib/forecast/artifact.ts)
(`ForecastArtifact`, schema v0.1.0):

- `status: "sample" | "fitted"` — the UI must never present a `sample` as a real
  forecast (it carries an "Illustrative sample · not fitted" badge + disclaimer).
- `appreciationPath[]` — cumulative-appreciation predictive bands (p10/p50/p90) per year.
- `monteCarlo` — `runs`, `fiveYearReturn` band, `terminalValue` band (`runs`/`generatedAt`
  are `null` for samples).
- `method`, `disclaimer`.

The stub view is [web/src/components/ForecastPanel.tsx](../../web/src/components/ForecastPanel.tsx),
wired into the property deal memo. It currently renders a `buildSampleForecast()`
artifact that merely compounds the property's expected/low/high appreciation —
**not a fitted model**.

## Governance — why the compiler is deferred

The real compiler (repeat-sales/hedonic index + Monte-Carlo terminal-value
simulation) is intentionally **not built yet**. It is gated on:

1. **Real data** — the ingestion lane (Cook County, FHFA, Zillow, ACS, Redfin).
2. **Pre-registration** — H001–H004 frozen via `/preregister` (immutable design.md +
   SHA) **before** fitting; a **prospective power analysis** at the registered
   alpha/power (retrospective/post-hoc power is forbidden —
   [Hoenig & Heisey 2001](https://doi.org/10.1198/000313001300339897)).
3. **Multiple-testing gate** — BH-FDR / Hansen SPA over the strategy family
   (rules/quant-project.md) so the forecast family is not silently p-hacked.
4. **Walk-forward + purge/embargo** and point-in-time inputs (no look-ahead).

## Swap when it lands

The compiler emits `status: "fitted"` artifacts of this exact schema (one JSON per
property/submarket), committed like the engine fixtures. `ForecastPanel` renders
them unchanged; `buildSampleForecast` is replaced by an artifact loader following
the [data-source boundary](../../web/src/lib/data/source.ts) pattern, and the
sample badge/disclaimer are removed.
