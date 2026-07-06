---
name: H002 — School-catchment capitalization (top-ISBE / Oscar Mayer boundary raises constant-quality appreciation)
description: Pre-registered design doc for hypothesis H002
type: project
hypothesis_id: H002
tier: 2
status: designed  # FROZEN 2026-07-06 via /preregister. running | evaluated | archived(positive|null|negative) follow.
owner: SKIE  # NOT a real-name / OS-username identifier (public repo, SKIE pseudonym discipline)
created: 2026-06-22
citations:
  - "10.1162/003355399556070"   # Black 1999 — boundary-discontinuity school-quality capitalization (price LEVEL)
  - "10.1086/522381"   # Bayer-Ferreira-McMillan 2007 (JPE 115(4):588-638) — boundary fixed-effects identification
  - "10.1080/01621459.1963.10480679"  # Bailey-Muth-Nourse 1963 — repeat-sales index (base log-difference)
  - "10.1162/rest.90.3.414"     # Cameron-Gelbach-Miller 2008 — wild-cluster bootstrap (few clusters)
  - "10.1111/caje.12661"   # Webb 2023 (CJE 56(3):839-858) — six-point wild-bootstrap weights for small G; originating edition = Webb 2014, Queen's Economics Dept WP No. 1315 (no journal DOI; cite by report number). CrossRef-verified; verify edition via /cite-add at freeze
  - "10.1016/S0304-4076(98)00084-0"  # Conley 1999 — spatial-HAC standard errors
  - "10.1111/j.2517-6161.1995.tb02031.x"  # Benjamini-Hochberg 1995 — FDR
  - "10.1111/jors.12141"   # Bogin & Nguyen-Hoang 2014, "Property Left Behind: An Unintended Consequence of a No Child Left Behind 'Failing' School Designation," J. Regional Science 54(5) — repeat-sales/DiD capitalization of an NCLB failing-school DESIGNATION (school-quality signal change; rate-interaction license; verify via /cite-add at freeze)
  # external_doi omitted: internal-only at draft; set on OSF upload at /preregister (R3-2b)
---

> **FROZEN 2026-07-06 via [/preregister](https://github.com/s-koirala/dotfiles/tree/main/claude/commands/preregister.md).**
> This document is now IMMUTABLE: any change requires a new hypothesis ID. Every
> `# TBD-at-freeze` marker has been resolved (§11.2 freeze-resolution record); the freeze SHA-256
> of this file is recorded in the freeze ReproLog (`config_resolved_sha256`) and in the
> [hypothesis_backlog.md](../../../hypothesis_backlog.md) H002 row — recompute and compare to
> verify integrity. Freeze was pre-authorized by the operator on 2026-06-22, gated on the data
> landing (§11), which cleared 2026-07-06. External posting (OSF) deferred per R3-2b:
> internal-only freeze, fully verifiable from the ReproLog.

# H002 — School-catchment capitalization

This document is the pre-registration record for hypothesis H002. It is **draft** at this
revision; it becomes frozen at `designed` status via `/preregister`, after which any change
requires a new hypothesis ID (the freeze computes a SHA-256 over the rendered 11-section
document; editing a header or numeric basis post-freeze breaks the immutability contract).

The 11 sections below are ported from the SKIE-Universe trading-strategy template
([hypothesis_design_TEMPLATE.md](~/.claude/skills/pre-register-hypothesis/assets/hypothesis_design_TEMPLATE.md)).
H002 is a **real-estate repeat-sales econometrics study**, not a trading strategy: there is no
position, no trade, and no Sharpe. Per the template-fit mapping in
[methodology_data-feasibility_2026-06-22.md](../../../docs/methodology/methodology_data-feasibility_2026-06-22.md)
(§5), all 11 headers are retained for freeze fidelity; trading-specific sections (3 Features,
4 Label, 5 Estimator, 6 Splitter, 7 Cost model, and the DSR sub-field of 8 Gate thresholds)
carry an explicit `N/A for an index study, mapped to <X>` note. Feasibility for open data is
established in that memo (§3): of the family H001–H004, **only H002 is testable on the
currently-available open panel**, because the repeat-sales estimator differences out every
time-invariant unit attribute and therefore needs none of the MLS/MRED-gated structural fields
(beds / sqft / DOM / HOA) that block H001/H003/H004.

## 1. Hypothesis

The estimand is a **constant-quality appreciation differential** across a CPS attendance
boundary: the difference in constant-quality price-growth rate between the higher-quality
(top-ISBE / Oscar-Mayer-boundary) side and the adjacent lower-quality side. It is stated as a
regression coefficient on a `boundary_side × period` interaction in a repeat-sales index
(equivalently, the growth-rate difference between two side-specific repeat-sales indices — see
§5).

- **H0:** `β_diff = 0` — the across-boundary difference in constant-quality appreciation is zero.
  Formally, in the repeat-sales specification of §5, the coefficient on the
  (high-quality-side × period) interaction summarizing the across-boundary differential
  cumulative log price-relative is zero: `β_diff = 0`.
- **H1:** `β_diff > 0` (sign **+**, directional) — a property inside a top-ISBE-rated /
  Oscar-Mayer attendance boundary is associated with a **positive** across-boundary
  constant-quality appreciation differential. One-sided alternative; the mechanism predicts a
  signed direction, so the confirmatory test is one-tailed at the §8 alpha (the two-sided CI is
  also reported).
- **Mechanism:** **School-quality capitalization.** Households bid up housing whose deed conveys
  access to a higher-quality assigned public school; the differential is identified by comparing
  otherwise-similar units that fall on opposite sides of an administrative attendance boundary
  (a spatial discontinuity in the assignment, not in the housing stock).
- **Primary citations:**
  - **Black 1999** ([10.1162/003355399556070](https://doi.org/10.1162/003355399556070)) —
    boundary-discontinuity capitalization of school quality into house **prices** (the seminal
    boundary design). *Verify and mirror into [CITATION.cff](../../../CITATION.cff) via `/cite-add` before freeze —
    the backlog H002 row flags "verify via /cite-add"; this draft does not assume the citation is
    already in [CITATION.cff](../../../CITATION.cff).*
  - **Bayer, Ferreira & McMillan 2007** ([10.1086/522381](https://doi.org/10.1086/522381))
    — "A Unified Framework for Measuring Preferences for Schools and Neighborhoods," *Journal of
    Political Economy* 115(4):588–638. Boundary **fixed-effects** estimator controlling for
    unobserved neighborhood attributes that co-vary with school quality (the convergent-validity
    cross-check of §5).
  - **Bailey-Muth-Nourse 1963** ([10.1080/01621459.1963.10480679](https://doi.org/10.1080/01621459.1963.10480679))
    — repeat-sales index, base log-difference OLS estimator.
  - **Case-Shiller 1987/1989** — 3-stage WLS holding-period heteroskedasticity correction on the
    repeat-sales index.
  - **Calhoun 1996 / FHFA** — geometric weighting of the repeat-sales index.

### 1.1 Estimand reconciliation (LEVEL vs RATE) — required reading for the confirmatory claim

Black 1999 estimates a **price-LEVEL** capitalization effect: the percentage difference in the
sale **price** of houses on the high-quality side of the boundary, identified cross-sectionally
with a boundary fixed effect and structural controls (beds/sqft/lot). That estimand is **not**
open-data-identifiable here, because the CCAO open panel has **no structural attributes**
([schemas.py](../../../src/lp_reit_lab/ingest/schemas.py): `pin`, `sale_date`, `sale_price`,
`class`, `doc_no`, `lat`, `lon` only — confirmed against the validated pandera schema, not
assumed), so a constant-quality **level** comparison cannot be formed from open data alone.

The **confirmatory estimand for H002 is the constant-quality appreciation DIFFERENTIAL (a RATE)**,
not the price level, for one decisive reason: the **repeat-sales** estimator differences two sales
of the **same PIN**, so every time-invariant unit attribute (beds, bath, sqft, vintage, fixed
micro-location quality) cancels within the pair — *the unit is its own control*. This makes the
appreciation differential identifiable **without any structural attributes** and is precisely why
H002 (alone in the family) clears the open-data feasibility gate
([methodology_data-feasibility_2026-06-22.md](../../../docs/methodology/methodology_data-feasibility_2026-06-22.md) §3).

Relationship between the two estimands: under capitalization, a **widening** quality gap (or a
period of differential demand growth) produces a positive appreciation **rate** differential even
when the cross-sectional **level** premium is the deeper structural object. A non-zero rate
differential is therefore *sufficient* evidence of differential capitalization dynamics but is a
**distinct** estimand from Black 1999's level premium; this design tests the rate differential and
does **not** claim to reproduce the level premium.

- **Confirmatory estimand:** the repeat-sales across-boundary appreciation-rate differential
  `β_diff` (§5). This is the H1 coefficient gated in §8/§10.
- **Convergent-validity cross-check (NOT confirmatory, conditional):** a **boundary fixed-effects
  level** comparison in the spirit of Bayer et al. 2007 — included **only if** a constant-quality
  level proxy becomes available (e.g. an MLS structural-attribute join landing per the deferred
  H001 acquisition, or a defensible CCAO-assessed-value normalization). With open data alone no
  such proxy exists, so the level cross-check is **deferred / conditional** and explicitly **not**
  part of the confirmatory gate. It is named here for transparency, not promised on the open panel.

### 1.2 Identifying assumptions for the `boundary_side × period` rate estimand

The confirmatory estimand is a **rate** (a `boundary_side × period` interaction in a within-PIN
repeat-sales index), not a cross-sectional **level**. In the within-PIN repeat-sales design the
time-invariant side indicator is **differenced out**; only its interaction with period survives, so
`β_diff` is a **difference-in-differences** parameter, not the level discontinuity of Black 1999 /
Bayer et al. 2007. The level-capitalization boundary papers (cross-sectional designs) do **not** by
themselves license this rate-interaction estimand; the following assumptions and tests do.

- **Parallel-trends / common-shock identifying assumption (REGISTERED):** absent the school-quality
  differential, constant-quality appreciation trends on the two boundary sides are **parallel** —
  i.e. there is no side-specific common shock (differential gentrification, transit access, zoning
  change, or amenity shock) that would by itself open a `boundary_side × period` differential. Under
  this assumption a non-zero `β_diff` is attributable to the capitalization mechanism (or to a
  *widening* quality gap, §1.1), not to a confounding side-specific trend. This is the DiD analogue
  of Black 1999's level-design conditional-independence assumption, and it is the load-bearing
  assumption of the confirmatory claim.
- **Pre-trend / placebo gate (REGISTERED, run before the confirmatory read):**
  - **(a) Event-study pre-trend test** — estimate the full vector of `boundary_side × period`
    interactions and confirm no significant side differential in the periods *before* the
    quality-gap opens. A significant pre-trend falsifies parallel trends and **blocks** the
    confirmatory read (the design is then archived `null` with an identification-failure note, §10),
    rather than re-specified to chase significance.
  - **(b) Placebo-boundary test** — re-run `β_diff` on a **non-qualifying** administrative boundary
    (a boundary with no school-quality discontinuity); the placebo `β_diff` should be ≈ 0. A
    non-zero placebo signals a residual side-specific trend confound. Both gate results are reported
    alongside the confirmatory estimate.
- **Treatment-label vintage (REGISTERED — reconciles a TIME-VARYING treatment with the static side
  indicator):** ISBE quality (§3 `isbe_quality`) is reconstructed annually and **revises**, so a
  boundary's "top-ISBE" status can **flip mid-panel** — a static `boundary_side` label would then
  mislabel the treatment. The high-quality-side label is therefore **time-varying**, set from the
  ISBE vintage in force on each sale's `sale_date` (consistent with the §2 roll-handling / point-in-
  time rule). Boundary segments whose top-ISBE status **flips within a pair's holding interval**
  `[t1, t2]` are **excluded** from the confirmatory set (the side label is not stable across the
  pair); the confirmatory `β_diff` is estimated on segments with a **stable side label across the
  pair**, with the flip-segment subset reported separately as a sensitivity. This is distinct from,
  and in addition to, the §2 index-revision leakage note.
- **Rate/DiD licensing citation:** the rate-interaction estimand is licensed by a school-quality-
  **change** capitalization framing — a *widening* quality gap producing an appreciation-rate
  differential — for which the appropriate anchor is a repeat-sales / DiD study of price responses
  to school-quality *changes* (e.g. **Bogin & Nguyen-Hoang 2014**, "Property Left Behind: An
  Unintended Consequence of a No Child Left Behind \"Failing\" School Designation," *J. Regional
  Science* 54(5), [10.1111/jors.12141](https://doi.org/10.1111/jors.12141) — repeat-sales/DiD
  capitalization response to an NCLB Title-I failing-school **designation** (a school-quality
  *signal* change), which fits the rate/DiD licensing argument more tightly than a generic
  school-choice framing; verify and mirror via `/cite-add` at freeze). Black 1999 / Bayer et al. 2007
  remain the **level**-capitalization anchors; the rate estimand additionally rests on the parallel-
  trends assumption above and the cited change-capitalization design. `# justify: rate-interaction
  estimand licensed by a school-quality-CHANGE / repeat-sales-DiD citation + the registered parallel-
  trends assumption, NOT by level-capitalization papers alone; DiD citation verified via /cite-add at freeze.`

## 2. Universe and sample period

Bounded at pre-reg; no discretion later. Walk-forward only — **no k-fold** per
[rules/quant-project.md](~/.claude/rules/quant-project.md) "Time-series integrity".

- **Instruments:** CCAO **repeat-sale PIN pairs** — two arms'-length sales of the same 14-digit
  PIN — in **Lincoln Park (community area 7)** and adjacent submarkets **Lakeview (CA 6)** and
  **Near North (CA 8)**, **restricted to the attendance-boundary-straddling buffer** (pairs whose
  PIN lat/lon falls within the §6 distance bandwidth of a qualifying CPS attendance-boundary
  segment). The buffer restriction is what makes the comparison a boundary-discontinuity design
  rather than a whole-submarket comparison (Black 1999; Bayer et al. 2007). Condo class and 1–4
  unit residential class included; non-residential CCAO classes excluded.
- **Frequency:** transaction-event, aggregated to **quarterly index periods** (the repeat-sales
  time dummies are quarterly). Quarterly chosen as the finest period that keeps repeat-pair counts
  per cell above the thin-cell variance floor identified in the research memo
  ([§6](../../../docs/research_notes/research_market-scoping_2026-06-05.md), §12).
  **PINNED at freeze (2026-07-06): quarterly.** Realized vintage-era pair volume = 39,871 pairs
  over 80 confirmatory quarters ≈ 498 pairs/quarter panel-wide (buffer subset ≈ 52/quarter at the
  250 m band) — above the thin-cell floor at quarterly granularity.
  `# justify: quarterly = FHFA/Case-Shiller index convention; confirmed against observed per-cell pair counts at freeze, not hand-set.`
- **Session(s):** N/A for a property index (no intraday/RTH-ETH session regime). Retained header;
  the analogue is the **sale-completion event** (CCAO `sale_date`, date-only).
- **Train window / Validation window / Test window:** time-ordered, **disjoint**, walk-forward
  over `sale_date`. The first fold's train window opens at the panel epoch
  (`sales_epoch_start`, schemas.py) and the final test window closes at the snapshot date; fold
  boundaries are the quarterly index-period edges (§6). **RESOLVED at freeze (2026-07-06) from the
  realized ingested panel:** span = 1999-01-01 → 2026-05-26 (realized max `sale_date`; snapshot
  2026-07-06), i.e. quarterly periods 1999Q1–2026Q2 (110 quarters). The **confirmatory
  labelled subset opens 2006-11-01** — the epoch is set by the LATER of the two label
  requirements: the first CPS boundary vintage is in force from 2006-09-01 (SY0607, Sep-1 rule),
  but the first ISBE quality label enters force 2006-11-01 (rc2006 publication rule, recipe §3.2),
  and a pair needs BOTH labels. Effective confirmatory span 2006Q4–2026Q2 = **79 labelable
  quarters** (2006Q3 is structurally empty of quality-labelable sales). Rule unchanged:
  expanding-window walk-forward, ≥ one full quarter of test per fold.
  **Confirmatory boundary LEVEL — ELEMENTARY only (registered):** the confirmatory universe is
  the elementary attendance-boundary layer. Basis: the H1 mechanism names an elementary boundary
  (Oscar Mayer); the seminal design (Black 1999) is an elementary-school capitalization study;
  and high-school attendance areas OVERLAP the elementary layer — the same parcel would carry two
  side labels, double-counting boundaries and contaminating segment clustering. The high-school
  layer is ingested, validated, and RESERVED for a registered secondary/robustness analysis, not
  the confirmatory gate.
- **Roll-handling note:** the repeat-sales index is **re-estimated per fold using ONLY the vintage
  of every input knowable at that fold's decision date.** Index **revision** is a look-ahead trap:
  a later sale revises earlier index periods, and ISBE Report Card / boundary GeoJSON vintages also
  revise — the research memo §6 flags this explicitly ("index **revision** is a look-ahead trap
  (use the vintage knowable at decision time)"). Each fold therefore consumes the as-of vintage,
  never the latest. Spatial point-in-polygon assignment uses the boundary vintage in force on the
  `sale_date`, not the current boundary.

## 3. Features

> `N/A for an index study (no FEATURE_REGISTRY trading features); mapped to covariate / boundary
> modules.` No `FEATURE_REGISTRY` semver namespace exists in this project yet, so modules are named
> **descriptively** below rather than as `name@version` entries; a versioned registry entry is a
> follow-on if/when these modules are reused. The point-in-time property test and pipeline-level
> leakage check (R3-5 [pit-canary](https://github.com/s-koirala/dotfiles) skill) **must pass
> before any run** — the canary is mandatory here precisely because the point-in-polygon + ISBE +
> permit joins each carry a revision/vintage leakage surface (§2 roll-handling).

- **`boundary_side` (boundary-side indicator):** point-in-polygon test of each PIN's lat/lon
  against the CPS attendance-boundary GeoJSON in force on the `sale_date` —
  **elementary `u959-tya7`**, **high-school `fkiq-5i7q`**
  ([research memo §4.6](../../../docs/research_notes/research_market-scoping_2026-06-05.md)).
  Yields the high-quality vs adjacent-side label that defines `β_diff`.
- **`isbe_quality` (school-quality signal):** ISBE Illinois Report Card metrics reconstructed into
  a quality signal — **SQRP was retired in 2025**, so legacy SQRP levels are historical-only and the
  signal is rebuilt from ISBE component metrics (research memo §4.6). Used to *select* which boundary
  segments qualify as "top-ISBE" and to rank-order boundary pairs; the reconstruction recipe is
  pre-specified at freeze (no post-hoc metric cherry-picking).
- **`reno_permit_flag` (renovation-contamination flag):** Chicago building-permit join
  (**`ydr8-5enu`**) — a major permit dated **between** the two sales of a pair flags that pair for
  exclusion (§4), because a renovation breaks the repeat-sales constant-quality assumption (research
  memo §4.2, §6). **"Major" PINNED at freeze (2026-07-06):** `permit_type ∈ {PERMIT -
  RENOVATION/ALTERATION, PERMIT - NEW CONSTRUCTION, PERMIT - WRECKING/DEMOLITION}` — the three
  structural-alteration types of the City of Chicago permit-type taxonomy (`ydr8-5enu`
  `permit_type` values) — with **no reported-cost floor** (declared costs are owner-reported and
  gameable; a floor would re-admit under-declared renovations; a $10k-floor variant is a
  registered sensitivity). Join key is the building-level `pin10`; over-flagging of condo units
  by building/neighbour works is the conservative direction (sample loss, not contamination) and
  its rate is reported at fit.
- **`dist_to_boundary` (running variable):** signed network/Euclidean distance from PIN to the
  nearest qualifying attendance-boundary segment; defines the §2 straddling buffer and enters as the
  boundary-discontinuity running variable / bandwidth selector (§6).

## 4. Label construction

> `N/A — no triple-barrier (no pt_sl profit-take/stop-loss, no vertical_barrier, no
> volatility_estimator); mapped to the repeat-sales log price relative.` This is a **panel index
> study, not a trade-labeled strategy**: there is no entry/exit, no barrier, and no meta-label. The
> López de Prado AFML §3.2 triple-barrier machinery does **not** apply and is intentionally absent.

- **Outcome:** the **log price relative of a repeat-sale pair** of the same PIN,
  `y = log(sale_price_t2) − log(sale_price_t1)` for the two sales at `t1 < t2`. This is the
  dependent variable of the BMN 1963 repeat-sales regression (§5).
- **Renovation exclusion:** pairs with a `reno_permit_flag` (a major building permit between `t1`
  and `t2`, `ydr8-5enu`) are **excluded** — renovation contaminates the constant-quality assumption
  (research memo §4.2, §6).
- **Minimum holding-period filter:** pairs with an inter-sale interval below a minimum holding
  period are **dropped** to suppress flip / non-arm's-length noise (rapid resales are
  disproportionately distressed, intra-family, or flip transactions that violate the index's
  arm's-length assumption — Case-Shiller 1987 motivate down-weighting/excluding short-interval
  pairs). **PINNED at freeze (2026-07-06): 182 days (6 months), the S&P CoreLogic Case-Shiller
  index-methodology exclusion.** The registered data-driven changepoint was attempted first and
  FAILED as a flip discriminator: the Fisher-1958 k=2 break on log holding time lands at 1,080
  days — it splits the organic-resale bulk, not the flip tail, because the flip cluster is too
  thin to changepoint (0.9% of realized pairs < 90 days; 2.4% < 180; 5.5% < 365). The cited
  index-methodology convention therefore substitutes for the failed empirical rule — a
  fallback hierarchy (empirical rule → published methodology convention) ADOPTED at resolution
  time, pre-freeze and outcome-blind (dates only), not previously registered — and the < 1-year
  exclusion variant is reported as sensitivity. Source: S&P CoreLogic Case-Shiller Home Price
  Indices Methodology (S&P Dow Jones Indices, current edition,
  [spglobal.com](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-corelogic-cs-home-price-indices.pdf))
  — sale pairs with an interval under six months are excluded as likely non-arms-length/flip
  transactions.
  `# justify: 182d = S&P CoreLogic Case-Shiller methodology exclusion (cited convention), adopted after the registered changepoint rule failed on the realized distribution (documented above); not hand-set.`
- **No-look-ahead at the label:** the schema gate already rejects any `sale_date` after the snapshot
  ([schemas.py](../../../src/lp_reit_lab/ingest/schemas.py) L37–42); both sales of every retained
  pair are therefore in-sample as-of the snapshot, and `t2` membership in a fold is governed by the
  §6 purge.
- **Meta-label horizon → splitter purge:** there is no meta-label horizon; the analogue feeding the
  splitter `purge` is the **inter-sale holding interval** `[t1, t2]` (see §6).

## 5. Estimator

> `mapped to repeat-sales regression (no ML hyperparameter grid in the classifier sense).`

- **Model class — confirmatory:** **repeat-sales regression.**
  - *Baseline:* **Bailey-Muth-Nourse 1963** log-difference **OLS** — regress `y` (§4) on the set of
    quarterly period dummies, with the across-boundary differential entered as a
    **`boundary_side × period` interaction** (`β_diff` = the H1 coefficient of §1). Equivalently,
    estimate **two side-specific repeat-sales indices** and define `β_diff` as the difference in
    their cumulative log growth over the test window — the two parameterizations are reported
    together as an internal consistency check.
  - *Heteroskedasticity correction:* **Case-Shiller 1987/1989 3-stage WLS** — the repeat-sales
    residual variance grows with holding-period length; stage 2 regresses squared first-stage
    residuals on holding interval, stage 3 re-weights. This is the primary index estimator; BMN OLS
    is the un-weighted reference.
  - *Weighting variant:* **Calhoun 1996 / FHFA geometric** weighting reported as a robustness
    variant of the index.
- **Model class — convergent cross-check (conditional, not confirmatory):** **boundary
  fixed-effects hedonic** (Bayer, Ferreira & McMillan 2007, *JPE* 115(4):588–638,
  [10.1086/522381](https://doi.org/10.1086/522381)) — boundary-segment fixed
  effects absorbing unobserved neighborhood attributes. **Conditional on a constant-quality level
  proxy existing** (§1.1) — not estimable on the open panel alone; reported as convergent validity
  only when an attribute join lands. Does **not** enter the §8 confirmatory gate.
- **Inference (standard errors) — clustering level and implied G (REGISTERED):** clustering at the
  **submarket / community-area** level is **rejected as the primary level** because it yields only
  **G ≈ 3** clusters (CA 6 / 7 / 8), far below the ~30–50 rule-of-thumb at which cluster-robust
  asymptotics hold and below the range where even the wild-cluster bootstrap has reliable coverage
  (Cameron-Gelbach-Miller 2008 show poor coverage at very small G). The **primary clustering unit is
  the CPS attendance-boundary SEGMENT** — each qualifying boundary segment is a cluster — which
  raises G to the number of qualifying segments in the buffer (`G_segment`, pinned at freeze from the
  realized buffer; **target G_segment well above the small-G regime**, with the realized count
  reported). `# justify: clustering at the boundary-segment level (not the G≈3 community-area level)
  to keep G out of the small-G regime where CR asymptotics and the wild bootstrap both fail (CGM
  2008); G_segment pinned at freeze.`
  - *Primary SE:* **cluster-robust by boundary segment** with the **wild-cluster bootstrap
    (Cameron-Gelbach-Miller 2008, [10.1162/rest.90.3.414](https://doi.org/10.1162/rest.90.3.414))**
    using **Webb six-point weights** (Webb 2023, *Canadian Journal of Economics* 56(3):839–858,
    [10.1111/caje.12661](https://doi.org/10.1111/caje.12661); originating edition Webb 2014, Queen's
    Economics Dept WP No. 1315) — the Rademacher two-point weights degenerate when G is small, so the
    six-point weights are the registered small-G remedy — *not* HC3 (HC3 assumes independence,
    false under spatial/serial clustering; research memo §6).
  - *Spatial primary / fallback when `G_segment` is still small:* **Conley 1999 spatial-HAC**
    ([10.1016/S0304-4076(98)00084-0](https://doi.org/10.1016/S0304-4076(98)00084-0)) as the primary
    inference where the realized `G_segment` remains below the small-G threshold (spatial-HAC does
    not depend on a cluster count), with the bandwidth chosen at the distance where the residual
    Moran correlogram flattens (research memo §6 — *not* a hand-set bandwidth; sensitivity reported).
  - The realized `G_segment` is reported and **tied directly to the design effect in the power
    analysis** (`m_bar` = mean repeat-pairs per segment cluster drives `DEFF`; see
    [power_analysis_2026-06-22.md](power_analysis_2026-06-22.md), DEFF section). The inference
    limitation at small G is acknowledged explicitly rather than asserted away.
- **Identification gate (REGISTERED — runs BEFORE the confirmatory read, §1.2):** the event-study
  **pre-trend** test (full `boundary_side × period` vector; no significant pre-quality-gap side
  differential) and the **placebo-boundary** test (`β_diff ≈ 0` on a non-qualifying administrative
  boundary) are estimated and reported alongside `β_diff`. A failed pre-trend or a non-null placebo
  **blocks** the confirmatory read (archive `null`, identification-failure note, §10). The
  confirmatory `β_diff` is estimated only on boundary segments with a **stable** top-ISBE side label
  across each pair's holding interval (§1.2 treatment-label vintage); flip-segments are reported as a
  separate sensitivity, not in the confirmatory gate.
- **CI:** **block bootstrap** (not i.i.d.) on `β_diff` and on the index path, block length =
  Politis-White automatic selection (the same length feeds the §6 embargo). i.i.d. bootstrap is
  forbidden on the serially dependent index (research memo §6;
  [rules/quant-project.md](~/.claude/rules/quant-project.md) bootstrap clause).
- **Hyperparameter grid / search protocol:** **no ML hyperparameter grid.** The only tunable
  quantities are the **boundary buffer bandwidth** (§6) and the **quarterly period granularity**
  (§2); both are **data-driven and pre-specified** (bandwidth at the boundary-discontinuity optimal
  bandwidth / Moran-flattening distance; granularity from per-cell pair counts), selected **inside**
  the walk-forward so no information leaks from outer test folds to the inner selection (template §5
  "search nested in walk-forward" transfers). `# justify: bandwidth + period granularity are the only tuned values; both selected by data-driven rule, fixed at freeze.`
- **Loss / metric:** repeat-sales WLS objective (Case-Shiller weighting); the reported statistic is
  `β_diff` with its block-bootstrap CI and clustered/spatial-HAC SE.

## 6. Splitter

> `mapped to PurgedWalkForward over sale_date.`

- **Splitter choice:** **time-ordered walk-forward over `sale_date`** (expanding window), **never
  k-fold** ([rules/quant-project.md](~/.claude/rules/quant-project.md);
  [research memo §6](../../../docs/research_notes/research_market-scoping_2026-06-05.md)). Folds
  break on quarterly index-period edges (§2).
- **`purge` derivation:** a repeat-sale **pair spans an interval `[t1, t2]`**; a pair whose interval
  **straddles a train/test fold boundary** would leak test-period information into training (its
  `y` embeds price movement on both sides of the cut). **Purge therefore removes every pair whose
  holding interval crosses the fold boundary**, i.e. `purge ≥ the maximum repeat-pair holding-period
  overlap` at each boundary. This is the index-study analogue of `purge ≥ max label horizon`
  (template §6) — here the "label horizon" is the inter-sale interval (§4). `# justify: purge = max straddling holding-period interval; derived from the data, not fixed.`
- **`embargo` selection method:** **data-driven**, **not hand-set** — the **maximum** of the lag
  implied by the **residual PACF** and the **Politis-White automatic block length** (template §6
  wording transfers verbatim; the block length is the same one used for the §5 block-bootstrap CI).
  `# justify: embargo = max(residual-PACF lag, Politis-White block length); data-driven per template §6.`
- **Spatial leakage control:** handled by **design**, not only by purge — the §2 boundary-buffer
  restriction + the §5 cluster-robust / Conley spatial-HAC SEs address cross-sectional spatial
  dependence; the residual Moran correlogram is inspected and the Conley bandwidth set where it
  flattens (research memo §6).
- **If CPCV:** not used — a plain `PurgedWalkForwardSplitter` is sufficient; the combinatorial-purged
  variant is unnecessary for a single index/coefficient estimand and would multiply the test count
  without benefit. (`n_groups` / `n_test_groups` N/A.)

## 7. Cost model

> **N/A for an index study — no trading, no slippage, no commission.** Header retained for freeze
> fidelity.

- **`cost_model_id`:** N/A. Appreciation-index / boundary-coefficient estimation has **no
  trading or transaction-cost layer**: nothing is bought or sold by the analysis, so there is no
  slippage, commission, or financing cost to model. This is an econometric estimand, **not a
  tradable strategy**.
- **Commission schedule source / Slippage model version:** N/A (see above).

## 8. Gate thresholds

Any deviation from project defaults carries a `# justify:` note + citation.

- **`alpha`:** one-sided significance level for the confirmatory `β_diff > 0` test.
  **PINNED at freeze (2026-07-06): α = 0.05 one-sided** (basis: the conventional level per
  Fisher 1925, *Statistical Methods for Research Workers*; retained rather than a stricter
  single-claim level because the operative gate is already the stricter family-corrected
  `α/m = 0.0125` below). `# justify: 0.05 = Fisher 1925 convention; the binding threshold is the family-corrected 0.0125.`
- **`bh_threshold` (BH-FDR threshold):** the H002 confirmatory `β_diff` is one member of the
  **pre-registered family H001–H004**; **family-wise control is BH-FDR**
  (Benjamini-Hochberg 1995, [10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x))
  across the family, and **Holm 1979** for the **single headline confirmatory claim** (research
  memo §6). The H002 effect is registered in
  [config/multipletest_family.yaml](../../../config/multipletest_family.yaml)
  **before fit** via the [multipletest-gate](https://github.com/s-koirala/dotfiles) skill (family
  `lp-reit-core-2026`, rows H001–H004; H002 = the single confirmatory member, `status:
  designed_draft`). **Single-observable-p regime (finding `mt-bhfdr-single-observable-7`):** BH-FDR
  and Holm are procedures on a *vector* of simultaneously-observed p-values, but at registration
  **only H002 is testable** on the open panel (H001/H003/H004 are MLS-gated, `raw_p = null`). With a
  *single* observable p against the pre-registered m=4, **both procedures degenerate to the same
  single-test threshold** `α/m = 0.05/4 = 0.0125` (BH rank-1 `= (1/m)·α`; Holm step-1 `= α/m`; they
  coincide). The operative gate on the lone H002 claim is therefore an **`α/m` single-test threshold
  (Bonferroni-equivalent), not an FDR procedure** — FDR control is undefined/over-conservative with
  one observable p. The m=4 denominator is retained (pre-registered family scope, so the threshold is
  not understated); the **full FDR p-vector is re-evaluated only when ≥2 family members yield a
  p-value** (a gated member becomes testable on a future MLS acquisition).
  `# justify: with one observable p against m=4, BH-FDR≡Holm≡α/m=0.0125 (Bonferroni-equivalent); FDR vector re-evaluated only when ≥2 members are testable (finding mt-bhfdr-single-observable-7); q level pinned at freeze with the family count.`
- **`dsr_activation_size` (Deflated Sharpe Ratio activation):** **N/A — no Sharpe.** Mapped to: the
  headline confirmatory boundary-effect claim is gated by **Holm**, the family by **BH-FDR**.
  **Hansen 2005 SPA / White 2000 reality check are reserved for strategy-return framings** and do
  **not** apply to a single index/coefficient estimand (feasibility memo §5.2).
- **Power target:** **0.80**, the conventional target (Cohen 1988, *Statistical Power Analysis for
  the Behavioral Sciences*, 2nd ed.). `# justify: 0.80 = Cohen 1988 convention.` Power is computed
  **prospectively** at the registered effect-of-interest, alpha, and realized repeat-pair counts via
  the [power-analysis](https://github.com/s-koirala/dotfiles) skill **after** this freeze and
  **before** fit; **retrospective (post-hoc) power is forbidden** (Hoenig & Heisey 2001). The
  registered effect-of-interest (the smallest appreciation-rate differential worth detecting) is
  pinned at freeze from a **rate-scale** school-quality-**change** / repeat-sales-DiD capitalization
  magnitude (Bogin & Nguyen-Hoang 2014, §1.2), **not** from Black 1999's price-LEVEL premium (using
  the level magnitude to set the rate MDE re-imports the level/rate conflation §1.1 warns against).
  **PINNED at freeze (2026-07-06): Δ_window = 0.05 cumulative log-points over the nominal 7-year
  test window** (≈ 0.83 × the ~6-log-point Bogin & Nguyen-Hoang 2014 failing-designation
  capitalization response — the registered rate-scale anchor; see
  [power_analysis_2026-06-22.md](power_analysis_2026-06-22.md) `DELTA_RATE_WINDOW` derivation),
  pro-rated per pair by holding interval.
  The power object is **not** an i.i.d. two-sample t: because the §5 estimator is a
  clustered/heteroskedastic repeat-sales WLS **coefficient** with Webb wild-cluster-bootstrap
  inference, the operative `n_required_for_power_80` is computed by **Monte-Carlo simulation of that
  estimator and that inference** under the design effect (intra-segment correlation `ρ_icc` entering
  the side contrast via cluster-level treatment composition, mean cluster size `m̄`, Case-Shiller
  `V(τ)` heteroskedasticity), with the i.i.d. two-sample-t result kept only as an **absolute floor**
  and a Kish DEFF as a conservative analytic bracket
  ([power_analysis_2026-06-22.md](power_analysis_2026-06-22.md)). The pre-freeze
  feasibility-rehearsal simulation gave a provisional central requirement of 239 pairs/side (478
  total) at the assumed (ρ_icc=0.05, m̄=20). **RESOLVED at freeze (2026-07-06) by the
  full-fidelity re-run on the REALIZED cluster structure** (`WILD_B=399`, `N_REP=2000`,
  M_BAR_GRID = realized {112.5, 127.5, 139.7, 141.0}, registered ρ grid; run record
  [power_run_2026-07-06.log](power_run_2026-07-06.log)):
  **`n_required_for_power_80` = 1,105 pairs/side (2,210 total)** at the frozen central case
  (ρ_icc = 0.05, m̄ = 112.5, q_top = 10, 250 m band), under the REALIZED cluster-structure priors
  (segment-size shares CV 1.429, realized per-segment treatment composition, realized holding
  moments — unequal clusters raise the requirement ~2.6× over the equal-cluster draft, the Kish
  size-CV effect). The realized qualified low-side count is **1,718 ≥ 1,105** (1.6×), so the §9
  futility gate passes at freeze; the ρ_icc = 0.10 sensitivity is expected to exceed the realized
  count and is reported as an acknowledged infeasibility bound, not silently dropped. Conservatism
  note: the simulation models G = n/m̄ (G ≈ 20 clusters at the answer point) while the realized
  design carries **G = 37** segments at the realized n — small-G inference is strictly harder, so
  the simulated requirement over-states what the realized cluster count demands.
  `# justify: power on the actual clustered/heteroskedastic WLS coefficient + Webb wild-cluster bootstrap (simulation) at the REALIZED m̄ grid; ρ kept at the registered grid central (estimating realized ρ_icc needs outcome residuals, sealed until post-freeze).`

## 9. Stopping rule

- **Stop criterion:** **(a) a fixed number of walk-forward folds** determined by the realized panel
  span at the §2 quarterly granularity, **OR (b) futility** — terminate if the realized usable
  repeat-pair count in the boundary buffer falls below `n_required_for_power_80` from the §8
  prospective power analysis (the design is then archived **null-underpowered** per §10, not
  re-specified to chase significance). `n_required_for_power_80` is **BOUND at freeze
  (2026-07-06): 1,105/side (2,210 total)** — the §8 full-fidelity re-run value on the frozen
  alpha / effect-of-interest / granularity / realized cluster structure; the realized qualified
  low-side count (1,718) clears it, so the study proceeds. **Granularity note (finding `power-futility-vs-pooled-n-6`):** the §8 count is a
  **pooled** (terminal) usable-pair count, while the §6 purge drops every pair whose `[t1,t2]`
  straddles a fold boundary, so the **per-fold** effective n is materially smaller than the pooled
  count (a multi-year hold straddles many quarterly fold edges). The futility gate is therefore
  evaluated against the **pooled terminal** count at the **same granularity the confirmatory pooled
  `β_diff` is estimated on** (the confirmatory estimator pools across folds; the walk-forward folds
  drive the pre-trend/placebo identification gate and out-of-sample stability, not the confirmatory
  n), and the realized per-fold counts are reported alongside so the post-purge thinness is visible.
  `# justify: futility n defined at the pooled-terminal granularity of the confirmatory estimator, with per-fold post-purge counts reported (finding power-futility-vs-pooled-n-6); pinned at freeze.`
  No "train until the coefficient crosses X" rule exists; there is no Sharpe optimization target
  (the template's Sharpe clause is inert here).
- **Max folds:** **RESOLVED at freeze (2026-07-06): ≤ 78** — the 79 realized labelable
  confirmatory quarters (2006Q4–2026Q2, §2) minus the opening train quarter; the realized fold
  count after the §6 purge is reported at fit.
- **Max wall-clock budget:** not the binding constraint (the estimator is a closed-form WLS +
  bootstrap, not an iterative search); fold count / futility govern. A generous wall-clock ceiling
  may be pinned at freeze for the bootstrap loop.

## 10. Decision rule

Mapping from gate outcome to archival label and next action. **Null results stay in the hypothesis
register** per the non-loss policy ([hypothesis_backlog.md](../../../hypothesis_backlog.md) status legend).

- **If `passed=True`** (one-sided `β_diff > 0` significant after Holm for the headline + BH-FDR
  across the family, CI excludes zero, n ≥ `n_required_for_power_80`): **archive(positive)**; report
  the capitalization differential with its block-bootstrap CI; promote to the deal-memo /
  neighborhood-profile evidence layer (the index-study analogue of the template's paper-trade list).
- **If `passed=False` and CI excludes zero but the BH-FDR / Holm family correction is not cleared:**
  **archive(null)** with an explicit **multiple-testing note** (the raw effect was nominally
  significant but did not survive family-wise control).
- **If `passed=False` and CI covers zero:** **archive(null)** — no across-boundary appreciation
  differential detected.
- **If realized n < `n_required_for_power_80`** (= **1,105/side**, the value bound at the §11.1
  freeze; at freeze the realized 1,718 low-side count clears it — this clause remains live only
  against post-purge attrition at fit)**:** **archive(null, underpowered)** —
  kept in the register as a thin-cell / power-limited result (research memo §6, §12 flag
  sub-municipal repeat-pair thinness as the dominant variance risk), **not** deleted and **not**
  re-specified.
- **If the §5 identification gate fails** (significant `boundary_side × period` pre-trend, or a
  non-null placebo-boundary `β_diff`): **archive(null)** with an explicit **identification-failure
  note** — the parallel-trends assumption (§1.2) is not supported, so the confirmatory `β_diff` is
  not interpretable as capitalization; the result is **not** re-specified to chase significance.

## 11. Reproducibility commitments

Per [~/.claude/CLAUDE.md](~/.claude/CLAUDE.md) reproducibility contract and the project
[CLAUDE.md](../../../CLAUDE.md) "Reproducibility contract" (13-field ReproLog via the
[emit-repro-log](https://github.com/s-koirala/dotfiles) skill):

- **git HEAD (at run):** auto-populated by the ReproLog at run time.
- **`uv pip freeze` sha (at run, 64-hex):** auto-populated by the ReproLog.
- **RNG seed:** **PINNED at freeze (2026-07-06): `20260706`** — the registered seed for every
  confirmatory-analysis stochastic component (wild-cluster bootstrap draws, block bootstrap CI);
  date-of-freeze convention, same scheme as the rehearsal seed (20260622), which it supersedes.
  `# justify: pre-registered; the deterministic WLS estimator and the block-bootstrap CI consume
  it; do not modify post-hoc (RNG seeds are the one value exempt from the data-driven-tuning rule
  — user CLAUDE.md "Parameter & Prompt Selection").`
- **Dataset checksums (frozen at pre-reg from [data/_manifest.json](../../../data/_manifest.json)):**
  **RESOLVED at freeze (2026-07-06): the data-landing gate has CLEARED.** All four inputs are
  ingested keyless, validated, and checksummed: CCAO sales panel (137,189 arms-length sales /
  124,745 parcels, snapshot 2026-07-06, byte-reproducible re-pull, sha256 `55902ee2…`), 40 CPS
  attendance-boundary vintages (SY0607–SY2526 × two levels), Chicago building permits (dual-arm,
  count-anchored), and 20 ISBE Report Card years + 12 layouts (config-pinned sha256 per file).
  Validation report: [data/validation_h002-freeze-inputs_2026-07-06.md](../../../data/validation_h002-freeze-inputs_2026-07-06.md)
  (all checks PASS); per-file checksums frozen in
  [data/_manifest.json](../../../data/_manifest.json) (78 files, `--check` stable at freeze);
  raw-pull provenance (queries, upstream versions, dual-source lineage) in
  [ingest_manifest.json](../../../data/processed/_provenance/ingest_manifest.json).
- **Reproducibility log path:**
  [logs/reproducibility/](../../../logs/reproducibility/)`repro_log_<run_id>.json`.
- **Design.md SHA at freeze:** auto-populated by `/preregister` (R3-2a). **Not computed at draft
  stage** — this document is mutable until freeze.

### 11.1 Pre-freeze checklist (must clear before `/preregister`)

1. Verify the **Black 1999** mechanism DOI via [/cite-add](https://github.com/s-koirala/dotfiles)
   and mirror it (plus Bayer et al. 2007, BMN 1963, Case-Shiller, CGM 2008, Conley 1999, BH 1995)
   into [CITATION.cff](../../../CITATION.cff) (backlog H002 row flags "verify via /cite-add"). **Bayer, Ferreira &
   McMillan 2007 mirrors as DOI `10.1086/522381`** (*Journal of Political Economy* 115(4):588–638),
   **NOT** any `10.1162/qjec…` string — the QJE DOI is fabricated and resolves 404; do not let
   `/cite-add` re-introduce it.
2. Ingest + validate the CCAO repeat-sales panel and the H002 auxiliaries (CPS `u959-tya7` /
   `fkiq-5i7q`, ISBE Report Card, permits `ydr8-5enu`); freeze their
   [data/_manifest.json](../../../data/_manifest.json) checksums.
3. Run **prospective** power-analysis (§8) on realized boundary-buffer pair counts; pin `alpha`,
   the effect-of-interest, the RNG seed, the quarterly granularity, the buffer bandwidth, and the
   minimum holding-period filter — resolving every `# TBD-at-freeze` above.
4. Register the H002 `β_diff` in [config/multipletest_family.yaml](../../../config/multipletest_family.yaml)
   under BH-FDR (Holm headline) via [multipletest-gate](https://github.com/s-koirala/dotfiles).
5. Pass the [pit-canary](https://github.com/s-koirala/dotfiles) point-in-time leakage check on the
   join pipeline (§3).

### 11.2 Freeze-resolution record (2026-07-06)

All values below were resolved OUTCOME-BLIND (school-side data, geography, and pair COUNTS only;
no sale price or log price relative consumed) by the registered data-driven rules; evidence
artifacts are committed alongside this design.

| Quantity | Frozen value | Basis / evidence |
|---|---|---|
| Boundary buffer bandwidth (power basis) | **250 m** | Mid-grid of the {150, 250, 400} m candidates, inside the Black-1999-style boundary-band range; the in-analysis data-driven bandwidth rule of §5 (boundary-discontinuity optimal bandwidth / Moran-flattening) is unchanged and reported with sensitivities at 150/400 m. |
| `q_top` (top-tier rung) | **10** (ISBE-Exemplary decile) | Registered rule: FINEST rung of {10, 20, 25, 33.3} meeting the power target at its realized cluster structure — see [qualification_counts_2026-07-06.md](../../../docs/research_notes/qualification_counts_2026-07-06.md). |
| `G*` (qualification gap) | **4.944 percentile pts** (`G_noise`, Kane-Staiger noise floor); `G_break` = 36.170 pts retained as strong-gap SENSITIVITY | Rule revised pre-freeze, outcome-blind, rationale + realized values in the recipe §2.2 ([methodology_isbe-quality-recipe_2026-07-06.md](../../../docs/methodology/methodology_isbe-quality-recipe_2026-07-06.md)). |
| Realized qualified design (q_top=10, 250 m, G*=G_noise) | **4,161 stable qualified pairs (2,443 high / 1,718 low side), G_segment = 37, m̄ = 112.5**; excl.-stale sensitivity 3,603 | Qualification memo table; low side is the binding count. |
| `G_segment` inference regime | 37 → **Webb six-point wild-cluster bootstrap primary**; **Conley spatial-HAC co-reported unconditionally** | The §5 "small-G threshold" was left unpinned at draft; RESOLVED here as **G < 30** (the CGM 2008 rule-of-thumb floor §5 already cites) — G = 37 therefore keeps Webb primary. This resolves a registered ambiguity, not a pinned rule. |
| Boundary-school ↔ RCDTS crosswalk | 55/55 matched (50 exact, 5 prefix, 0 forced); Oscar Mayer = school_id 610059 → RCDTS 150162990252337, top decile at rc2025 | [crosswalk_boundary_rcdts_2026-07-06.csv](../../../data/interim/crosswalk_boundary_rcdts_2026-07-06.csv). |
| Min holding period | **182 days** + <1-year sensitivity | §4 (registered changepoint failed on the realized distribution; cited S&P CS convention substituted, documented). |
| Quarterly granularity | **quarterly** | §2 (realized per-cell counts). |
| Registered RNG seed | **20260706** | §11. |
| `n_required_for_power_80` | **1,105/side (2,210 total)** at the frozen central case (ρ=0.05, m̄=112.5, realized cluster-structure priors); realized low side 1,718 ⇒ futility gate PASSES at freeze (1.6×); ρ=0.10 sensitivity acknowledged infeasible at realized counts | Full-fidelity re-run (`WILD_B=399`, `N_REP=2000`, **seed 20260706** — the registered §11 seed; the 20260622 rehearsal seed and its figures are retired), central-cell record in [power_run_2026-07-06.log](power_run_2026-07-06.log); [power_sim_2026-06-22.py](power_sim_2026-06-22.py) with M_BAR_GRID resolved to realized values. |
| Power-simulation priors (realized, outcome-blind) | mean hold **3.778 y**, holding CV **0.669**, segment-size shares (CV **1.429**) and per-segment high-side composition RESAMPLED from the frozen cell's realized vectors; `WINDOW_YEARS = 7.0` retained as the registered EFFECT-SCALE definition (not a data prior) | Per-segment evidence: [segment_structure_h002-frozen-cell_2026-07-06.csv](../../../data/interim/segment_structure_h002-frozen-cell_2026-07-06.csv) (dates/counts/geometry only). |
| Blind-window pair-geometry input (committed, price-free) | [pairs_geometry_h002_2026-07-06.parquet](../../../data/interim/pairs_geometry_h002_2026-07-06.parquet) — 39,871 pairs, NO price columns (p1/p2/log-relative dropped at export), checksummed in [data/_manifest.json](../../../data/_manifest.json) | Makes the outcome-blindness of the qualification/count/prior work STRUCTURAL and third-party reproducible (freeze-audit remediation). |
| Filename-convention deviation (recorded) | `crosswalk_boundary_rcdts_2026-07-06.csv` and `qualification_counts_2026-07-06.md` use underscores inside the description slot | Accepted as-is: both are cross-referenced from this frozen document; renaming post-hoc would break frozen links. |

---

## AI-assistance statement (ICMJE 2026)

Per [ICMJE Recommendations (updated January 2026)](https://www.icmje.org/recommendations/), AI is
**not** an author. This draft pre-registration was produced with **Claude Opus 4.8** (model id
`claude-opus-4-8`), role = **code + prose + audit** (rendering the 11-section design from the
SKIE-Universe template against the project's literature/schema substrate, with the repeat-sales
template-fit mapping; no new data analysis performed). The mechanism citations remain to be verified
via `/cite-add` before freeze (§11.1). Reproducibility envelope per the project contract at
[logs/reproducibility/](../../../logs/reproducibility/); the design.md SHA is computed only at the
`/preregister` freeze, not at this draft revision.
