---
type: project
date: 2026-07-06
author: SKIE
status: DRAFT — pre-freeze input to the H002 design; unfrozen until `/preregister`
---

# `isbe_quality` Reconstruction Recipe — Pre-Specified Treatment-Signal Methodology (H002)

| Field | Value |
|---|---|
| Document | [docs/methodology/methodology_isbe-quality-recipe_2026-07-06.md](methodology_isbe-quality-recipe_2026-07-06.md) |
| Author | SKIE |
| Date | 2026-07-06 |
| Hypothesis | H002 — [design.md](../../research/01_hypothesis_register/H002/design.md) §1.2 (treatment-label vintage), §2 (roll-handling), §3 (`isbe_quality`) |
| Data inspected | [data/raw/isbe_report_card/snapshot=2026-07-06/](../../data/raw/isbe_report_card/) — rc2006–rc2017 zip+layout files, rc2018–rc2025 xlsx workbooks (20 vintages) |
| Blindness statement | **No sale-price data was opened in preparing this recipe.** The Cook County panel ([data/raw/cook_county/](../../data/raw/cook_county/)) was not read. Every rule below is defined on school-side and geography-side data only, per the design-before-outcomes principle (Rubin 2008, [10.1214/08-AOAS187](https://doi.org/10.1214/08-AOAS187)). |
| Verification | Field/sheet names verified **against the raw files** for rc2006, rc2010, rc2012, rc2014, rc2015, rc2016, rc2017 (layouts + row-level reads of the delimited data), rc2018, rc2019, rc2020, rc2021, rc2022, rc2024, rc2025 (workbook headers + CPS row samples). See §6 verification log. |
| Status | DRAFT for operator review. At freeze this file's SHA-256 is pinned and design.md §3 references it; post-freeze changes require a new HID. |

---

## 1. Signal definition and per-era metric mapping

### 1.1 What the signal is

`isbe_quality(s, v)` is a **within-year cross-sectional percentile rank**: the rank of school `s`
among CPS attendance-area schools of the same level (elementary vs high school) in report-card
vintage `v`, computed on that vintage's published proficiency composite. It does two jobs in H002
([design.md](../../research/01_hypothesis_register/H002/design.md) §3):

1. **Qualification** — selects which CPS attendance-boundary segments qualify as "top-ISBE" (§2 below).
2. **Rank-ordering** — orders boundary pairs by cross-boundary quality gap for reporting and for
   the §2 gap rule.

### 1.2 Why within-year ranks, not raw levels

The Illinois assessment regime breaks four times inside the panel: ISAT/PSAE (≤2014) → PARCC
(2015–2018) → IAR+SAT (2019–2024) → IAR+ACT (2025), with a COVID assessment waiver in SY2019-20.
Raw proficiency levels are **not scale-comparable across regimes** (e.g., statewide
meets-and-exceeds fell from roughly 60–80% under ISAT to roughly 30% under PARCC — a cut-score
artifact, not a real quality collapse). A percentile rank is invariant to **any monotone
transformation of the score scale**, so regime changes can distort the treatment label only by
genuinely re-ordering schools, not by moving the scale:

- Ho 2009, *A Nonparametric Framework for Comparing Trends and Gaps Across Tests*, JEBS 34(2)
  ([10.3102/1076998609332755](https://doi.org/10.3102/1076998609332755)) — rank/ordinal statistics
  are the appropriate basis for comparisons **across different tests**.
- Ho & Reardon 2012, JEBS 37(4)
  ([10.3102/1076998611411918](https://doi.org/10.3102/1076998611411918)) — ordinal methods on
  proficiency-category data are robust to the test-metric assumptions that break under regime change.
- Reardon, Kalogrides & Ho 2021, JEBS 46(2)
  ([10.3102/1076998619874089](https://doi.org/10.3102/1076998619874089)) — aggregate-level linking
  of heterogeneous test scales; supports treating within-year relative position as the stable object.
- Precedent for coarse/relative treatment coding in the capitalization literature: Black 1999 used
  raw test scores in a **single-regime** window
  ([10.1162/003355399556070](https://doi.org/10.1162/003355399556070)); Bogin & Nguyen-Hoang 2014 —
  the H002 licensing citation — used a **designation** (NCLB "failing" label), i.e., an ordinal
  signal, not a scale score ([10.1111/jors.12141](https://doi.org/10.1111/jors.12141)); Figlio &
  Lucas 2004 used letter grades ([10.1257/0002828041464489](https://doi.org/10.1257/0002828041464489)).
  A rank/tier signal is the norm when the metric regime is not constant.

**Rank convention (pinned):** percentile `p = 100 × (r − 0.5) / n`, with mid-ranks for ties
(Hazen plotting position; type 5 in Hyndman & Fan 1996,
[10.1080/00031305.1996.10473566](https://doi.org/10.1080/00031305.1996.10473566)). Chosen because
it is symmetric, avoids the degenerate 0/100 endpoints, and is deterministic under ties.
`# justify: convention selection from the Hyndman-Fan taxonomy, not a tuned parameter; rank ORDER is identical under any type.`

### 1.3 Per-era metric mapping (verified against the raw files)

The **score** ranked within each vintage is the school-level "all students"
proficiency composite for the school's accountability assessment(s), exactly as published in that
vintage. One score per school per vintage; subject-level fields are combined by unweighted mean
where no combined field is published (justification below).

| RC vintage | School year | Regime | Elementary score | High-school score | Verified field/sheet (raw file) |
|---|---|---|---|---|---|
| rc2006–rc2014 | SY2005-06 – SY2013-14 | ISAT (elem) / PSAE (HS) | `ALL TESTS {yr} SCHOOL COMPOSITE PERCENT FOR MEETS & EXCEEDS` | same field (composite pools all state tests taken at the school) | rc2006 layout field #588; rc2010 #696; rc2012 #851; rc2014 #895. Semicolon-delimited `rc{yy}.txt`; field index = layout field number − 1. Row-level check: Lincoln Elem 91.8 / Lincoln Park HS 72.8 (rc14, 2014 composite). |
| rc2015–rc2016 | SY2014-15 – SY2015-16 | PARCC (elem + HS) | `{yr} ELA/MATH SCHOOL - STUDENTS MET EXPECTATIONS` **+** `... EXCEEDED EXPECTATIONS` (levels 4+5) | same (HS took PARCC both years) | rc2015 layout Assessment fields #390+#391; rc2016 #398+#399. Row-level check: Lincoln Elem 50.9+29.1, LP HS 32.9+3.2 (rc16). |
| rc2017 | SY2016-17 | PARCC (elem) / SAT (HS) | PARCC `MET` + `EXCEEDED` (fields #422+#423) | SAT `{yr} ELA/MATH SCHOOL MEETS STANDARDS` + `... EXCEEDS STANDARDS` (fields #481+#482) | Row-level check: Lincoln Elem PARCC 50.0+33.4; LP HS SAT 46.1+12.6; PARCC fields empty for HS — confirms the 2017 HS switch. |
| rc2018 | SY2017-18 | PARCC (elem) / SAT (HS) | `ELA Proficiency Total %`, `Math Proficiency Total %` — sheet `ELA and Math` | same fields (ISBE publishes one unified proficiency pair spanning the underlying assessments) | rc2018 xlsx, sheet `ELA and Math` c22/c44; `General` c11 = `Summative Designation` (ESSA designations begin). |
| rc2019 | SY2018-19 | IAR (elem) / SAT (HS) | `% ELA Proficiency`, `% Math Proficiency` — sheet `ELA Math Science` | same | rc2019 xlsx verified. |
| rc2020 | SY2019-20 | **COVID waiver — no assessment** | none published (sheet `ELA Math Science` carries **no** proficiency columns — verified absent) | none | Carry-forward rule §2.3. `General` republishes the 2019-derived designations. |
| rc2021 | SY2020-21 | IAR / SAT, depressed participation | `% ELA Proficiency`, `% Math Proficiency` (published; values verified) | same | `Summative Designation` = `Not Calculated` (verified). Low-participation flag §2.4. |
| rc2022–rc2024 | SY2021-22 – SY2023-24 | IAR (elem) / SAT (HS) | `% ELA Proficiency`, `% Math Proficiency` — sheet `ELA Math Science` / `ELAMathScience` | same | rc2022 c29/c65; rc2024 c10/c28 verified. FERPA `*` observed in-file (rc2024). |
| rc2025 | SY2024-25 | IAR (elem) / **ACT** (HS) | `% ELA Proficiency`, `% Math Proficiency` — sheet `ELAMathScience` | same (ACT feeds the unified fields; `ACT` sheet carries grade-11 detail) | rc2025 verified: `ACT ELA/Math Proficiency Rate Grade 11` present; unified `%` fields present. |

Mapping rules pinned by this table:

- **Resolve fields by description string, not by hard-coded position.** Zip-era field numbers
  drift year to year (e.g., the ALL TESTS composite is field #588 in rc2006 but #895 in rc2014);
  the loader must locate each field by matching the layout-workbook description, then map to the
  delimited-file index (field number − 1). The layout workbooks shipped in the snapshot are the
  official ISBE record layouts and are the source of truth
  ([ISBE Report Card Data Library](https://www.isbe.net/ilreportcarddata)).
- **Always take the current-year field from each vintage, never a later file's restatement.**
  Each zip-era file publishes current **and** prior-year values (rc14 carries 2013 and 2014
  composites — verified). Taking restated history from a later vintage is exactly the revision
  look-ahead the design's §2 roll-handling rule forbids.
- **Subject combination 2018+:** score = unweighted mean of `% ELA Proficiency` and
  `% Math Proficiency`. Justification: (a) it mirrors the pooled ELA+math composite ISBE itself
  published in 2006–2017 (the `ELA/MATH` and `read and math` composite fields above), so the
  combined object is era-consistent; (b) at freeze, report the Spearman correlation between
  ELA-only and math-only within-year ranks over the CPS pool — school-level subject ranks are
  strongly concordant, so any fixed positive weighting yields near-identical percentile ranks;
  ELA-only and math-only ranks are registered **sensitivities** (§5). `# justify: equal weight = the published-composite convention 2006–2017 carried forward; concordance quantified at freeze rather than asserted.`
- **Composite-definition drift inside the ISAT/PSAE era is absorbed by the rank.** The published
  composite includes science through rc2012 (`read,math,sci`) and drops to `read and math` by rc2014
  (verified in the layouts). Within a vintage every school is scored on the same definition, so
  the within-year rank is unaffected; no cross-era level comparison is ever made.
- **Growth percentiles and ESSA designations are NOT the primary signal.** Growth (2018+ era)
  moves between sheets across years (verified: `ELA and Math` in rc2018, `ELA Math Science` in
  rc2022, `IAR (2)` in rc2024/rc2025), exists only post-2017, and measures a different estimand
  (value-added vs attainment). Summative designations exist only 2018+ and are too coarse to
  rank-order North Side CPS schools — in rc2022, 399 of 624 CPS schools are `Commendable`
  (verified) — so they cannot discriminate at a boundary. Both are retained as **diagnostics**
  (§4.5), not treatment inputs. SQRP (CPS's own rating) was retired in 2025 and is historical-only
  per [design.md](../../research/01_hypothesis_register/H002/design.md) §3; it never enters.

## 2. "Top-ISBE" segment qualification rule

### 2.1 Rank pool

The percentile in §1 is computed within the pool of **CPS attendance-area schools of the same
level in the same vintage**:

- CPS filter: RCDTS prefix `150162990` (City of Chicago SD 299; verified key format, 15-digit
  string, school rows only — `Type = School` in 2018+ workbooks, school-type code in zip era).
- Level pool membership is derived from the **CPS boundary GeoJSON join, not the ISBE type string**:
  the elementary pool is the set of schools serving polygons in the elementary attendance-boundary
  file (`u959-tya7`), the HS pool from the HS file (`fkiq-5i7q`)
  ([research memo §4.6](../research_notes/research_market-scoping_2026-06-05.md)). Rationale: the
  ISBE `School Type` taxonomy drifts (`ELEMENTARY`/`CHARTER SCH` through rc2022 vs
  `Elementary School`/no charter type in rc2024 — verified), while boundary-file membership is
  exactly the treatment-relevant universe. The type string is a cross-check only.
- **Charter / magnet / selective-enrollment exclusion is structural:** schools without an
  attendance-boundary polygon in the in-force boundary vintage never join the pool. Charters,
  citywide magnets, and selective-enrollment schools assign by lottery/testing, not geography, so
  no parcel is "on their side" of a boundary. Belt-and-suspenders: rows with zip-era type code `C`
  (`CHARTER SCH`, verified) or 2018–2022 `School Type = CHARTER SCH` are dropped before the join.
  **Oscar Mayer is the registered exception** — the one CPS magnet **with** an attendance boundary
  ([research memo §4.6](../research_notes/research_market-scoping_2026-06-05.md)); it joins the
  boundary file and therefore stays in the pool. `PreK` and `Special School` rows (no tested
  grades) drop out structurally for the same reason.

### 2.2 Qualification rule (pre-specified)

A boundary segment `b` with schools `s_hi`, `s_lo` on its two sides **qualifies as top-ISBE at
vintage `v`** iff:

1. **Top-tier condition:** `p(s_hi, v) ≥ 100 − q_top`, i.e., the high side is in the top `q_top`
   percent of the within-vintage CPS pool for its level; and
2. **Material-gap condition:** `Δ(b, v) = p(s_hi, v) − p(s_lo, v) ≥ G*`.

Both parameters are pinned by **rule**, not by hand:

- **`q_top` (top-tier cutoff) — data-driven at freeze.** Selection rule: the **finest** cutoff in
  the standard-quantile ladder `{10, 20, 25, 33.3}` such that the qualifying segment set supports
  the registered power target (≥ n_required repeat-sale **pair counts** per side from the §8 power
  re-run at freeze; interim 239/side per
  [power_analysis_2026-06-22.md](../../research/01_hypothesis_register/H002/power_analysis_2026-06-22.md)).
  Ladder justification: 10 = ISBE's own `Exemplary` tier (top 10% statewide,
  [ISBE summative designations](https://www.isbe.net/summative)) — the official precedent for
  quantile tiering; 25 = the quartile stated in the H002 hypothesis text; 20 / 33.3 = the adjacent
  standard quantiles bracketing it. Pair **counts** use sale dates and geography only — never
  prices — so the selection stays outcome-blind (Rubin 2008; design §8 already licenses
  count-based granularity decisions at freeze).
- **`G*` (gap threshold) — data-driven at freeze; noise-floor rule (REVISED 2026-07-06,
  pre-freeze, outcome-blind):**
  `G* = G_noise`, where
  - `G_noise` = the median absolute year-over-year within-school rank change over the CPS pool
    (all vintage-adjacent pairs, COVID-gap-adjacent pairs excluded). A "materially lower" adjacent
    side must differ by more than typical measurement noise in school-level aggregates — the noise
    floor is motivated by the documented volatility of small-school accountability measures (Kane
    & Staiger 2002, [10.1257/089533002320950993](https://doi.org/10.1257/089533002320950993)).
    **Realized 2026-07-06: `G_noise = 4.944` percentile points.**
  - `G_break` — the two-group optimal-partition break (Fisher 1958 exact 1-D grouping,
    [10.1080/01621459.1958.10501479](https://doi.org/10.1080/01621459.1958.10501479); Jenks k = 2)
    of pooled `|Δ(b, v)|` — is retained as a **registered SENSITIVITY partition**, not the
    confirmatory gate: the "strong-gap" segment subset (`|Δ| ≥ G_break`) is reported alongside the
    confirmatory estimate. **Realized 2026-07-06: `G_break = 36.170` percentile points (n = 908
    segment×vintage gaps).**

  **Why the earlier draft's `max(G_break, G_noise)` composite was revised (documented per the
  no-silent-respec rule; decided OUTCOME-BLIND — only school-side ranks and pair COUNTS were
  consumed, never prices; Rubin 2008 design-trumps-analysis):** the two components answer
  different questions. The noise floor answers *"is the cross-boundary quality difference real
  (above measurement error)?"* — which is the qualification's actual job under §1 of the design.
  The Fisher/Jenks k=2 split point answers *"where does the pooled gap distribution cluster?"* —
  a distributional-shape statistic that, realized at 36.170 points on a bimodal gap distribution,
  would demand near-extreme-tail contrasts: it collapses the confirmatory design to
  G_segment ≈ 14–19 qualifying segments (re-entering the small-G regime the design's §5
  segment-clustering choice exists to escape) with low-side pair counts (249–398 across the
  bandwidth grid) below the Kish-forecast clustered requirement at the realized mean cluster
  sizes (m̄ ≈ 56–126 ⇒ DEFF-scaled n/side ≈ 420–810 — in every case above the realized low-side
  counts). Under `G* = G_noise` the finest ladder rung
  (q_top = 10) at the 250 m band yields low-side 1,718 pairs over G = 37 segments (m̄ = 112.5) —
  a design that is both scientifically faithful (gaps exceed measurement noise) and prospectively
  powered. This is a pre-registration DESIGN choice made before any outcome data is consumed and
  is subject to the freeze audit; the strong-gap sensitivity preserves the changepoint's
  information content.
  Both components are computed from school-side data only (outcome-blind) and their realized
  values are pinned in the freeze block (§5) with the full `|Δ|` histogram archived alongside
  ([qualification_counts_2026-07-06.md](../research_notes/qualification_counts_2026-07-06.md)).
- **Rank-ordering of qualifying pairs** (the second job of the signal) is by `Δ(b, v)` descending;
  no additional parameter.

### 2.3 COVID-year handling — carry-forward with staleness flag (RECOMMENDED)

rc2020 publishes **no assessment** (verified: the proficiency columns are absent from the SY2019-20
workbook; federal waiver). Two candidate policies were considered:

| Policy | Effect |
|---|---|
| **Carry-forward last-published rank + staleness flag** (recommended) | The rc2019 rank stays in force through the window where no newer assessment exists; sales keep their labels. |
| Exclude sales in the unlabeled window | Drops roughly a year of transactions from a panel whose power binds at 239 pairs/side. |

**Recommendation: carry-forward.** Justification, in order of weight:

1. **It is the information set, not an imputation.** The treatment mechanism is capitalization of
   *published* school-quality signals (Figlio & Lucas 2004,
   [10.1257/0002828041464489](https://doi.org/10.1257/0002828041464489); Bogin & Nguyen-Hoang 2014,
   [10.1111/jors.12141](https://doi.org/10.1111/jors.12141)). During Nov 2020 – Oct 2021 the
   latest school-quality signal any buyer could observe **was** the 2019 report card; the
   carried-forward rank is exactly the label "in force" under the §3 publication-date rule.
2. **ISBE itself carried forward:** the rc2020 `General` sheet republishes the 2019-derived
   summative designations (verified: `Commendable`/`Comprehensive` values present), and rc2021
   designations are `Not Calculated` — the state treated the 2019 signal as the operative one.
3. **Power:** excluding the window burns sample the §8 power budget cannot spare.

Mechanics: each in-force label carries `staleness = number of missed assessment vintages`
(0 in normal years; 1 for the rc2019 rank while in force through the rc2020 window). Staleness is
capped by the **observed** maximum publication gap in the vintage series — one missed vintage (the
2020 waiver is the only gap; verified across all 20 files) — so `staleness_cap = 1`; a label older
than that lapses and the segment is non-qualifying until a new vintage publishes.
`# justify: cap equals the maximum gap the data actually contains; nothing is extrapolated beyond an observed regime.`
**Registered sensitivity (diagnostic, not a new family member):** re-run the confirmatory
estimate excluding sales whose in-force label has `staleness ≥ 1`.

### 2.4 SY2020-21 depressed participation

rc2021 proficiency is published (verified) but participation was depressed and differentially so
across schools (remote-learning year). Primary analysis uses the published rc2021 ranks — again the
information-set argument: buyers in Nov 2021 – Oct 2022 saw these numbers. The vintage carries a
`low_participation` flag, and a registered **sensitivity** extends the rc2019 carry-forward through
the rc2021 window (i.e., treats rc2021 like rc2020). Participation-rate fields exist in the
workbooks if a finer diagnostic is wanted at freeze; none enters the primary label.

## 3. Time-varying label protocol (point-in-time rule)

### 3.1 Publication convention — verified

- **Statute:** 105 ILCS 5/10-17a (Better Schools Accountability Law) requires ISBE to **prepare
  the report cards by October 31** of each year ("By October 31, 2013 and October 31 of each
  subsequent school year..."; pre-2013 text: "completed and disseminated prior to October 31 in
  each school year") — [ilga.gov full text](https://www.ilga.gov/legislation/ilcs/fulltext.asp?DocName=010500050K10-17a).
  Districts must disseminate locally by November 30 (same section).
- **Observed releases:** 2024 Illinois Report Card published October 30, 2024 (embargo lifted
  9 a.m. Oct 30 — [ISBE media briefing](https://www.isbe.net/Documents_TAC/2024-IL-Report-Card-Media-Briefing.pdf));
  2023 released October 30, 2023; 2025 release announced via
  [IASB](https://www.iasb.com/news-listing/isbe-announces-release-of-2025-illinois-report-car).
  All verified releases fall on or before the statutory October 31.

### 3.2 The rule (REGISTERED)

RC vintage `N` covers SY `(N−1)–N` (assessments administered spring of calendar year `N`) and is
published by October 31 of calendar year `N`. Therefore:

> **The `isbe_quality` label in force on `sale_date` t is the rank from RC vintage `N` where
> `N` is the largest vintage year with `effective_from(N) ≤ t`, and
> `effective_from(N) = November 1 of calendar year N`** (with a per-vintage override to the
> documented release date if a year's release is ever found to post-date October 31 — a freeze-time
> verification sweep enumerates any such exceptions; none found for the verified years).

Properties:

- **Publication date, not school-year coverage, drives the label** — a sale in June 2015 is
  labeled by rc2014 (published Oct 2014), *not* rc2015 (published Oct 2015, after the sale), even
  though SY2014-15 was in session at sale time. Using coverage would inject roughly six months of
  look-ahead per vintage.
- **November 1 is conservative:** every verified state release precedes it, so the rule never
  assumes information before it was public; at most it delays label availability by a few days
  (Oct 27–31 releases). This is the same "vintage knowable at decision time" discipline as the §2
  roll-handling rule in [design.md](../../research/01_hypothesis_register/H002/design.md).
- **COVID interaction:** rc2020 exists as a vintage but carries no assessment; under §2.3 the rank
  in force during [Nov 1 2020, Oct 31 2021] is the carried-forward rc2019 rank with `staleness = 1`.
- **Panel epoch:** sales dated before the first in-force vintage in the snapshot
  (before Nov 1, 2006) have no label; pairs with an unlabeled sale are excluded from the
  confirmatory set (both sales of a pair must carry an in-force label).
- **Pair stability (from design §1.2, restated for completeness):** the confirmatory set requires a
  **stable side label across the pair's holding interval** `[t1, t2]`; segments whose top-ISBE
  status flips between the vintages in force at `t1` and `t2` are excluded and reported separately
  as a sensitivity. The flip test is evaluated on the qualification rule of §2.2 at each in-force
  vintage in `[t1, t2]`.

## 4. Edge-case handling

### 4.1 FERPA-suppressed cells

Small cells are suppressed as `*` in the 2018+ workbooks (verified in rc2024 school rows) and as
blank/space-padded fields in the zip era. Rule: `*` and blank both parse to missing. A school-vintage
with a missing composite gets **no rank that vintage**; the §2.3 carry-forward applies (last
published rank, `staleness += 1`, lapse beyond `staleness_cap`). At the "All Students" school level
suppression is rare for CPS attendance-area schools (enrollments far exceed suppression thresholds);
the ingest validation step counts suppressed school-vintages and the count is archived at freeze.

### 4.2 School openings, closures, mergers (incl. the 2013 CPS mass closure)

- **Openings:** a school is ranked from its first vintage with published data; no backfill (backfill
  would be look-ahead by construction).
- **Closures/mergers** (CPS closed ~50 schools in 2013): the school's rank series ends at its last
  published vintage. Geography is governed separately by the **boundary GeoJSON vintage in force on
  the sale date** (design §2 roll-handling): when a closed school's territory is absorbed, the
  in-force boundary vintage re-assigns parcels to the receiving school, whose own rank then labels
  the segment. A pair whose holding interval straddles the re-assignment is a **label flip** and is
  excluded from the confirmatory set under the design §1.2 flip rule — no bespoke handling needed;
  the flip machinery already covers it.
- **RCDTS re-keying:** the 15-digit RCDTS school suffix is stable for continuing schools (verified:
  Lincoln Elem `150162990252314` constant across inspected vintages), but administrative re-keying
  can occur on reorganization. Rule: the ingest step builds a per-vintage crosswalk
  RCDTS ↔ CPS school ID (the boundary GeoJSONs carry CPS school IDs) via the CPS school-profile
  open dataset plus deterministic name normalization; unresolved re-keys are treated as
  closure + opening (which routes them into the flip-exclusion machinery). The crosswalk table is
  committed with the data manifest and checksummed in [data/_manifest.json](../../data/_manifest.json).

### 4.3 Charter / magnet / selective-enrollment exclusion

Handled structurally in §2.1: no attendance-boundary polygon → never in the rank pool, never a
segment side. The zip-era `C` type code and 2018–2022 `CHARTER SCH` type provide a redundant
pre-join drop. Oscar Mayer (boundary magnet) is the registered inclusion.

### 4.4 Middle schools and level assignment

CPS is overwhelmingly K-8 + HS (rc2022: 420 elementary vs 1 middle school row — verified). Level
pools derive from boundary-file membership (§2.1), so a middle school enters only if it serves a
polygon in one of the two boundary files for the relevant vintage; the handful of CPS
`Middle/Junior High School` rows otherwise drop out structurally.

### 4.5 Diagnostics that do NOT gate

Reported at freeze for transparency, never used for qualification: (a) concordance of the §2.2
qualifying set with ESSA summative designations (2018+ — a top-ISBE side carrying
`Comprehensive`/`Intensive` would flag a recipe defect); (b) Spearman correlation between ELA-only
and math-only ranks (§1.3); (c) year-over-year rank-stability distribution (the `G_noise` input);
(d) growth-percentile cross-tabulation (2018+ era only).

## 5. Freeze block

Parameters pinned at the data-gated `/preregister` freeze
([design.md](../../research/01_hypothesis_register/H002/design.md) §11.1). Values marked
**data-driven** are computed by the stated rule on the ingested (outcome-blind) school/geography
data at freeze and the realized numbers written into the frozen design.

| Parameter | Value / rule | Justification |
|---|---|---|
| Score fields per vintage | §1.3 table (resolve by layout-description string) | Verified against raw files (§6); official ISBE layouts are source of truth. |
| Percentile convention | Hazen `100·(r−0.5)/n`, mid-ranks for ties | Hyndman & Fan 1996 type 5; symmetric, endpoint-free, deterministic (§1.2). |
| Subject weights (2018+) | 0.5 ELA / 0.5 Math | Mirrors the published pooled composite of 2006–2017; concordance quantified at freeze; ELA-only / Math-only as sensitivities (§1.3). |
| Rank pool | CPS attendance-area schools, same level, same vintage; pool membership by boundary-file join | §2.1; treatment-relevant universe; robust to ISBE type-taxonomy drift. |
| `q_top` | **data-driven at freeze**: finest of `{10, 20, 25, 33.3}` satisfying the §8 pair-count power target (interim 239/side) | Ladder anchored on ISBE Exemplary (10%) and the hypothesis quartile (25); selection uses counts, never prices (§2.2). |
| `G*` | **`G_noise` = 4.944 pts (realized 2026-07-06)**; `G_break` = 36.170 pts retained as the registered strong-gap SENSITIVITY partition (rule revised pre-freeze, outcome-blind — §2.2) | Kane & Staiger 2002 noise floor = the material-difference criterion; Fisher 1958 changepoint kept as robustness subset; revision rationale + realized small-G/power forecast documented in §2.2; histogram archived. |
| COVID policy | Carry-forward + staleness flag | Information-set argument (Figlio & Lucas 2004), ISBE's own carry-forward, power (§2.3). |
| `staleness_cap` | 1 missed vintage | Equals the maximum observed publication gap in the 20-vintage series (§2.3). |
| Label effective date | Nov 1 of RC year `N` → Oct 31 of `N+1`; per-vintage override to documented release date if later than Oct 31 (freeze-time sweep) | 105 ILCS 5/10-17a statutory Oct 31 + verified Oct 27–30 releases; conservative no-look-ahead (§3). |
| rc2021 policy | Published ranks, `low_participation` flag; carry-forward sensitivity | §2.4. |
| FERPA/missing | `*`/blank → missing → carry-forward under `staleness_cap`, else lapse | §4.1. |
| Crosswalk | RCDTS ↔ CPS school ID table, committed + checksummed | §4.2. |
| Sensitivity family status | All sensitivities in this memo are **diagnostics**, not confirmatory tests — the registered family stays m = 4 per [config/multipletest_family.yaml](../../config/multipletest_family.yaml) | Prevents silent family inflation. |

## 6. Verification log (what was actually opened)

All checks run read-only on
[data/raw/isbe_report_card/snapshot=2026-07-06/](../../data/raw/isbe_report_card/); no Cook County
file was touched. Ephemeral `openpyxl`/`xlrd` via `uv run --with` (not added to the lockfile).

| Check | Result |
|---|---|
| Sheet inventories, rc2018–rc2025 (8 workbooks, via workbook.xml) | §1.3 table; rc2020 has only 4 sheets (no assessment sheets beyond `ELA Math Science` shell). |
| rc2018 headers: `General`, `ELA and Math`, `PARCC`, `SAT` | `Summative Designation` c11; `ELA Proficiency Total %` c22; `Math Proficiency Total %` c44; growth `%` fields c55/c66. |
| rc2019/rc2021/rc2022/rc2024/rc2025 headers | `% ELA Proficiency` / `% Math Proficiency` located per year; growth-percentile fields migrate across sheets (rc2022 `ELA Math Science` c83/c101; rc2024 `IAR (2)` c282/c300; rc2025 `IAR` c571+). |
| rc2020 COVID check (CPS school rows) | No proficiency columns exist; `General` republishes 2019-derived designations (`Commendable` etc.). rc2021 designation = `Not Calculated`, proficiency published (Amundsen HS 25.9/23.6). |
| Zip-era file format | `rc{yy}.txt` inside each zip is **semicolon-delimited** with fields ordered by layout row (space-padded to layout widths); not fixed-width. Field index = layout field number − 1. |
| School-type codes (rc14, full state) | `0` = HIGH SCHOOL (654), `1` = MIDDLE SCHL (619), `2` = ELEMENTARY (2456), `C` = CHARTER SCH (65). |
| ALL TESTS composite, zip era | rc2006 #588, rc2010 #696, rc2012 #851 (`read,math,sci`), rc2014 #895 (`read and math`). Row check (rc14): Lincoln Elem 91.8, Blaine 87.1, Burley 82.4, Alcott 83.4, Agassiz 66.6, Mayer 68.8, Nettelhorst 73.6, Prescott 63.3, LP HS 72.8; 565 CPS rows. |
| PARCC era | rc2015 #390/#391, rc2016 #398/#399 (`ELA/MATH SCHOOL MET/EXCEEDED EXPECTATIONS`); rc2016 row check Lincoln Elem 50.9+29.1, LP HS 32.9+3.2. |
| 2017 HS switch | rc2017 PARCC fields empty for LP HS; SAT `MEETS`+`EXCEEDS` (#481/#482) = 46.1+12.6; Lincoln Elem PARCC 50.0+33.4. |
| CPS taxonomy drift | rc2022 `School Type`: ELEMENTARY 420 / HIGH SCHOOL 88 / CHARTER SCH 112 / MIDDLE SCHL 1 / PreK 3. rc2024: Elementary School 468 / High School 142 / Middle-Junior 6 / Special 6 — **no charter type** → boundary-join is the load-bearing exclusion (§2.1). |
| Designation coarseness | rc2022 CPS: Commendable 399, Comprehensive 115, Targeted 81, Exemplary 17; rc2024 adds `Intensive` (39). |
| Publication convention | Statute + 2023/2024/2025 release records (§3.1 links). |

## 7. Open items for the freeze sweep

1. Compute and pin `q_top`, `G_break`, `G_noise`, and the subject-rank concordance on the ingested
   panel; archive the `|Δ|` histogram and YoY rank-change distribution beside the frozen design.
2. Freeze-time release-date sweep: enumerate documented ISBE release dates per vintage (Wayback /
   ISBE press archive) and record any post-Oct-31 exception (none expected; none found 2018–2025).
3. Build and checksum the RCDTS ↔ CPS school-ID crosswalk (§4.2) during ingestion.
4. Wire the recipe into the pit-canary run required by design §3 before any fit (the ISBE join is
   one of the three registered leakage surfaces).

## References

- Black, S.E. 1999. Do Better Schools Matter? Parental Valuation of Elementary Education. *QJE* 114(2). [10.1162/003355399556070](https://doi.org/10.1162/003355399556070)
- Bogin, A. & Nguyen-Hoang, P. 2014. Property Left Behind: An Unintended Consequence of a No Child Left Behind "Failing" School Designation. *J. Regional Science* 54(5). [10.1111/jors.12141](https://doi.org/10.1111/jors.12141)
- Figlio, D.N. & Lucas, M.E. 2004. What's in a Grade? School Report Cards and the Housing Market. *AER* 94(3). [10.1257/0002828041464489](https://doi.org/10.1257/0002828041464489)
- Fisher, W.D. 1958. On Grouping for Maximum Homogeneity. *JASA* 53(284). [10.1080/01621459.1958.10501479](https://doi.org/10.1080/01621459.1958.10501479)
- Ho, A.D. 2009. A Nonparametric Framework for Comparing Trends and Gaps Across Tests. *JEBS* 34(2). [10.3102/1076998609332755](https://doi.org/10.3102/1076998609332755)
- Ho, A.D. & Reardon, S.F. 2012. Estimating Achievement Gaps From Test Scores Reported in Ordinal Proficiency Categories. *JEBS* 37(4). [10.3102/1076998611411918](https://doi.org/10.3102/1076998611411918)
- Hyndman, R.J. & Fan, Y. 1996. Sample Quantiles in Statistical Packages. *Am. Statistician* 50(4). [10.1080/00031305.1996.10473566](https://doi.org/10.1080/00031305.1996.10473566)
- Kane, T.J. & Staiger, D.O. 2002. The Promise and Pitfalls of Using Imprecise School Accountability Measures. *J. Econ. Perspectives* 16(4). [10.1257/089533002320950993](https://doi.org/10.1257/089533002320950993)
- Reardon, S.F., Kalogrides, D. & Ho, A.D. 2021. Validation Methods for Aggregate-Level Test Scale Linking. *JEBS* 46(2). [10.3102/1076998619874089](https://doi.org/10.3102/1076998619874089)
- Rubin, D.B. 2008. For Objective Causal Inference, Design Trumps Analysis. *Ann. Appl. Stat.* 2(3). [10.1214/08-AOAS187](https://doi.org/10.1214/08-AOAS187)
- 105 ILCS 5/10-17a (Better Schools Accountability Law). [ilga.gov](https://www.ilga.gov/legislation/ilcs/fulltext.asp?DocName=010500050K10-17a)
- ISBE Report Card Data Library (layouts + public data sets). [isbe.net/ilreportcarddata](https://www.isbe.net/ilreportcarddata)
- ISBE Summative Designations (ESSA tiers). [isbe.net/summative](https://www.isbe.net/summative)
- ISBE 2024 Report Card media briefing (release/embargo timing). [isbe.net](https://www.isbe.net/Documents_TAC/2024-IL-Report-Card-Media-Briefing.pdf)
