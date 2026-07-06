---
title: Power analysis — H002
date: 2026-06-22
hypothesis_id: H002
type: power_analysis
owner: SKIE  # NOT a real-name / OS-username identifier (public repo, SKIE pseudonym discipline)
status: final  # Body = the 2026-06-22 PRE-FREEZE FEASIBILITY REHEARSAL (retained as history); the FREEZE ADDENDUM (2026-07-06, end of file) records the BINDING full-fidelity run on the resolved freeze inputs — its 1,105/side figure supersedes every rehearsal number and binds design §8/§9/§10.
---

# Power analysis for H002

> **PRE-FREEZE FEASIBILITY REHEARSAL — NOT the registered power analysis.** The
> [power-analysis](https://github.com/s-koirala/dotfiles) skill mandates running *after*
> `/preregister` freezes [design.md](design.md) (R3-2a → R3-3) and reading the **frozen** effect,
> alpha, and seed. design.md is **explicitly unfrozen** here: its effect-of-interest, alpha, RNG
> seed, quarterly granularity, ρ_icc and m̄ are all `# TBD-at-freeze` (design.md §8/§11). This
> document therefore computes a **provisional** required-n from placeholders the design says will be
> replaced; the headline figure is a **pre-freeze estimate**, not a `registered
> n_required_for_power_80`, and **does not bind** design §9/§10 until re-run on the frozen inputs
> after the §11.1 freeze (see Disposition). The reproducibility envelope below is **provisional** for
> the same reason (seed not yet pinned in design §11).

> **PROSPECTIVE (design-time) power only.** This computes the sample size required to
> detect the **registered effect of interest** at the registered alpha/power target,
> *before* any data is fit. It is **not** observed/retrospective power: retrospective
> power computed from an *observed* effect is monotone in the p-value and uninformative
> (Hoenig & Heisey 2001, [10.1198/000313001300339897](https://doi.org/10.1198/000313001300339897)),
> and the [power-analysis](https://github.com/s-koirala/dotfiles) skill forbids it. The
> effect of interest below is the **smallest scientifically-meaningful** appreciation-rate
> differential, deliberately **not** the literature point estimate (anchoring bias).

H002 estimand (design.md [§1](design.md)): the constant-quality across-boundary
**appreciation-RATE differential** `β_diff` — the difference in cumulative log price-growth
between the higher-quality (top-ISBE / Oscar-Mayer-boundary) side and the adjacent
lower-quality side, entered as a `boundary_side × period` interaction in a repeat-sales
index (design.md [§5](design.md)). The confirmatory test is **one-sided** (`β_diff > 0`,
directional H1, design.md §1).

## Test type and function selection

The confirmatory `β_diff` is the coefficient on a **`boundary_side × period` interaction** in a
repeat-sales WLS index (design.md [§1](design.md), [§5](design.md)), estimated with **Case-Shiller
holding-period weighting** and the **Webb six-point wild-cluster bootstrap** as the primary
inference (Conley 1999 spatial-HAC the registered small-G fallback) and a **block-bootstrap CI**.
It is **not** a plain two-sample mean comparison: its sampling variance is a
function of the time-dummy design matrix, the WLS weights, the within-PIN differencing, and the
clustered/spatial error structure — not the marginal SD of the raw per-pair `y`. Powering a
regression-coefficient test as a two-group mean difference (finding `power-estimand-mismatch-2`)
and dividing a **window-cumulative** gap by a **single-pair** SD (finding `power-dimensional-scale-4`)
both mis-state the standardized effect and **understate** required n.

**Operative method — Monte-Carlo simulation of the registered estimator AND inference.** Because the
confirmatory estimator is a clustered/heteroskedastic repeat-sales WLS **`boundary_side × period` DiD
differential** with the registered **Webb six-point wild-cluster bootstrap** (design.md §5), the only
fully correct prospective power route is **simulation of that estimator and that inference** under the
design's error structure: a boundary-segment random effect whose **side composition varies across
segments** (per-segment treatment propensity) so intra-cluster correlation `ρ_icc` enters the
`β_diff` variance; Case-Shiller stage-2 holding-period heteroskedasticity `V(τ)`; the BMN quarterly
period-dummy basis; and the Webb wild-cluster bootstrap one-sided rejection rule (the registered
small-G remedy). The power object uses the **primary** registered inference (Webb wild-cluster
bootstrap); design.md §5 names **Conley 1999 spatial-HAC** as the *fallback* when the realized
`G_segment` is still small (it does not depend on a cluster count), reported alongside at fit — the
power requirement is computed under the primary inference and re-checked under the Conley fallback if
the realized `G_segment` lands in the small-G regime. This is the operative power object below; the
script is [power_sim_2026-06-22.py](power_sim_2026-06-22.py).

**Reported only as bounds / cross-checks** (not the operative requirement):

- **i.i.d. floor — `TTestIndPower.solve_power`** (`statsmodels` 0.14.6,
  [statsmodels.stats.power](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.TTestIndPower.html),
  `alternative="larger"`): the constant-SD two-sample-t calculator. Because it assumes **i.i.d.**
  observations — false here (repeat-sale pairs are spatially + serially dependent, which is precisely
  why design.md §5 specifies cluster-robust / Conley SEs) — its n is an **absolute lower bound**, not
  the registered requirement (finding `power-cluster-deff-1`).
- **Analytic design-effect (DEFF) cross-check** — `n = n_floor · (1 + (m̄ − 1)·ρ_icc)` (Kish DEFF),
  with `m̄` = mean repeat-pairs per segment cluster and `ρ_icc` the intra-segment correlation. A
  closed-form exchangeable-within-cluster approximation; reported as a conservative analytic bracket
  on the simulated requirement, not as the requirement (the DEFF over-states inflation for an
  unbalanced-cluster WLS coefficient with a holding-fraction-pro-rated effect — see Required-n).

`NormalIndPower` (known-variance z) and `FTestPower` (omnibus F) are not used: the variance is
estimated, and the confirmatory claim is a single one-sided contrast.

## Effect-of-interest derivation (commensurate scales)

Two distinct scales appear and must be kept commensurate (finding `power-dimensional-scale-4`):
the **window-cumulative** scale (a gap accumulated over the full test window) and the **per-pair**
scale (one repeat-sale pair, holding interval `τ_i ≤ window`).

- **`Δ_rate` (window scale) = 0.05** — the smallest *scientifically-meaningful* cumulative
  across-boundary appreciation differential (5 log points over the test window). **Anchored to a
  RATE-scale change-capitalization magnitude, not to Black 1999's level premium** (design.md §1.1
  stresses LEVEL and RATE are *distinct* estimands; setting the rate MDE from the level magnitude
  re-imports the conflation §1.1 warns against, so it is deliberately avoided here). The licensing
  rate anchor is **Bogin & Nguyen-Hoang 2014** ([10.1111/jors.12141](https://doi.org/10.1111/jors.12141),
  *J. Regional Science* 54(5):788–805), which estimates that an NCLB Title-I failing-school
  **designation** (a school-quality *signal* change) capitalizes into an ≈**6% (≈0.06 log-point)**
  house-price response. Arithmetic shown for reproducibility: `0.05 ≈ 0.83 × 0.06` — i.e. the MDE is
  set just **below** a single documented designation-change capitalization, defensible as a *minimum*
  cumulative across-boundary gap worth detecting over a multi-year window (a persistent quality gap
  can accumulate at least one such designation-scale move). **Caveat:** the Bogin & Nguyen-Hoang
  6% is a single-event designation response on a different sample, so it sets the **order of
  magnitude** of a defensible rate MDE, not a pinned prior; the exact rate-scale anchor (and whether
  the realized boundary quality gap warrants a smaller MDE) is **re-pinned at freeze**.
  `# justify: Δ_rate=0.05 is a minimum-actionable RATE MDE anchored BELOW the ≈0.06 Bogin &
  Nguyen-Hoang 2014 designation-change capitalization (0.05 ≈ 0.83×0.06), NOT scaled from Black's
  LEVEL premium (which would re-import the level/rate conflation §1.1 warns against); the rate-scale
  magnitude is re-pinned at freeze, # TBD-at-freeze.` **This is deliberately the minimum meaningful
  effect, NOT a literature point estimate** (the anchoring bias Hoenig & Heisey 2001 caution against).

- **Per-pair pro-rating (commensurate conversion):** a pair contributes its expected boundary
  differential **pro-rated by its own holding fraction**: `E[Δy_i] = Δ_rate · (τ_i / window)`. A pair
  spanning the full window carries the full 0.05; shorter pairs carry proportionally less. This makes
  the per-pair *effect* and the per-pair *variance* live on the same time scale (the previous draft
  divided a full-window 0.05 by a single-pair SD, biasing the effect upward and required-n downward).
  The simulation draws `τ_i` from a holding-interval distribution (lognormal around the mean hold;
  pinned at freeze) and applies this pro-rating, so the realized average effect is *below* 0.05 —
  raising required n above the i.i.d. floor even before clustering.

- **`σ_idio` (per-pair dispersion) — order-of-magnitude DESIGN PRIOR, 0.15 (bracketed 0.10–0.20),
  with HETEROSKEDASTIC `V(τ)`.** **Relabeled (finding `L-4`):** no source publishes a scalar 0.15
  single-pair SD. Case & Shiller (1987 NBER WP 2393 / 1989 *AER* 79:125–137,
  [JSTOR 1827406](https://www.jstor.org/stable/1827406)) model the repeat-sale error with a variance
  that **grows with the holding interval** (their 3-stage WLS stage-2 regression of squared
  first-stage residuals on the inter-sale interval); Calhoun 1996 (OFHEO HPI Technical Description,
  FHFA) likewise gives a **3-parameter variance function**, not a scalar. 0.15 is therefore an
  explicit **order-of-magnitude design prior** at the **midpoint of the cited 10–20 log-point range**
  — *not* a value "from" Case-Shiller/Calhoun — and the heteroskedasticity is encoded directly
  (finding `power-sigma-heteroskedastic-3`) via the **Case-Shiller stage-2 form**
  `V(τ) = A + B·τ`, parameterized so `V(mean hold) = 0.15²` with a registered growth fraction `B`
  (the quadratic `C·τ²` term is a registered sensitivity, not the central case). The simulation draws
  pair errors with variance `V(τ_i)` and weights the WLS by `1/V(τ_i)` (the design's Case-Shiller
  weighting), so the variance object is **consistent with the registered estimator** rather than a
  single homoskedastic SD that contradicts it. `# justify: σ_idio=0.15 is an order-of-magnitude
  design prior (midpoint of the cited 0.10–0.20 range), NOT pinned-from-source; heteroskedasticity
  via Case-Shiller stage-2 V(τ)=A+B·τ; growth fraction B and mean-hold # TBD-at-freeze from the
  realized inter-sale-interval distribution; realized variance re-estimated at fit.`

The standardized two-sample `d = Δ_rate / σ_idio = 0.3333` is retained **only** for the i.i.d. floor
below (a small-to-medium effect by Cohen 1988; d ≈ 0.2 small, 0.5 medium) and is explicitly **not**
the standardized effect of the registered `β_diff` coefficient.

## Parameters (provisional — pinned at the §11.1 freeze, not yet registered)

These mirror design.md's draft values; design.md is **unfrozen**, so each is `# TBD-at-freeze` and
the figures below are pre-freeze placeholders, not registered values.

| Param | Value | Source |
|---|---|---|
| Effect of interest (Δ_rate, **window**-cumulative log gap) | 0.05  `# justify: minimum-actionable RATE MDE anchored BELOW the ≈0.06 Bogin & Nguyen-Hoang 2014 designation-change capitalization (0.05 ≈ 0.83×0.06); NOT scaled from Black's LEVEL premium; re-pinned at freeze; # TBD-at-freeze` | design.md §1 H1 + §1.2 + §8; Bogin & Nguyen-Hoang 2014 [10.1111/jors.12141](https://doi.org/10.1111/jors.12141) (rate-scale change-capitalization anchor); Black 1999 [10.1162/003355399556070](https://doi.org/10.1162/003355399556070) (level reference only) |
| Per-pair dispersion prior (σ_idio, **midpoint of 0.10–0.20**) | 0.15  `# justify: ORDER-OF-MAGNITUDE design prior, NOT pinned-from-source; no source publishes a scalar 0.15` | Case-Shiller 1987/1989, Calhoun 1996 FHFA (range, not scalar); memo §6 |
| Holding-period variance model V(τ)=A+B·τ (Case-Shiller stage-2) | A,B set so V(mean hold)=σ_idio²; growth-fraction B central, C·τ² sensitivity  `# justify: encodes heteroskedasticity the WLS corrects; B + mean-hold # TBD-at-freeze` | design.md §5 (Case-Shiller WLS); Case-Shiller 1987/1989 |
| Intra-segment correlation (ρ_icc) | central 0.05; grid {0, 0.02, 0.05, 0.10}  `# justify: pre-registered DEFF/clustering assumption; brackets plausible range; # TBD-at-freeze` | design.md §5 (boundary-segment clustering) |
| Mean cluster size (m̄, repeat-pairs/segment) | central 20; grid {10, 20, 50}  `# justify: pre-registered; pinned from realized buffer at freeze; # TBD-at-freeze` | design.md §5 (G_segment) |
| Standardized effect (Cohen's d) — **floor only** | 0.3333  `# justify: d = Δ_rate / σ_idio; used ONLY for the i.i.d. floor, NOT the registered β_diff effect` | derived |
| Alpha (one-sided) | 0.05  `# justify: design.md §8 default confirmatory alpha (Fisher 1925); one-sided via alternative='larger'` | design.md §8 |
| Power target | 0.80  `# justify: design.md §8 = Cohen 1988 convention` | design.md §8 |
| Allocation ratio (sides) | 1.0  `# justify: equal allocation across boundary sides assumed at design time` | design assumption |
| Alternative | larger (one-sided)  `# justify: design.md §1 H1 is directional, β_diff > 0` | design.md §1 |
| **Operative** test | **MC simulation of the repeat-sales WLS `boundary_side × period` DiD differential** (cluster-level treatment so ρ_icc loads the contrast; heteroskedastic V(τ); **Webb six-point wild-cluster bootstrap** one-sided) | design.md §5 |
| Floor / cross-check tests | i.i.d. two-sample t (TTestIndPower); analytic Kish DEFF | bounds only |
| RNG seed (simulation) | 20260622  `# justify: PROVISIONAL — design.md §11 RNG seed is # TBD-at-freeze; pre-freeze-rehearsal seed, load-bearing for the MC sim but not yet pinned/registered; do not modify within this rehearsal` | design.md §11 (# TBD-at-freeze) |
| MC replications (N_REP) | 2000  `# justify: binomial CI on power ±1.8pp at p=0.8; adequate for n-bisection to nearest pair` | design choice |
| Wild-cluster bootstrap reps (WILD_B) | 399  `# justify: B+1=400 ⇒ exact p-value grid; α·(B+1)=0.05·400=20 integer (Davidson & MacKinnon 2000); resolves the 0.95 quantile to 1/400; CGM 2008 / Webb 2023 use B=399 routinely; size verified 0.051 at the null` | design choice (Webb 2023; CGM 2008; Davidson & MacKinnon 2000) |
| Treatment-propensity dispersion (Beta concentration) | 2.0  `# justify: per-segment treatment propensity p_c~Beta(2,2): mean 0.5 (balanced sides in expectation) with broad cross-segment variation so ρ_icc loads the side contrast; realized composition # TBD-at-freeze` | design assumption (finding power-mc-clustering-inert-1) |

## Bootstrap validity — Type-I size check (benchmark)

Before trusting any power number, the Webb wild-cluster bootstrap rejection rule was checked for
**correct size** under the true null: with `delta_window = 0` (so `β_diff = 0` exactly), the one-sided
rejection rate must approach the nominal `α = 0.05`. Computed at n = 150/side, ρ_icc = 0.05, m̄ = 20
(1000 MC replications): **size ≈ 0.05–0.06** at the operative `WILD_B = 399` (within the ±1.4pp MC
binomial CI of nominal 0.05). The test is therefore correctly sized — it does **not** materially
over-reject under the null — so the power (Type-II) numbers below are not inflated by a size
distortion. (A naive CR1 + Student-t critical value at small G *over-rejects*, which is precisely why
design.md §5 registers the Webb wild-cluster bootstrap; this check confirms the registered inference
is the correctly-sized one.)

## Required n (three routes — operative = simulation)

All three routes run in [power_sim_2026-06-22.py](power_sim_2026-06-22.py)
(`uv run --extra analysis python …`; RNG seed `20260622`). Computed values, not asserted:

| Route | Assumptions | n/side | n total | Status |
|---|---|---:|---:|---|
| **(1) i.i.d. floor** (TTestIndPower, `d=0.3333`) | i.i.d.; constant σ; window/per-pair scales | **112** | **224** | **absolute lower bound — NOT the requirement** |
| **(2) analytic Kish DEFF** (central ρ=0.05, m̄=20) | `n_floor·(1+(m̄−1)ρ)` exchangeable-within-cluster | 219 | 438 | conservative analytic bracket |
| **(3) MC simulation (OPERATIVE)** (central ρ=0.05, m̄=20) | WLS `β_diff` DiD contrast; V(τ) heteroskedastic; segment random effect LOADS the contrast (cluster-level treatment); Webb wild-cluster bootstrap; pro-rated per-pair effect | **239** | **`478`** | **provisional pre-freeze estimate (re-run on frozen inputs)** |

> **RNG stream-order note:** 239/side comes from the full GRID run, in which the central cell
> consumes an RNG stream positioned by the cells simulated before it; a STANDALONE re-run of only
> the central cell (fresh stream from the same seed) yields **235/side** — a ~2% Monte-Carlo
> stream-order wobble, not a model difference. The grid-run value (239) is the registered
> provisional figure; the freeze-time full-fidelity re-run (`WILD_B=399`, `N_REP≥2000`) pins its
> own value, where stream-order wobble shrinks with `N_REP`.

The **operative** (provisional pre-freeze) requirement is the simulated **239 pairs/side
(`478` total)** at the central (ρ_icc = 0.05, m̄ = 20) assumptions — it powers the actual
registered estimator (the repeat-sales WLS `boundary_side × period` DiD differential) and the
registered inference (Webb six-point wild-cluster bootstrap). It is a **provisional pre-freeze
estimate** (the §11.1 freeze has not run; it is re-computed on frozen inputs before it binds the
design). Reading why it sits **well above** the i.i.d. floor:

- It is **far above the i.i.d. 112 floor** because (i) the **commensurate per-pair pro-rating**
  (`E[Δy_i] ∝ Δ_rate·τ_i/window`) lowers the realized average effect below the full-window 0.05
  (the dimensional-scale correction `power-dimensional-scale-4` the i.i.d. floor omits) AND (ii) the
  **clustering design effect now LOADS the side contrast**: in the corrected model the boundary-side
  composition varies across boundary-segment clusters (a per-segment treatment propensity), so the
  segment random effect inflates the `β_diff` variance — the inflation finding
  `power-mc-clustering-inert-1` showed was *inert* in the Round-1 model (where `side` was drawn
  independently of `cluster`, differencing `u_c` out of the side contrast).
- It moves **toward/above the analytic Kish DEFF (219/side at the central corner)** rather than
  below it — the corrected simulation no longer **understates** the requirement (the central
  operative figure is 239/side, **above** the 219/side central DEFF). Required-n now **rises with ρ_icc**
  (the registered monotonicity check in the script confirms non-decreasing n in ρ), the qualitative
  signature the Round-1 (inert) model lacked. The Kish DEFF is retained as a closed-form cross-check;
  the operative figure is the Webb-bootstrap MC requirement.

These are **usable, renovation-excluded, minimum-holding-period-filtered** repeat-sale pairs *inside
the boundary buffer* (design.md §2/§4), not raw transactions — the binding scarcity is boundary-buffer
repeat-pair thinness (research memo §6, §12 flag sub-municipal repeat-pair counts as the dominant
variance risk; design.md §10 archives `null, underpowered` on a futility stop).

### Embedded computation (call sites)

The i.i.d. floor (route 1):

```python
import math
from statsmodels.stats.power import TTestIndPower  # statsmodels 0.14.6

SIGMA_IDIO_PRIOR = 0.15  # justify: ORDER-OF-MAGNITUDE design prior (midpoint of cited 0.10–0.20),
                         #          NOT pinned-from-source; constant-σ here ⇒ this route is a FLOOR.
DELTA_RATE       = 0.05  # justify: window-cumulative minimum-actionable RATE MDE; anchored BELOW the
                         #          ≈0.06 Bogin & Nguyen-Hoang 2014 designation-change capitalization
                         #          (0.05 ≈ 0.83×0.06), NOT scaled from Black's LEVEL premium.
d_floor = DELTA_RATE / SIGMA_IDIO_PRIOR   # justify: floor-only Cohen's d; window/per-pair NOT
                                          #          commensurate ⇒ lower bound, not the requirement.
n_floor = TTestIndPower().solve_power(
    effect_size=d_floor, alpha=0.05, power=0.80, ratio=1.0, alternative="larger",
)  # 111.97 → ceil 112/side, 224 total — ABSOLUTE FLOOR
```

The operative route (3) — MC power of the repeat-sales WLS `boundary_side × period` coefficient under
the registered clustered + heteroskedastic error structure — is the full
[power_sim_2026-06-22.py](power_sim_2026-06-22.py): pairs drawn with holding intervals `τ_i` mapped to
quarterly `(t1, t2)` periods, side drawn from a **per-segment treatment propensity** (so ρ_icc loads
the side contrast), per-pair differential `β_per_period·(t2−t1)·side`, errors `~N(0, V(τ_i))` with
`V(τ)=A+B·τ` (Case-Shiller stage-2) plus a segment random effect of variance `ρ·σ²`, WLS weights
`1/V(τ_i)`, the **Webb six-point wild-cluster bootstrap one-sided test** on the single `β_diff`
coefficient, and bisection on `n` to the 0.80 power target. The DEFF cross-check (route 2) is
`n_floor·(1+(m̄−1)ρ_icc)`.

Computed (this run, seed `20260622`): floor **112**/side (224); analytic DEFF central **219**/side
(438); **operative MC central 239**/side (**`478`** total).

## Sensitivity grid (joint — clustering dominates)

The previous one-dimensional Δ_rate sweep (holding σ fixed and asserting the multiplier "reads
equivalently" as a σ sweep) understated joint uncertainty: that equivalence holds only for the
symmetric reciprocal pair, never brackets the **clustering** parameters (ρ_icc, m̄) that finding
`power-cluster-deff-1` shows **dominate** required n, and is computed for the wrong (i.i.d. t-test)
estimator. The operative grid below sweeps the two clustering parameters that drive the design
effect, computed on the **simulated WLS coefficient** (route 3) and cross-checked against the
analytic Kish DEFF (route 2). Both are reported because the closed-form DEFF brackets the simulated
inflation from above.

**Analytic DEFF cross-check** `n = 112·(1+(m̄−1)ρ_icc)`:

| m̄ \ ρ_icc | 0.00 | 0.02 | 0.05 (central) | 0.10 |
|---|---:|---:|---:|---:|
| 10 | 112 / 224 | 133 / 266 | 163 / 326 | 213 / 426 |
| **20** | 112 / 224 | 155 / 310 | **219 / 438** | 325 / 650 |
| 50 | 112 / 224 | 222 / 444 | 387 / 774 | 661 / 1322 |

**Operative MC simulation** (repeat-sales WLS `β_diff` DiD differential, heteroskedastic V(τ),
cluster-level treatment so ρ_icc loads the contrast, Webb wild-cluster bootstrap; n/side / total):

| m̄ \ ρ_icc | 0.00 | 0.02 | 0.05 (central) | 0.10 |
|---|---:|---:|---:|---:|
| 10 | 168 / 336 | 199 / 398 | 215 / 430 | 223 / 446 |
| **20** | 168 / 336 | 220 / 440 | **239 / 478** | 272 / 544 |
| 50 | 168 / 336 | 265 / 530 | 291 / 582 | 380 / 760 |

Reading the joint grid:

- **The i.i.d. 112 floor is never the operative requirement**, and **required-n rises with ρ_icc** at
  fixed m̄ (the registered ρ-monotonicity check in the script confirms non-decreasing n in ρ) — the
  clustering inflation is now live, not inert. The gap above 112 at ρ=0 is the dimensional-scale
  (per-pair pro-rating) correction; the further rise with ρ_icc is the boundary-segment clustering
  design effect loading the side contrast (`power-mc-clustering-inert-1`).
- **σ / effect axis:** because the simulation scales the per-pair effect by `Δ_rate·τ/window` and the
  variance by `V(τ)`, a mis-specified σ or Δ_rate moves the whole surface multiplicatively; the
  i.i.d.-floor table preserved below the line gives the order-of-magnitude σ/effect sensitivity, while
  the *clustering* sensitivity (the dominant risk) is the two grids above. The `C·τ²` (quadratic
  heteroskedasticity) and `VAR_GROWTH_FRACTION` knobs are registered sensitivities in the script.
- **Dominant-risk reading:** the worst plausible corner — not the optimistic left tail of a
  one-dimensional Δ sweep — governs the futility threshold. In the **corrected** model the cluster
  inflation is no longer inert: required-n **rises with ρ_icc** (the script's registered
  ρ-monotonicity check confirms non-decreasing n in ρ at m̄=20), so the worst (high-ρ_icc, high-m̄)
  corner sets the conservative requirement and the central corner sets the operative figure. The
  provisional pre-freeze `n_required_for_power_80 = 239/side (478 total)` is set at
  the central corner, with the grid disclosed so the realized (ρ_icc, m̄) at fit can be read against
  it. This is **not yet bound**: it is re-run on the frozen inputs after the §11.1 freeze.
- **DEFF vs MC, low- vs high-m̄:** at the central m̄=20 the simulated requirement (239/side) sits
  *above* the analytic Kish DEFF (219/side) — the per-pair pro-rating + clustering both inflate it. At
  **high m̄=50** the simulated worst corner (380/side at ρ=0.10) sits *below* the DEFF (661/side):
  the Case-Shiller WLS down-weighting of long, high-variance pairs damps the cluster inflation that
  the closed-form exchangeable-mean DEFF assumes, so the DEFF over-states the requirement for the
  unbalanced-cluster WLS coefficient at large m̄. The DEFF is therefore a *conservative upper bracket*
  at high m̄ and a *lower* reference at the central corner; the operative figure is the simulated
  requirement, not the DEFF.

*Order-of-magnitude σ/effect (i.i.d. floor only — NOT the operative requirement; retained for the
σ/Δ sensitivity it shows):* halving the effect (or doubling σ) raises the i.i.d. floor to ~446/side;
doubling it lowers the floor to ~29/side. The operative simulated requirement scales similarly with
the effect but is additionally floored by the pro-rating and clustering corrections above.

## Disposition

This is a **pre-freeze feasibility rehearsal** (not the registered power analysis — design.md is
unfrozen, all parameters `# TBD-at-freeze`); the realized usable repeat-pair count is **UNKNOWN
until the CCAO point-in-time pull, the CPS-boundary / ISBE / permit auxiliary joins, and the buffer +
renovation + minimum-holding filters land** (design.md §11; project MEMORY "Next steps"). No
data is frozen, so no disposition is *decided* here — only the rule (re-computed on frozen inputs at
the §11.1 freeze) is sketched:

- **If realized usable n ≥ `478` total (≥ 239 per side) at the frozen effect AND the
  realized (ρ_icc, m̄) place the requirement at or below the central corner:** proceed to
  [validate-data](https://github.com/s-koirala/dotfiles) → statistical-analysis.
- **If realized usable n < `478` (or < 239 per side), OR the realized (ρ_icc, m̄)
  push the simulated requirement above the realized n:** the design is under-powered for the
  registered minimum meaningful effect ⇒ **archive(null, underpowered)** per design.md §10 (kept in
  the register, **not** deleted, **not** re-specified to chase significance), OR revise the effect of
  interest downward under a **new** hypothesis ID with a fresh pre-registration. The futility stop of
  design.md §9 wires to the **operative** `n_required_for_power_80 = 239 per side /
  478 total` (central ρ_icc=0.05, m̄=20), **re-evaluated at fit against the realized (ρ_icc,
  m̄)** from the joint grid — the i.i.d. 112/224 is an absolute floor, never the operative threshold.

**Pooled vs per-fold n reconciliation (finding `power-futility-vs-pooled-n-6`).** The 239/side
figure is a **pooled, usable, renovation-excluded, minimum-holding-filtered** count *inside the
boundary buffer* — the count on which the **confirmatory pooled `β_diff`** is estimated. The §6 purge
removes every pair whose `[t1, t2]` straddles a fold boundary, so the **per-fold** effective n is
materially smaller (with a ~7y mean hold a pair straddles many quarterly fold edges; the bulk of
pairs hold >4y, so most pairs are purged from any single short fold). These are **two different
n's at two different granularities**: the confirmatory `β_diff` and its futility gate operate on the
**pooled terminal** count (this analysis powers *that* estimator), while the walk-forward folds drive
the §1.2 pre-trend / placebo **identification** gate and out-of-sample stability — not the
confirmatory sample size. The futility threshold is therefore keyed to the **pooled terminal usable
count** (239/side), and the realized **per-fold post-purge counts are reported alongside** so
the post-purge thinness (research memo §6/§12 sub-municipal repeat-pair scarcity) is visible and a
fold whose post-purge n collapses is flagged rather than silently pooled.

This operative required-n becomes `n_required_for_power_80` in the design's §9 stopping rule and §10
decision rule **only after** the §11.1 freeze resolves the remaining `# TBD-at-freeze` parameters
(alpha, the rate-scale Δ_rate anchor, the RNG seed, the quarterly granularity, mean hold, growth
fraction B, and the realized ρ_icc and m̄ from the buffer) and the simulation is **re-run on those
frozen inputs**. The figure shown here is the provisional pre-freeze estimate.

## References

- Black, S. E. (1999). "Do Better Schools Matter? Parental Valuation of Elementary Education."
  *QJE* 114(2):577–599. [10.1162/003355399556070](https://doi.org/10.1162/003355399556070) —
  boundary-discontinuity school-quality price-LEVEL capitalization. The headline magnitude is a
  **conditional elasticity**: parents pay ≈2.5% more (≈2.1% higher house price) **per 5% increase in
  test scores**, *not* a flat unconditional premium. Used only as an order-of-magnitude level anchor;
  the cumulative rate MDE is re-anchored to a rate-scale change-capitalization estimate at freeze
  (see Effect-of-interest derivation).
- Bogin, A., & Nguyen-Hoang, P. (2014). "Property Left Behind: An Unintended Consequence of a No
  Child Left Behind \"Failing\" School Designation." *Journal of Regional Science* 54(5):788–805.
  [10.1111/jors.12141](https://doi.org/10.1111/jors.12141) — repeat-sales/DiD capitalization of an
  NCLB Title-I failing-school designation (≈6% house-price response); the **rate-scale** anchor for
  the Δ_rate MDE (Δ_rate=0.05 set just below this single-event ≈0.06 magnitude).
- Case, K. E., & Shiller, R. J. (1989). "The Efficiency of the Market for Single-Family
  Homes." *American Economic Review* 79(1):125–137 ([JSTOR 1827406](https://www.jstor.org/stable/1827406);
  pre-DOI-era, no CrossRef DOI) and (1987) NBER WP 2393 — repeat-sales 3-stage WLS. Provides the
  **holding-period variance FORM** `V(τ)` (variance grows with the inter-sale interval), **not** a
  scalar σ_idio; 0.15 is an order-of-magnitude design prior bracketed by the cited 0.10–0.20 range,
  not a value published by this source.
- Calhoun, C. A. (1996). *OFHEO House Price Indexes: HPI Technical Description.* FHFA — geometric
  repeat-sales weighting; gives the **3-parameter variance function**, not a scalar idiosyncratic SD
  (so likewise not the source of a 0.15 figure; corroborates only the order-of-magnitude range).
- Bailey, M. J., Muth, R. F., & Nourse, H. O. (1963). "A Regression Method for Real Estate Price
  Index Construction." *JASA* 58(304):933–942.
  [10.1080/01621459.1963.10480679](https://doi.org/10.1080/01621459.1963.10480679) — the base
  repeat-sales log-difference estimator underlying `β_diff`.
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed. Lawrence
  Erlbaum. ISBN 978-0805802832 — the 0.80 power convention and d benchmarks.
- Hoenig, J. M., & Heisey, D. M. (2001). "The Abuse of Power: The Pervasive Fallacy of Power
  Calculations for Data Analysis." *Am Stat* 55(1):19–24.
  [10.1198/000313001300339897](https://doi.org/10.1198/000313001300339897) — retrospective power
  is uninformative; only prospective (pre-specified-effect) power is legitimate.
- Seabold, S., & Perktold, J. (2010). statsmodels. *Proc. 9th Python in Science Conf.* —
  `statsmodels.stats.power.TTestIndPower` (v0.14.6), the solver used here.

## Reproducibility

The ReproLog is **emitted mechanically by the simulation script** (not by hand) — run
`uv run --extra analysis python power_sim_2026-06-22.py --emit-repro-log`, which calls the project
[emit-repro-log](https://github.com/s-koirala/dotfiles) skill's `capture()`/`write()` and asserts
`ReproLog.verify()` before exit (findings `repro-emission-not-guarded-2`, `repro-config-sha-stale-1`).
phase=`validation`; hypothesis_id=`H002`; rng_seed=`20260622`
`# justify: PROVISIONAL — design.md §11 RNG seed is # TBD-at-freeze; this is the pre-freeze
feasibility-rehearsal seed, load-bearing for the MC simulation but NOT yet the registered/pinned
seed`; dataset_checksums=`{}` `# no dataset frozen yet — pre-freeze power from a literature variance
prior`.

**`config_resolved_sha256` is now defined over a FILE-INDEPENDENT canonical input**, removing the
self-referential rendered-markdown slice that was the root cause of the stale-hash finding. The
script computes it as

```
config_resolved_sha256 = sha256( sha256(design.md)_hex || "\n" || sha256(power_sim_2026-06-22.py)_hex )
```

(function `canonical_config_sha256()` in [power_sim_2026-06-22.py](power_sim_2026-06-22.py)), so any
third party can recompute it from the two source files alone — it does **not** depend on the bytes of
*this* markdown and therefore cannot drift when the prose is edited. statsmodels 0.14.6; numpy 2.4.6;
scipy 1.17.1; git HEAD, `uv pip freeze` SHA-256, and `uv.lock` env_id are captured automatically by
the ReproLog envelope. The simulation itself is [power_sim_2026-06-22.py](power_sim_2026-06-22.py).

### Reproducibility — run record (this analysis)

Values below are emitted **mechanically** by `power_sim_2026-06-22.py --emit-repro-log` and mirrored
here verbatim (no hand-entry), per finding `repro-emission-not-guarded-2`:

| Field | Value |
|---|---|
| run_id | `4a0a06c6c950444eb72ea4b674c597c3` |
| ReproLog path | `logs/reproducibility/repro_log_4a0a06c6c950444eb72ea4b674c597c3.json` |
| phase | `validation` |
| hypothesis_id | `H002` |
| rng_seed | `20260622` (**provisional** — design.md §11 RNG seed is `# TBD-at-freeze`; pre-freeze rehearsal seed) |
| dataset_checksums | `{}` (no dataset frozen yet — pre-freeze power from a literature variance prior) |
| git HEAD | `6d0b450d1821c5abe6a9905dc136d701335dd61f` |
| pip_freeze_sha256 | `e4ad712dd61bbf48e5aaad53e0e56fb7ebb9fe3bbd5c5ef60f8112744f24c075` |
| env_id (uv.lock) | `b39ef7bcf390040f74c51c25a8c9d682071e94a6f20c1fa928732d625e538d69` |
| statsmodels / numpy / scipy | `0.14.6` / `2.4.6` / `1.17.1` |
| config_resolved_sha256 | `baafeb0529e3e49d27f09f2d58d0d31160abd0d24343e75b0b10a7594064a394` (= `sha256(sha256(design.md) ‖ "\n" ‖ sha256(power_sim_2026-06-22.py))`; file-independent, recomputable by any third party — NOT a self-referential slice of this markdown) |

(Run record re-emitted 2026-06-22T18:15Z after the `L-1` DOI correction — `10.1111/jors.12076`→`10.1111/jors.12141` in design.md and power_sim_2026-06-22.py — which changed the bytes of both hashed source files and therefore `config_resolved_sha256` and `run_id`; the simulated grid is **unchanged** (central 239/side = 478 total) because the edit touched only a citation string, no simulation input. The superseded run was `run_id 0b7131e999d14c8d89fa9c2871611f05` / `config_resolved_sha256 f7df1a38…`.)

**Binding integrity anchor at this DRAFT revision (finding `R-2`).** The `git HEAD` recorded above
(`6d0b450`) is the repo HEAD *at run time*, but every input that produced this run is **untracked or
modified** in the working tree at this pre-freeze revision (design.md, this script, this analysis, the
config YAML, and the ReproLog itself are not yet committed — the freeze commits them via
[/preregister](https://github.com/s-koirala/dotfiles)). A third party checking out `6d0b450` would
**not** find these files, so `git_head` does **not** pin the byte-state of the run inputs at draft
stage and is **informational only** until the §11.1 `/preregister` freeze (which commits the artifact
set and recomputes design.md's SHA, R3-2a). The binding reproducibility anchor at this revision is
therefore **`config_resolved_sha256`** — the content hash `sha256(sha256(design.md) ‖ "\n" ‖
sha256(power_sim_2026-06-22.py))`, recomputable from the two source files alone — **not** `git_head`.
Scope caveat: `config_resolved_sha256` covers **design.md + this script only**; it does **not** cover
[config/multipletest_family.yaml](../../../config/multipletest_family.yaml) or
[hypothesis_backlog.md](../../../hypothesis_backlog.md), which are pinned (and committed) only at the
freeze. This is the expected pre-freeze posture (design.md §11/§11.1 pin the design.md SHA and dataset
checksums **at** `/preregister`, not at draft); it is logged here so the run-record is not mistaken for
a committed-HEAD-anchored reproducibility claim.


---

## AI-assistance statement (ICMJE 2026)

Per [ICMJE Recommendations (updated January 2026)](https://www.icmje.org/recommendations/), AI
is **not** an author. This prospective power analysis was produced with **Claude Opus 4.8**
(model id `claude-opus-4-8`), role = **code + audit** (implementing and running the Monte-Carlo
power simulation of the registered clustered/heteroskedastic repeat-sales WLS coefficient
[power_sim_2026-06-22.py](power_sim_2026-06-22.py), the i.i.d. floor, and the analytic DEFF
cross-check; rendering this artifact against the design's pre-registered parameters). Numeric
outputs are the real computed values from the embedded call sites, not asserted. The effect of
interest is a pre-specified minimum meaningful effect (not an observed/retrospective quantity),
per Hoenig & Heisey 2001 and the power-analysis skill. This revision incorporates Round-1 audit
remediations (operative power moved from the i.i.d. two-sample t to the simulated WLS coefficient;
commensurate per-pair/window scales; Case-Shiller `V(τ)` heteroskedasticity; joint (ρ_icc, m̄)
sensitivity grid; corrected σ_idio attribution) **and Round-2 remediations**: (a) the boundary-side
composition now **varies across boundary-segment clusters** (per-segment treatment propensity) so the
segment random effect **loads the side contrast** and ρ_icc is no longer inert (`power-mc-clustering-inert-1`);
(b) the estimand is the repeat-sales **`boundary_side × period` DiD differential** (a single
summarizing growth-rate coefficient with the BMN period-dummy basis), not a side-dummy level
(`power-estimand-mismatch-persists-2`); (c) inference is the **registered Webb six-point wild-cluster
bootstrap** (`power-smallG-inference-mismatch-3`); (d) the MDE is re-anchored to a **rate-scale**
change-capitalization magnitude (Bogin & Nguyen-Hoang 2014), dropping the false "⅓-of-Black"
arithmetic (`power-mde-arithmetic-false-4`); (e) the artifact is relabeled a **pre-freeze feasibility
rehearsal** (`power-run-before-freeze-5`); (f) the ReproLog is **emitted mechanically** by the script
with a file-independent canonical config hash (`repro-emission-not-guarded-2`,
`repro-config-sha-stale-1`); (g) the Black 1999 magnitude is restated as a **conditional elasticity**
(`L-3`). Reproducibility envelope at [logs/reproducibility/](../../../logs/reproducibility/).


---

## FREEZE ADDENDUM — binding full-fidelity re-run (2026-07-06)

The rehearsal figures above (239/side central at assumed ρ=0.05, m̄=20) are RETIRED. The binding
run executes [power_sim_2026-06-22.py](power_sim_2026-06-22.py) with every `# TBD-at-freeze`
prior RESOLVED outcome-blind from the realized frozen cell (q_top=10, `G* = G_noise`, 250 m;
evidence [segment_structure_h002-frozen-cell_2026-07-06.csv](../../../data/interim/segment_structure_h002-frozen-cell_2026-07-06.csv)):
mean hold 3.778 y, holding CV 0.669, segment-size shares (CV 1.429) and per-segment high-side
composition resampled from the realized vectors, M_BAR_GRID = {112.5, 127.5, 139.7, 141.0},
registered ρ grid, `WILD_B=399`, `N_REP=2000`. Full log:
[power_run_2026-07-06.log](power_run_2026-07-06.log) (the equal-cluster first attempt is
retained as [power_run_2026-07-06_SUPERSEDED-priors.log](power_run_2026-07-06_SUPERSEDED-priors.log)).

**OPERATIVE: `n_required_for_power_80` = 1,105/side (2,210 total)** at the frozen central case
(ρ_icc = 0.05, m̄ = 112.5). Realized qualified low-side count 1,718 ⇒ futility gate PASSES
(1.6×). ρ-monotonicity check passed. Central-column sensitivity: ρ=0.02 → 543/side (clears);
ρ=0.10 → 2,042/side (**exceeds the realized 1,718 — acknowledged infeasibility bound**, design
§11.2). Unequal clusters raise the requirement ≈2.6× over the equal-cluster draft — the Kish
size-CV effect the freeze audit demanded be modeled.

Run record (mirrors the ReproLog):

| field | value |
|---|---|
| run_id | `1ab78e33e92a4a7182893026e3045d51` |
| repro_log_path | [repro_log_1ab78e33e92a4a7182893026e3045d51.json](../../../logs/reproducibility/repro_log_1ab78e33e92a4a7182893026e3045d51.json) |
| phase | validation |
| rng_seed | 20260706 (the registered §11 seed) |
| git_head | `6d0b450d1821c5abe6a9905dc136d701335dd61f` |
| pip_freeze_sha256 | `676fa96233dfde98201a3767d4c816a333b43c531959de8af452dfb769bb3f2e` |
| config_resolved_sha256 | `fd5253df4469f4c256d3068c59060e2fa6b316ebc1dee27915c38896a8cf167b` |
