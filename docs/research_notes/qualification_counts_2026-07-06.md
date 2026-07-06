---
type: project
date: 2026-07-06
author: SKIE
status: DRAFT — freeze-time input to H002 §8 power re-run; unfrozen until `/preregister`
---

# Boundary-School ↔ ISBE RCDTS Crosswalk and Qualified-Segment Pair Counts (H002)

| Field | Value |
|---|---|
| Recipe (normative) | [docs/methodology/methodology_isbe-quality-recipe_2026-07-06.md](../methodology/methodology_isbe-quality-recipe_2026-07-06.md) §2 (qualification), §3 (label windows), §4.2 (crosswalk) |
| Crosswalk table | [data/interim/crosswalk_boundary_rcdts_2026-07-06.csv](../../data/interim/crosswalk_boundary_rcdts_2026-07-06.csv) |
| ReproLog | [logs/reproducibility/repro_log_313c6f9935e84d3b98cdeebefc5b37bc.json](../../logs/reproducibility/repro_log_313c6f9935e84d3b98cdeebefc5b37bc.json) (run_id `313c6f9935e84d3b98cdeebefc5b37bc`) |
| Blindness statement | **No sale price or log-relative column was read.** Inputs: pair dates, coordinates, school keys, segment keys, boundary distances (counts only), CPS boundary GeoJSONs, ISBE report cards. Per the design-before-outcomes principle (Rubin 2008, [10.1214/08-AOAS187](https://doi.org/10.1214/08-AOAS187)); pair-count-based granularity decisions at freeze are licensed by design §8. |

## 1. Crosswalk coverage

Needed set = union of both members of every boundary segment observed on repeat-sale
pairs with `dist_to_boundary_m ≤ 800` (36,307 pairs): **55 boundary keys**, of which
31 are CPS school-id keys and 24 are name keys (the SY0607/SY0708 boundary vintages
publish no `school_id`, so their resolved key is `school_nm` per
[src/lp_reit_lab/h002/boundaries.py](../../src/lp_reit_lab/h002/boundaries.py)
`_resolve_key_property`). The same physical border therefore appears under two
keyspaces; canonicalizing by matched-RCDTS pair collapses **89 keyspace segments to
57 physical segments**.

- **Matched: 55/55** (50 exact, 5 prefix, 0 token, 0 manual). **Unmatched: 0** — no forced matches were needed.
- Matching = normalized-name comparison (uppercase, punctuation stripped, generic
  tokens ELEM/ELEMENTARY/SCHOOL(S)/SCH/ACADEMY/ACAD/HS/HIGH dropped, token-level
  prefix equivalence for CPS truncations such as COMM≈COMMUNITY) between all boundary
  name variants (school_nm / short_name / schoolname across the 20 vintages) and all
  ISBE `school_name` variants per RCDTS pooled across rc2006–rc2025 (names drift).
- Parser benchmark: all 8 recipe §6 row-level rc2014 composites (Lincoln 91.8,
  Blaine 87.1, Burley 82.4, Alcott 83.4, Agassiz 66.6, Mayer 68.8, Nettelhorst 73.6,
  Prescott 63.3) reproduce exactly from
  [src/lp_reit_lab/h002/isbe.py](../../src/lp_reit_lab/h002/isbe.py).

### 1.1 Brief correction — school_id 610013 is not Oscar Mayer

The task brief identified Oscar Mayer as `school_id 610013`; in the CPS boundary
files 610013 is **PILSEN** (1420 W 17th St). Oscar Mayer is **`school_id 610059`**
(boundary names MAYER), matched **exact** to RCDTS `150162990252337`
(MAYER ELEM SCHOOL), covered in all 20/20 rc vintages. See §4.

### 1.2 Schools with ISBE coverage gaps (all lifecycle events, not match failures)

| boundary_key | boundary_names_seen | matched_rcdts | n_rc_years_covered | isbe_missing_rc_years |
|---|---|---|---|---|
| 609838 | CARPENTER | 150162990252121 | 6 | 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| 610012 | JENNER | 150162990252287 | 13 | 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| 610162 | SCHILLER | 150162990252440 | 4 | 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| 610187 | STEWART | 150162990252466 | 8 | 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| 610189 | STOCKTON | 150162990252470 | 8 | 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| CARPENTER | CARPENTER | 150162990252121 | 6 | 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| JENNER | JENNER | 150162990252287 | 13 | 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| LEMOYNE | LEMOYNE | 150162990252310 | 2 | 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| SCHILLER | SCHILLER | 150162990252440 | 4 | 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| STEWART | STEWART | 150162990252466 | 8 | 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |

Interpretation (recipe §4.2 — closures/mergers route into flip-exclusion, no bespoke
handling): SCHILLER closed 2009 (last rc2009); LEMOYNE last rc2007; CARPENTER last
rc2011; STEWART and STOCKTON closed in the 2013 CPS mass closure (last rc2013);
JENNER last rc2018 — consolidated into OGDEN (the Jenner polygon disappears from the
boundary file at SY1819; Ogden's RCDTS `150162990252380` continues 20/20). MANIERRE
additionally has FERPA-suppressed composites in rc2024–rc2025 (rank lapses those
vintages per recipe §4.1). A missing rank at any in-force vintage inside a pair's
holding window makes the segment non-qualifying for that pair (lapse → recipe §2.3).

## 2. G* candidates (recipe §2.2, computed outcome-blind)

Pooled cross-boundary gap distribution `|Δ(b, v)|`: 57 physical segments × published
vintages with both sides ranked (rc2020 carry-forward rows excluded so no assessment
year is double-weighted) → **n = 908** gap observations, quantiles
(5/25/50/75/95) = [1.35, 5.51, 13.46, 34.3, 75.84] percentile points. Including the rc2020 duplicates leaves
the break unchanged (36.170).

| Candidate | Rule | Value (percentile points) |
|---|---|---|
| `G_break` | Fisher 1958 exact k=2 partition ([10.1080/01621459.1958.10501479](https://doi.org/10.1080/01621459.1958.10501479)) = Jenks natural breaks, k=2; threshold = minimum of the upper cluster | **36.170** |
| `G_noise` | Kane–Staiger noise floor ([10.1257/089533002320950993](https://doi.org/10.1257/089533002320950993)): median absolute year-over-year within-school rank change, CPS elementary pool, COVID-gap-adjacent vintage pairs excluded | **4.944** |

> **SUPERSEDED (recipe §2.2 revision, 2026-07-06, pre-freeze):** this memo was computed under
> the draft composite rule `G* = max(G_break, G_noise)` = 36.170 (Jenks binding). The recipe was
> revised BEFORE the freeze — outcome-blind, rationale in
> [methodology_isbe-quality-recipe_2026-07-06.md](../methodology/methodology_isbe-quality-recipe_2026-07-06.md)
> §2.2 — to `G* = G_noise = 4.944` (confirmatory), with `G_break = 36.170` retained as the
> registered strong-gap SENSITIVITY partition. The `ks_noise` rows of the count grid below are
> therefore the CONFIRMATORY cells; the `jenks_k2` rows are the sensitivity cells. All numbers
> below are retained unmodified as computation evidence.

Both candidates are carried separately through the count grid below; the realized values are
pinned at freeze with the `|Δ|` histogram archived alongside (recipe §5).

## 3. Qualified-segment pair counts

Universe: repeat-sale pairs with `geom_stable`, `dist_to_boundary_m ≤ bandwidth`,
and an in-force ISBE label at both endpoints (40 pairs dated before the rc2006
window open on 2006-11-01 drop; 0 pairs lost to unmapped segments; 30,077 labelable
pairs at ≤ 800 m). Qualification (recipe §2.2): at vintage `v`,
`max(p_own, p_adj) ≥ 100 − q_top` **and** `|p_own − p_adj| ≥ G*`, with `p` the Hazen
percentile within the CPS elementary pool. Stability (recipe §3.2, strict reading):
qualification must hold and the high side must not flip at **every** in-force
vintage in `[t1, t2]` — a missing rank, a gap collapse, or a sign flip at any
intermediate vintage excludes the pair (design §1.2 flip exclusions).
`n_excl_stale_label` = the same count after additionally dropping pairs whose t1 or
t2 label is the rc2020 carry-forward (staleness sensitivity, recipe §2.3).

| q_top | G_rule | G_value | bandwidth_m | n_pairs_qualified_stable | n_hi_side | n_lo_side | n_segments_qualified | m_bar | n_excl_stale_label |
|---|---|---|---|---|---|---|---|---|---|
| 10.0 | jenks_k2 | 36.17 | 150 | 533 | 393 | 140 | 11 | 48.5 | 455 |
| 10.0 | jenks_k2 | 36.17 | 250 | 782 | 529 | 253 | 14 | 55.9 | 669 |
| 10.0 | jenks_k2 | 36.17 | 400 | 1029 | 720 | 309 | 16 | 64.3 | 872 |
| 10.0 | ks_noise | 4.944 | 150 | 2727 | 1669 | 1058 | 31 | 88.0 | 2367 |
| 10.0 | ks_noise | 4.944 | 250 | 4161 | 2443 | 1718 | 37 | 112.5 | 3603 |
| 10.0 | ks_noise | 4.944 | 400 | 5162 | 3037 | 2125 | 40 | 129.1 | 4492 |
| 20.0 | jenks_k2 | 36.17 | 150 | 1027 | 778 | 249 | 15 | 68.5 | 949 |
| 20.0 | jenks_k2 | 36.17 | 250 | 1532 | 1134 | 398 | 17 | 90.1 | 1419 |
| 20.0 | jenks_k2 | 36.17 | 400 | 2071 | 1590 | 481 | 18 | 115.1 | 1914 |
| 20.0 | ks_noise | 4.944 | 150 | 3540 | 2236 | 1304 | 34 | 104.1 | 3115 |
| 20.0 | ks_noise | 4.944 | 250 | 5354 | 3302 | 2052 | 42 | 127.5 | 4701 |
| 20.0 | ks_noise | 4.944 | 400 | 6768 | 4239 | 2529 | 44 | 153.8 | 5972 |
| 25.0 | jenks_k2 | 36.17 | 150 | 1431 | 1049 | 382 | 15 | 95.4 | 1187 |
| 25.0 | jenks_k2 | 36.17 | 250 | 2135 | 1542 | 593 | 17 | 125.6 | 1783 |
| 25.0 | jenks_k2 | 36.17 | 400 | 2901 | 2209 | 692 | 19 | 152.7 | 2409 |
| 25.0 | ks_noise | 4.944 | 150 | 3977 | 2520 | 1457 | 34 | 117.0 | 3384 |
| 25.0 | ks_noise | 4.944 | 250 | 6005 | 3734 | 2271 | 43 | 139.7 | 5111 |
| 25.0 | ks_noise | 4.944 | 400 | 7660 | 4896 | 2764 | 45 | 170.2 | 6525 |
| 33.3 | jenks_k2 | 36.17 | 150 | 1435 | 1053 | 382 | 15 | 95.7 | 1191 |
| 33.3 | jenks_k2 | 36.17 | 250 | 2146 | 1552 | 594 | 17 | 126.2 | 1794 |
| 33.3 | jenks_k2 | 36.17 | 400 | 2920 | 2227 | 693 | 19 | 153.7 | 2428 |
| 33.3 | ks_noise | 4.944 | 150 | 4014 | 2541 | 1473 | 34 | 118.1 | 3419 |
| 33.3 | ks_noise | 4.944 | 250 | 6063 | 3769 | 2294 | 43 | 141.0 | 5167 |
| 33.3 | ks_noise | 4.944 | 400 | 7736 | 4945 | 2791 | 45 | 171.9 | 6597 |

### 3.1 Interim read against the power target (selection happens at freeze, not here)

The recipe §2.2 `q_top` selection rule wants the **finest** ladder cutoff whose
qualifying set supports the registered per-side pair-count target (interim
239/side per [power_analysis_2026-06-22.md](../../research/01_hypothesis_register/H002/power_analysis_2026-06-22.md)).
Under the pre-revision composite rule (jenks_k2 rows — now the SENSITIVITY partition, see the
supersession note in §2), the binding side is `min(n_hi_side, n_lo_side)`:

| bandwidth_m | min_side_q10 | min_side_q20 | min_side_q25 | min_side_q33 | finest_qualifying_q_top |
|---|---|---|---|---|---|
| 150 | 140 | 249 | 382 | 382 | 20 |
| 250 | 253 | 398 | 593 | 594 | 10 |
| 400 | 309 | 481 | 692 | 693 | 10 |

These are interim counts against the interim target; the freeze-time §8 full-fidelity
power re-run (WILD_B=399, N_REP≥2000) re-pins `n_required_for_power_80` and the final
`q_top` before anything is frozen.

## 4. Oscar Mayer (the design's named boundary)

Crosswalk row: `610059` / MAYER → RCDTS `150162990252337` (MAYER ELEM SCHOOL),
match_method **exact**, 20/20 rc vintages covered. Mayer is the registered
boundary-magnet inclusion (recipe §2.1). Its Hazen percentile at rc2025 (latest
vintage) = **95.9** — top decile, so Mayer satisfies the
top-tier condition at every `q_top` in the ladder — segment-level qualification at
rc2025 therefore varies only with the G* rule (identical across the q_top grid):

| segment | p_A | p_B | gap | qualifies_jenks_k2 | qualifies_ks_noise |
|---|---|---|---|---|---|
| AGASSIZ-MAYER | 86.6 | 95.9 | 9.2 | False | True |
| ALCOTT-MAYER | 96.6 | 95.9 | 0.7 | False | False |
| BURR-MAYER | 90.9 | 95.9 | 5.0 | False | True |
| JENNER-MAYER | lapsed | 95.9 | n/a | False | False |
| LINCOLN-MAYER | 98.0 | 95.9 | 2.1 | False | False |
| MANIERRE-MAYER | lapsed | 95.9 | n/a | False | False |
| MAYER-OGDEN | 95.9 | 51.3 | 44.5 | True | True |
| MAYER-PRESCOTT | 95.9 | 95.6 | 0.2 | False | False |
| MAYER-PULASKI | 95.9 | 85.4 | 10.4 | False | True |
| MAYER-SCHILLER | 95.9 | lapsed | n/a | False | False |

Reading: at rc2025 the Mayer boundary qualifies **against OGDEN under both G* rules
at every q_top** (gap 44.5). Under the `ks_noise` candidate it additionally
qualifies against AGASSIZ/TUBMAN (9.2), BURR (5.0), and PULASKI (10.4). It never
qualifies against LINCOLN (2.1), ALCOTT (0.7), or PRESCOTT (0.2) — peer top-decile
schools with sub-noise gaps — and the JENNER, MANIERRE, and SCHILLER sides carry no
rc2025 rank (closure/suppression lapses, §1.2). Under the pre-revision composite
`G* = max = 36.170` (now the strong-gap SENSITIVITY), **Mayer–Ogden is the only qualifying
Mayer segment**, at every `q_top`; under the CONFIRMATORY `G* = G_noise = 4.944` Mayer
additionally qualifies vs Agassiz/Tubman, Burr, and Pulaski (see §4 grid).

## 5. Unmatched schools

None. All 55 needed boundary keys matched an ISBE CPS elementary RCDTS without
forcing (names tried are in `boundary_names_seen` of the crosswalk CSV).

## 6. Determinism and provenance

Inputs pinned by the ReproLog dataset checksums (feat_recon.parquet, the 20
elementary boundary GeoJSONs, the ISBE snapshot). Crosswalk CSV is sorted by
`boundary_key` (deterministic). No RNG anywhere in the pipeline. Recipe SHA-256 is
the ReproLog `config_resolved_sha256`.
