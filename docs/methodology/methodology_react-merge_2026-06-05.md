# Methodology Memo — React-base UI merge + retrospective/projection time-series

| Field | Value |
|---|---|
| Document | `methodology_react-merge_2026-06-05.md` |
| Author | SKIE (`s-koirala`) |
| Date | 2026-06-05 |
| Status | v1 — plan frozen for execution; P0 in progress (audit-remediate round 1) |
| Project kind | quant (`rules/quant-project.md`) |
| Decision record | [ADR-0003](../decisions/ADR-0003.md) (supersedes the screener portion of [ADR-0002](../decisions/ADR-0002.md)) |
| Reporting discipline | Time-series integrity (no look-ahead, walk-forward, HAC inference, multiple-testing gate); TRIPOD-style transparency for predictive models; hypotheses pre-registered before fit |
| AI-assistance | Drafted with Claude (Opus 4.8). Evidence base: 8 parallel research agents across two rounds (time-series/finance math, free-data sources, prior-art/AVM cautions, Streamlit eng [round 1]; design principles, assumption-control UX, shadcn/Recharts/map impl, integration architecture [round 2]) + audit-remediate loop. See README AI-assistance note. |

> **Scope.** This memo specifies the merge of the rigorous Python analytics engine
> into the Lovable-generated React app (the aesthetic base), plus property search
> and a retrospective + projection time-series feature. It supersedes the
> Streamlit-host plan. MVP = phases **P0–P4**; the forecasting/Monte-Carlo layer
> (**P5**) is the governed heavyweight phase and is deferrable.

---

## 1. Purpose and the pivot

The product is a decision-support screener for buy-and-hold residential acquisition
in Lincoln Park / North Side Chicago, scored on two estimands (long-run
appreciation; net rental yield) — see [research memo](../research_notes/research_market-scoping_2026-06-05.md).

The pivot recorded in [ADR-0003](../decisions/ADR-0003.md): the **front-end base is
the React app**, not Streamlit. Streamlit is retired as a UI (the v0 screener is
already removed; commit `455fd10`). The Python engine is **not** discarded — its
role splits into (i) a build-time artifact compiler and (ii) the source of truth
for a parity-gated TypeScript deterministic mirror.

The Lovable app's `web/src/lib/data/properties.ts::computeMetrics` is **discarded**:
it encodes exactly the magic numbers the project forbids (`maintenance*0.008`,
`vacancy*0.06`, verdict cuts `0.045`/`0.032`, blended weights `0.55/0.45`), and its
`expectedAppreciation` ("5y CAGR ± 0.012") is the naive extrapolation documented to
fail (Glaeser & Nathanson 2017; the Zillow Offers post-mortem). Math comes from the
Python engine; the React app supplies presentation only.

## 2. Architecture (the hybrid)

Cut along the deterministic/statistical seam — see [ADR-0003](../decisions/ADR-0003.md)
for the full rationale and the rejected alternatives (Pyodide, live API, full TS
port).

- **Build-time (Python venv):** tested engine + forecasting (statsmodels VECM /
  state-space; arch bootstrap) + Monte-Carlo → versioned static artifacts
  (`per_property_metrics.json`, `scenario_grid.parquet`, `forecast_dist.parquet`,
  `mc_summary.json`, `golden_vectors.json`), each stamped with its ReproLog
  `run_id`.
- **Client:** TS mirror of **only** the deterministic functions of
  [metrics.py](../../src/lp_reit_lab/finance/metrics.py) +
  [cashflow.py](../../src/lp_reit_lab/finance/cashflow.py) for instant slider
  recompute; forecast/MC rendered from precomputed artifacts.
- **Parity gate:** Python generates `golden_vectors.json`; pytest **and** Vitest
  assert against it with an `rtol` derived from the observed cross-runtime residual.
  Required edge cases: zero-rate amortization; the cash-flow-negative
  exit-cap→appreciation reversion fallback; the multiple-IRR-root stream (rank by
  NPV). Divergence ⇒ red build.
- **Hosting:** static Cloudflare Pages.

## 3. Design system (evidence-based; keep the oklch base)

Keep the React app's mature Tailwind v4 `@theme` oklch token system
([web/src/styles.css](../../web/src/styles.css)); refine, do not rebuild. All
tokens trace to a system (no design "magic numbers").

- **Spacing:** 8 pt grid `{4,8,16,24,32,48,64}` (Material 8 dp rationale: divisibility, 2× displays). Map to Tailwind tokens.
- **Type:** Minor-Third 1.2 modular scale; `font-variant-numeric: lining-nums tabular-nums` on **every** aligned figure (table cells, axis ticks, tooltips — currently inconsistent); prose measure 45–75 ch.
- **Color/accessibility:** Okabe-Ito (2008) categorical palette; ColorBrewer/viridis for sequential/diverging; never color-alone (redundant sign/arrow/label — also covers grayscale Quarto print). WCAG 2.2 AA, CI-gated: **4.5:1** text, **3:1** large-text / chart-marks / UI bounds. Two concrete fixes: `--muted-foreground` at 10 px, and verdict colors used as *text* (`--watch` at L 0.72 fails 4.5:1) → add darker `*-foreground` variants for text, keep bright fills.
- **Charts:** position/length encodings (Cleveland & McGill 1984); no pie/3D; forecast **fan charts that widen with horizon** (Bank of England method), bands tied to the model's real predictive distribution and level-labeled.
- **Feedback/motion:** Nielsen 0.1/1/10 s thresholds; functional motion kept brief (operational default ~200–250 ms, to be tuned — not a fixed threshold) gated behind `prefers-reduced-motion`; never optimistic display of un-computed financial figures. Add a pre-paint dark-mode bootstrap + toggle (theme exists, no switch yet).

## 4. Assumption-control UX (fix the "wall of sliders")

- **Good cited defaults** so the result renders fully on load (default effect — Johnson & Goldstein 2003): most users never open a control.
- **Two disclosure tiers, never three** (NN/g): 4 high-leverage levers inline (mortgage rate, down-payment %, rent growth, exit-cap spread) + the rest in a right **Drawer** (results stay full-width). Lever choice **confirmed by the engine's own tornado** ([sensitivity.py](../../src/lp_reit_lab/finance/sensitivity.py)), not asserted.
- **Numeric input primary** (NN/g + Accot-Zhai 1997: precise money values can't be set on a drag track), with a linked coarse slider on the 4 levers.
- **Scenarios:** Base/Bull/Bear presets (cited sets) + 2–3-up side-by-side compare; always-visible Reset; per-control "Δ vs cited default" badge; "why this default?" provenance tooltip (operationalizes the cited-default mandate).
- **Live recompute** debounced (operational default ~250 ms, to be tuned; discrete controls instant); briefly highlight changed output cells.

## 5. Features

- **Search (replaces scroll):** `@tanstack/react-table` + `@tanstack/match-sorter-utils` fuzzy **global** filter; `cmdk` ⌘K palette for jump-to-property. All shadcn primitives already vendored.
- **Real OSM map (replaces hand-drawn SVG):** `react-leaflet` 5 + `react-leaflet-cluster` on **CARTO Positron** raster tiles (no Mapbox token; do **not** hit `tile.openstreetmap.org` — usage policy). Marker click ↔ table selection ↔ detail; client-only mount guard for the static build. **Gating data gap:** properties carry synthetic `x,y ∈ [0,1000]`, **no real lat/lng** — add coordinates (synthetic Lincoln Park bbox now; geocode at real-data ingestion). Nothing places on a real basemap until this lands.
- **Retrospective + projection time-series:** Recharts `ComposedChart` = tuple-`[low,high]` `Area` band + solid actual + dashed forecast + `ReferenceLine` at "today"; ≤2 concurrent bands, small multiples beyond. Insertion point: [web/src/routes/market.tsx](../../web/src/routes/market.tsx) (already renders mock index lines).

## 6. Data + forecasting math (retrospective + projection)

Hybrid free-first per [ADR-0001](../decisions/ADR-0001.md). A Cook County Assessor
ingestion layer already exists (commit `7fbe4ac`, `src/lp_reit_lab/ingest/`).

- **Retrospective series.** Metro: S&P Case-Shiller `CHXRSA` (FRED) + FHFA MSA. Neighborhood: DePaul IHS submarket index; Zillow ZORI (ZIP). Per-property: index-anchored last sale with **band widened for idiosyncratic dispersion** (Goetzmann 1992); rent hedonic-imputed to ZORI; tax via the explicit Cook chain. Per-property rent/opex have **no free real series → modeled and labeled**. Point-in-time discipline: vendor vintages, publication-lag, triennial-reassessment step (look-ahead traps).
- **Projection (forecast).** Model in **log space**. Mandatory **random-walk-with-drift benchmark**. Default **bivariate VECM(log price, log rent)** (price-rent cointegration; Gallin 2008; Campbell-Shiller 1988) with momentum + multi-year mean reversion (Case & Shiller 1989); Harvey (1989) local-linear-trend state-space fallback for thin/property level. Lag order by AICc (cited selector).
- **Net P/L.** Monte-Carlo over jointly-simulated value/rent/vacancy paths through the existing engine (Hoesli, Jani & Bender 2006) → distribution of cumulative P/L, levered IRR, equity multiple; report median, P(loss), P(IRR<hurdle). Cap rates time-varying (Plazzi-Torous-Valkanov 2010) — the `exit_cap_spread` lever already respects this.
- **Uncertainty.** Analytic fan charts for display; stationary bootstrap (Politis-Romano 1994) with data-driven block length (Politis-White 2004) for CIs. Round ≤1 decimal (no false precision).
- **Validation + governance.** Rolling-origin (walk-forward) backtest with purge+embargo; metrics RMSE / MASE (Hyndman-Koehler 2006) + PIT calibration / coverage / CRPS (Gneiting et al. 2007); model comparison by Diebold-Mariano (1995) with Harvey-Leybourne-Newbold (1997) small-sample correction and Newey-West (1994) HAC bandwidth; family gate Hansen (2005) SPA / BH-FDR. **Pre-register** model + horizon + selectors + loss + tests before any fit.

## 7. Governance

- **ADR-0003** supersedes the screener portion of ADR-0002.
- **Pre-register** the forecast hypotheses (design.md) before fitting; repro-logs stamped into artifacts; commits via `/commit-with-provenance` (ICMJE 2026 disclosure).
- **Lovable de-coupling:** runtime telemetry sink (`lovable-error-reporting.ts`) and `.lovable/` removed in P0; the `@lovable.dev/vite-tanstack-config` build coupling (wires Nitro/Cloudflare target; dev-only `lovable-tagger`, plus a dead `@lovable.dev/mcp-js` exclude in `bunfig.toml`) is a P1 follow-on.
- **Identity hygiene:** vendored `web/` scanned — no real email, no bare-username token. Git author remains `s-koirala <238704148+s-koirala@users.noreply.github.com>`.
- **Repo:** front-end consolidated under `web/` (one governed provenance boundary). The vendored snapshot is `git archive HEAD` of `north-side-property-compass` @ `bff9b480cbf7` (2026-06-05), recorded in [web/PROVENANCE.md](../../web/PROVENANCE.md).
- **Fair Housing:** tenant-fit stays market-demand framing; run an AVM racial-disparity check (Urban Institute; HUD Cityscape) before any compliance-sensitive publication.

## 8. Phasing (each phase = one `audit-remediate-loop`, ≤3 rounds)

| Phase | Deliverable | Notes |
|---|---|---|
| **P0** | branch; ADR-0003; this memo; vendor React app → `web/`; strip Lovable telemetry; identity scan | *in progress* |
| **P1** | design-system pass on `web/` (tabular-nums, contrast fixes, dark toggle, 8 pt/scale tokens; vite-config de-Lovable) | beautiful base locked |
| **P2** | TS deterministic-DCF mirror + golden-vector parity gate (pytest + Vitest); replace magic-number `computeMetrics`; assumption-Drawer UX + instant recompute | |
| **P3** | search (TanStack Table) + real OSM map (add lat/lng) + bidirectional linking | |
| **P4** | retrospective series from real free metro/neighborhood data + fan-chart UI; `validate-data` | **MVP boundary** |
| **P5** | forecasting + MC artifact compiler (pre-registered) → precomputed artifacts → projection UI + net-P/L distribution | governed heavyweight; deferrable |

## 9. New dependencies (justified)

- **TS** (`web/`): `@tanstack/react-table`, `@tanstack/match-sorter-utils`, `leaflet` + `react-leaflet` + `react-leaflet-cluster`. Respect [web/bunfig.toml](../../web/bunfig.toml) 24 h release-age rule.
- **Python:** `statsmodels`, `arch`, a FRED/Socrata client, `pyarrow` — in `[data]` / forecast extras with cited justification.

## 10. Risks and residuals

- This is a **multi-language program** (React product + Python artifact compiler + parity-gated TS mirror), not a UI tweak — P5 carries the statistical weight and the pre-registration burden.
- The **lat/lng data gap** gates the real map (P3).
- The repo is **edited live** in parallel (the ingestion layer landed mid-plan); work proceeds on `feat/react-merge-p0` to avoid collision.
- Per-property history is **modeled** (no free series) — label and widen bands.
- The Lovable **build** coupling persists until P1.
- Cloudflare Pages static is confirmed viable for everything except live arbitrary forecasting (precomputed).

## 11. References (load-bearing)

- Case & Shiller 1989 (momentum/mean-reversion); Glaeser & Nathanson 2017 (extrapolation → boom/bust); Gallin 2008 (price-rent cointegration); Campbell & Shiller 1988 (present value); Harvey 1989 (structural TS); Goetzmann 1992 (repeat-sales small-sample variance); Plazzi, Torous & Valkanov 2010 (time-varying cap rates).
- Hoesli, Jani & Bender 2006 (real-estate DCF Monte-Carlo); Pagourtzi et al. 2003 (valuation methods review).
- Politis & Romano 1994 (stationary bootstrap); Politis & White 2004 (block length); Hyndman & Koehler 2006 (MASE); Gneiting, Balabdaoui & Raftery 2007 (CRPS/calibration); Diebold & Mariano 1995 + Harvey, Leybourne & Newbold 1997; Newey & West 1994 (HAC bandwidth); Hansen 2005 (SPA).
- Cleveland & McGill 1984 (graphical perception); Okabe & Ito 2008 (CVD-safe palette); WCAG 2.2 (contrast); NN/g progressive disclosure / slider design; Johnson & Goldstein 2003 (default effect); Accot & Zhai 1997 (steering law); Bank of England fan charts.
- Data sources: [ADR-0001](../decisions/ADR-0001.md); Pyodide 0.29.4 lockfile + Cloudflare Workers limits (architecture constraints, [ADR-0003](../decisions/ADR-0003.md)).

> DOIs for the method citations above are deferred to `CITATION.cff` via `/cite-add` (research-memo house style); none are fabricated here.
