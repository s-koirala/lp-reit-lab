---
type: project
date: 2026-06-22
author: SKIE
---

# Data-Feasibility & Template-Fit Methodology Memo — lp-reit-lab

| Field | Value |
|---|---|
| Document | [docs/methodology/methodology_data-feasibility_2026-06-22.md](methodology_data-feasibility_2026-06-22.md) |
| Author | SKIE |
| Date | 2026-06-22 |
| Project kind | quant (matched by `rules/quant-project.md` globs) |
| Inputs | [hypothesis_backlog.md](../../hypothesis_backlog.md), [research memo](../research_notes/research_market-scoping_2026-06-05.md), [ingest schema](../../src/lp_reit_lab/ingest/schemas.py), [ADR-0001](../decisions/ADR-0001.md), [ADR-0003](../decisions/ADR-0003.md), [pre-registration template](~/.claude/skills/pre-register-hypothesis/assets/hypothesis_design_TEMPLATE.md) |
| Decision | Only **H002** is testable on currently-available open data. **H001 / H003 / H004** deferred pending MLS/MRED structural-attribute acquisition. |

---

## 1. Purpose

Gate which of the four backlog hypotheses H001–H004 ([hypothesis_backlog.md](../../hypothesis_backlog.md))
are testable on **currently-available open data** *before* any pre-registration freeze, power
analysis, or fit. The user-global execution order (ingest structure → validate method against
sources → implement → verify → document) and the project's pre-registration contract
([CLAUDE.md](../../CLAUDE.md) "Scope") both require that a hypothesis be *runnable on data that
actually exists* before it enters `/preregister`. Pre-registering a hypothesis whose required
fields are not in the open-data panel would freeze an un-runnable design and waste a HID
(designs are immutable post-freeze; any change requires a new HID — see the template preamble in
[hypothesis_design_TEMPLATE.md](~/.claude/skills/pre-register-hypothesis/assets/hypothesis_design_TEMPLATE.md)).

This memo is a **feasibility gate**, not an analysis. It produces a per-hypothesis verdict
(feasible-now / MLS-gated), names the missing fields explicitly, and — for the single feasible
hypothesis (H002) — maps the SKIE-Universe trading-strategy pre-registration template onto a
real-estate repeat-sales econometrics study so the downstream `/preregister` freeze can proceed
without template drift.

## 2. Open-data inventory

Posture inherited from [ADR-0001](../decisions/ADR-0001.md): open/free-first; paid/MLS sources
catalogued but not load-bearing. Point-in-time integrity per
[rules/quant-project.md](~/.claude/rules/quant-project.md) "Time-series integrity".

### 2.1 Primary panel — Cook County Assessor parcel sales (open, Socrata)

The ingested sales panel is the only transaction substrate. Its **exact** validated columns are
fixed by the pandera schema in
[src/lp_reit_lab/ingest/schemas.py](../../src/lp_reit_lab/ingest/schemas.py)
(`property_sales_schema`):

| Column | Type / check | Role | Source of truth |
|---|---|---|---|
| `pin` | `str`, `^\d{14}$`, non-null | 14-digit parcel id; the **repeat-sales pairing key** | schemas.py L34–36 |
| `sale_date` | `datetime64[ns]`, in `[sales_epoch_start, snapshot]`, non-null | event time; upper bound = snapshot ⇒ no-look-ahead enforced at the gate | schemas.py L37–42 |
| `sale_price` | `Int64`, `> 0`, non-null | whole-dollar USD; the **price relative numerator/denominator** | schemas.py L43–45 |
| `class` | `str`, non-null | CCAO property class (condo class is distinct; no structural attrs) | schemas.py L46 |
| `doc_no` | `str`, nullable, optional | CCAO deed id; stricter downstream dedup key | schemas.py L47 |
| `latitude` | `float64`, in county bounds, nullable | parcel-universe geo crosswalk for point-in-polygon | schemas.py L48–53 |
| `longitude` | `float64`, in county bounds, nullable | parcel-universe geo crosswalk for point-in-polygon | schemas.py L54–59 |
| (joined geography) | `strict=False` | community-area / tract / ZIP / block-group GEOIDs carried but not all modeled | schemas.py L60–61 |

What the panel does **not** contain — confirmed against the schema, not assumed: bedrooms,
bathrooms, building square footage, year built, days-on-market, days-to-lease, HOA/condo
assessment, special-assessment history, list price, rent. Condo structural characteristics are a
**separate, absent** dataset: the CCAO Single/Multi-Family Characteristics file (`x54s-btds`,
≤6-unit, **not condos**) does not cover the condo stock that dominates the Lincoln Park / Lakeview
3BR universe (research memo [§4.1](../research_notes/research_market-scoping_2026-06-05.md),
"condo bed/bath/sqft are **not** in CCAO open data (condos are a separate class)").

### 2.2 Auxiliary open sources required for H002 (school-catchment capitalization)

These are all keyless, scriptable, ToS-clean public sources (research memo
[§4.2](../research_notes/research_market-scoping_2026-06-05.md),
[§4.6](../research_notes/research_market-scoping_2026-06-05.md)):

| Source | Dataset id | Role in H002 | Notes |
|---|---|---|---|
| CPS elementary attendance boundaries | `u959-tya7` (GeoJSON) | point-in-polygon: assign each PIN to its elementary catchment at each sale date | research memo §4.6 |
| CPS high-school attendance boundaries | `fkiq-5i7q` (GeoJSON) | secondary catchment layer (e.g. Lincoln Park HS / IB) | research memo §4.6 |
| ISBE Illinois Report Card | `isbe.net/ilreportcarddata` | school-quality signal; **SQRP retired 2025** ⇒ reconstruct quality from ISBE metrics (legacy SQRP levels historical-only) | research memo §4.6 |
| Chicago building permits | `ydr8-5enu` | renovation-contamination filter: drop repeat-sale pairs with a major permit **between** the two sale dates | research memo §4.2, §6 (repeat-sales bullet) |

The decisive operation for H002 is documented in the research memo §4.6: "point-in-polygon of
property → CPS attendance boundary". The renovation-permit join is the documented mitigation for
the repeat-sales constant-quality assumption (research memo §6: "filter renovation-contaminated
pairs via a building-permit join (Chicago `ydr8-5enu`) between the two sale dates").

## 3. Per-hypothesis feasibility table

Required-field set per hypothesis is derived from the estimator named in
[hypothesis_backlog.md](../../hypothesis_backlog.md) and research memo
[§6](../research_notes/research_market-scoping_2026-06-05.md) /
[§10](../research_notes/research_market-scoping_2026-06-05.md).

| HID | Estimator (backlog) | Required fields | Available in open panel? | Verdict | Missing fields (named) | Gap citation |
|---|---|---|---|---|---|---|
| **H001** transit premium | Hedonic semi-log on structural + locational covariates, tract FE (Rosen 1974) | `sale_price`, geo, **`beds`, `sqft`** (structural controls), CTA-GTFS distance | No — structural controls absent | **MLS-gated** | `beds`, `bathrooms`, `building_sf`, `year_built` | research memo [§4.1](../research_notes/research_market-scoping_2026-06-05.md) (condo bed/bath/sqft absent from CCAO open data) |
| **H002** school-catchment capitalization | **Repeat-sales index** (BMN 1963 / Case-Shiller WLS / Calhoun) + boundary point-in-polygon | `pin`, `sale_date`, `sale_price`, `lat`/`lon`; CPS boundaries `u959-tya7`/`fkiq-5i7q`; ISBE; permits `ydr8-5enu` | **Yes** — all present | **FEASIBLE-NOW** | none | — (repeat-sales differences out time-invariant unit quality ⇒ no structural attrs needed; research memo [§6](../research_notes/research_market-scoping_2026-06-05.md) repeat-sales bullet) |
| **H003** 3BR liquidity | Cox PH survival on days-to-lease, PIN-clustered SEs (Anglin-Rutherford-Springer 2003) | event-time **`days_to_lease`** (or for-sale DOM), configuration `beds` | No — duration outcome and beds absent | **MLS-gated** | `days_to_lease` / rental DOM, `beds` | research memo [§4.4](../research_notes/research_market-scoping_2026-06-05.md) ("rental days-to-lease is a structural gap … lives in MLS (MRED)") |
| **H004** HOA drag on net yield | Carrying-cost / cap-rate capitalization (Geltner et al.) | **`hoa_fee`**, **`special_assessment_history`**, gross rent, `beds` | No — HOA and assessment data absent | **MLS-gated** | `hoa_fee`, `special_assessment` (pre-1980 vintage flag), gross rent | research memo [§4.5](../research_notes/research_market-scoping_2026-06-05.md) (HOA per-listing/MLS; IL Condo Act §22.1 disclosure only at due-diligence) |

**Why H002 alone clears the gate.** The repeat-sales estimator (Bailey-Muth-Nourse 1963; the
Case-Shiller 1987/1989 WLS holding-period correction; Calhoun 1996 / FHFA weighting — research
memo §6) regresses the **log price relative of two sales of the same PIN** on time dummies. Because
the within-pair difference cancels every time-invariant unit attribute (beds, bath, sqft, vintage,
fixed micro-location quality), the estimator needs **none** of the MLS-gated structural fields that
block H001/H003/H004. H002's only inputs are sale pairs (present: `pin` + `sale_date` +
`sale_price`), a point-in-polygon catchment assignment (present: `lat`/`lon` + CPS GeoJSON), a
quality signal (present: ISBE), and a contamination filter (present: permits `ydr8-5enu`). The
documented risks — thin sub-municipal repeat-pair counts inflating variance, and index-revision
look-ahead — are inference/point-in-time issues handled in design, not feasibility blockers
(research memo §6, §12).

## 4. Conclusion

**Only H002 is feasible on currently-available open data.** H001, H003, and H004 each require at
least one MLS/MRED-gated field (condo structural attributes; rental days-to-lease; HOA and
special-assessment history) that is verifiably absent from the open panel
([schemas.py](../../src/lp_reit_lab/ingest/schemas.py)) and from CCAO open data (research memo
§4.1/§4.4/§4.5). They are **deferred** — not rejected — pending the MLS/MRED acquisition the
research memo §12 already flags as the highest-value next paid acquisition. The memory note
"highest-value next acquisition = MLS/MRED" is consistent with this gate.

## 5. Template-fit note (pre-registration template → repeat-sales study)

The project pre-registration template
([hypothesis_design_TEMPLATE.md](~/.claude/skills/pre-register-hypothesis/assets/hypothesis_design_TEMPLATE.md))
is ported verbatim from **SKIE-Universe**, where every hypothesis is a **trading strategy**:
triple-barrier labeling (López de Prado AFML §3.2), profit-take/stop-loss multipliers, a slippage
& commission cost model, and a Deflated-Sharpe activation gate. H002 is a **real-estate
repeat-sales econometrics study** producing a constant-quality price index and a boundary-effect
coefficient — there is no position, no trade, no Sharpe. The 11 section headers MUST be kept for
template fidelity and the downstream `/preregister` freeze (the freeze computes a SHA over the
rendered 11-section document; dropping a header would break the contract and the immutability
guarantee). The mapping below is therefore **header-preserving**: transfer-verbatim sections carry
their meaning unchanged; adapted sections keep the header and add an explicit
`N/A for an index study, mapped to <X>` note.

### 5.1 Sections that transfer verbatim

| § | Header | Why it transfers unchanged |
|---|---|---|
| 1 | Hypothesis | H0/H1 in sign-and-magnitude form + mechanism + primary citation is domain-neutral. H002 mechanism = school-quality capitalization, cited Black 1999 ([10.1162/003355399556070](https://doi.org/10.1162/003355399556070)) — verify via `/cite-add` ([hypothesis_backlog.md](../../hypothesis_backlog.md) H002 row). |
| 2 | Universe and sample period | Instruments → the CCAO sale-pair universe (LP CA 7 / Lakeview CA 6 / Near North CA 8); frequency → quarterly index periods; time-ordered disjoint train/val/test, walk-forward only. Transfers verbatim. |
| 8 | Gate thresholds | `alpha`, BH-FDR `bh_threshold`, power target transfer directly (BH-FDR across the pre-registered family per research memo §6). **`dsr_activation_size` (Deflated Sharpe)** is the one sub-field that is N/A — see §5.2 note on §8. |
| 9 | Stopping rule | Fixed number of walk-forward folds / calendar budget / futility-vs-power transfers; "Sharpe is reporting-only" clause is simply inert (no Sharpe here). |
| 10 | Decision rule | Gate-outcome → archival label (positive / null / null-underpowered), non-loss policy, multiple-testing note. Domain-neutral; transfers verbatim. |
| 11 | Reproducibility commitments | git HEAD, pip-freeze SHA, RNG seed (pre-registered, not modifiable), dataset checksums from `data/_manifest.json`, ReproLog path, design.md SHA at freeze. Transfers verbatim. |

### 5.2 Sections that must be ADAPTED (header kept; `N/A … mapped to <X>` note)

| § | Header | Adaptation note (verbatim style for the design.md) |
|---|---|---|
| 3 | Features | `N/A for an index study (no FEATURE_REGISTRY trading features), mapped to`: covariate / boundary modules — (a) CPS attendance-boundary point-in-polygon assignment per PIN per sale date (`u959-tya7`, `fkiq-5i7q`); (b) ISBE Report Card quality signal (SQRP retired 2025 → reconstructed); (c) building-permit renovation flag (`ydr8-5enu`). Point-in-time property test still required. |
| 4 | Label construction | `N/A — no triple-barrier (pt_sl / vertical_barrier / volatility_estimator), mapped to`: outcome = **log price relative of repeat-sale pairs** of the same PIN, `log(p_t2) − log(p_t1)`. No profit-take/stop-loss, no meta-label horizon; the "holding period" is the inter-sale interval, which feeds the splitter purge (see §6). |
| 5 | Estimator | `mapped to`: **repeat-sales WLS index** (BMN 1963 base log-difference OLS; Case-Shiller 1987/1989 3-stage WLS holding-period heteroskedasticity correction; Calhoun 1996/FHFA geometric weighting) **and/or boundary fixed-effects hedonic** as convergent validity (research memo §6). Inference: cluster-robust SEs by submarket (CGM 2008 wild-cluster bootstrap when clusters few; [10.1162/rest.90.3.414](https://doi.org/10.1162/rest.90.3.414)) and/or Conley 1999 spatial-HAC ([10.1016/S0304-4076(98)00084-0](https://doi.org/10.1016/S0304-4076(98)00084-0)); block-bootstrap CIs on the index. Clustering LEVEL is the **boundary segment** (not the G≈3 community-area level, which is in the small-G regime where CR asymptotics and the wild bootstrap both fail) — Webb 2014 six-point weights for the small-G wild bootstrap, with Conley spatial-HAC as the primary when G_segment is still small (design.md §5). "Hyperparameter grid fixed at pre-reg; search nested in walk-forward" transfers. |
| 6 | Splitter | `mapped to`: time-ordered **walk-forward over `sale_date`** (never k-fold). **Purge = on overlapping holding periods** — a repeat-sale pair spans two dates; any pair whose [t1, t2] interval straddles the train/test boundary is purged to prevent leakage of the test-period index into training. **Embargo** data-driven (residual PACF vs Politis-White block length, max — template §6 wording transfers). Renovation-contaminated pairs removed pre-split (`ydr8-5enu`). |
| 7 | Cost model | `N/A for an index study — no trading, no slippage, no commission`. No `cost_model_id`. State explicitly that transaction costs are out of scope (this is an index/coefficient estimate, not a tradable strategy); the section header is retained with the N/A note for freeze fidelity. |
| 8 | Gate thresholds (sub-field) | `alpha` / `bh_threshold` / power transfer (see §5.1); **`dsr_activation_size` = N/A (no Sharpe), mapped to**: the headline confirmatory boundary-effect claim is gated by Holm; the family by BH-FDR (research memo §6). Hansen 2005 SPA / White 2000 reality check are reserved for strategy-return framings and do **not** apply to a single index/coefficient estimand. |

Net: sections 1, 2, 9, 10, 11 transfer verbatim; section 8 transfers except the DSR sub-field;
sections 3, 4, 5, 6, 7 are adapted with explicit N/A-mapped notes. All 11 headers are retained.

## 6. Disposition recommendations

1. **H002 — pre-register now (DRAFT pending freeze).** Render the 11-section design.md from the
   template using the §5 mapping, status `proposed` → `designed` only at the `/preregister` freeze.
   Before freeze: (a) verify the Black 1999 mechanism citation via `/cite-add`
   ([hypothesis_backlog.md](../../hypothesis_backlog.md) H002 note already flags "verify via
   /cite-add"); (b) run the prospective power analysis (`power-analysis` skill) on real repeat-pair
   counts — sub-municipal thin-cell variance (research memo §6, §12) makes power non-trivial and
   retrospective power is forbidden (Hoenig & Heisey 2001); (c) register the H002 effect in the
   multiple-testing family (`config/multipletest_family.yaml`) under BH-FDR before fit.
2. **H001 / H003 / H004 — annotate as deferred.** Add a `deferred: MLS/MRED-gated` note to each row
   in [hypothesis_backlog.md](../../hypothesis_backlog.md) (status stays `proposed`; do not
   pre-register — freezing an un-runnable design wastes a HID). Re-gate each when the MLS/MRED
   acquisition lands and the missing fields (§3 table) enter the validated panel.

## AI-assistance statement (ICMJE 2026)

Per [ICMJE Recommendations (updated January 2026)](https://www.icmje.org/recommendations/): AI is
not an author. This memo was produced with **Claude Opus 4.8** (model id `claude-opus-4-8`), role =
**audit + prose** (feasibility gating against existing literature/schema substrate and drafting; no
new data analysis performed). Reproducibility envelope per project contract at
`logs/reproducibility/`.
