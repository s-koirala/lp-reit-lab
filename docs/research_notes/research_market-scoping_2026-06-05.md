# Market-Scoping & Methodology Memo — lp-reit-lab

| Field | Value |
|---|---|
| Document | `research_market-scoping_2026-06-05.md` |
| Author | SKIE (`s-koirala`) |
| Date | 2026-06-05 |
| Status | v1 — initial research scoping; round-1 audit-remediate applied (trail: `docs/audits/audit_trail_2026-06-05_market-scoping.md`) |
| Project kind | quant (now matched by `rules/quant-project.md` globs) |
| Reporting discipline | Quant-project rules (time-series integrity, HAC inference, multiple-testing gate) + TRIPOD-style transparency for the predictive models. Hypotheses pre-registered before fit. |
| AI-assistance | Drafted with Claude (Opus 4.8); 5 parallel web-research agents + audit-remediate loop. See README AI-assistance note. |

> **Provenance caveat.** Every dollar figure and current-market statistic below is **provisional**, carrying a source and as-of date. Several providers (Zillow, Redfin, Realtor.com, FRED series pages, IHS) return HTTP 403 to automated fetch; those numbers were read from the providers' own indexed pages and **must be re-pulled programmatically (sanctioned CSV / API) into the reproducibility log before any analytic use.** Open endpoints (Cook County Socrata `/resource`, Census API, FHFA, EPA, CTA GTFS) are scriptable without keys.

---

## 1. Purpose & estimands

Decision-support for buy-and-hold residential acquisition in Lincoln Park and adjacent North Side Chicago. Each candidate property is scored on two estimands:

1. **Long-run appreciation** — expected constant-quality price growth over a ~5–10 year hold.
2. **Net rental yield** — going-in capitalization rate (NOI ÷ price) and levered cash-on-cash / IRR on a family-tenant rental.

All other variables (supply/demand, walkability, transit, schools, amenities, carrying costs, demographics) enter as **covariates** of those two estimands or of a tenant-demand (rent/occupancy) model — never as instruments for selecting tenants (see §3).

**Primary tenant thesis (market-demand framing):** stable, dual-income, upper-middle-class families seeking 3BR+ units. Operationalized as *which configurations/locations the market rewards with higher rent, lower vacancy, and stronger appreciation* — a statement about the market, not about whom to lease to.

## 2. Geography & unit of analysis

- **Primary:** Lincoln Park (Chicago community area 7; ZIP 60614).
- **Adjacent:** Lake View / Lakeview (CA 6; 60657), Near North / Old Town (60610), and the LP sub-neighborhoods DePaul, Sheffield Neighbors, Wrightwood Neighbors, RANCH Triangle, Park West.
- **Nested geographic keys:** PIN → Census block group / tract → community area → ZIP. The Cook County Assessor **Parcel Universe** ([nj4t-kc8j](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Universe/nj4t-kc8j)) supplies `latitude`/`longitude`, ZIP, community area, and tract/block-group GEOIDs as the crosswalk.
- **Unit of analysis:** property × time panel. Repeat-sales pairs for the appreciation index; listing spells for time-on-market survival.
- **Property scope:** v1 focus 3BR condos/townhomes/single-family; architecture supports 1–2BR and houses.

## 3. Fair Housing compliance boundary (binding)

Familial status (households with children under 18, pregnant persons, those securing custody) is a **protected class** under the Fair Housing Act (42 U.S.C. §3604; added by the Fair Housing Amendments Act of 1988). This project sits entirely inside the **permitted** zone — *market-demand and property-economics analysis* — and must never cross into conduct toward persons.

**Permitted (this lab's activity):**
- Estimating which unit configurations / micro-locations / school-catchment quality command higher rent, sell faster, or appreciate more.
- Using **aggregate** ACS demographics (household-size distribution, income, tenure) as market-sizing covariates for rent/occupancy/appreciation forecasts.
- Inferring that a segment *values* a configuration **to forecast demand** ("3BR units near top-rated schools have lower vacancy in this tract").

**Prohibited (never produced, recommended, or implied):**
- **Tenant steering** — routing prospects toward/away from units by familial status (§3604(a)/(b)).
- **Screening/selection** — using familial status or facially-neutral proxies (e.g., occupancy limits below the recognized ~2-persons-per-bedroom standard; "adults-only" outside the narrow HOPA 55+/62+ exemptions) to accept/reject/set terms.
- **Advertising/statements (§3604(c))** — any listing language indicating a protected-class preference ("perfect for young professionals," "no children"). §3604(c) has **no** small-provider exemption.

**Disparate-impact status (as of 2026-06-05):** the statutory cause of action survives (*Texas Dept. of Housing v. Inclusive Communities Project*, 576 U.S. 519 (2015)). HUD's regulation 24 C.F.R. §100.500 is **in flux** — an NPRM to rescind it (91 Fed. Reg. 1475, 2026-01-14; comments closed 2026-02-13) is **pending, not final**, so the 2013 three-step burden-shifting framework remains operative. **Re-verify before any compliance-critical publication.** Any facially-neutral rule derived from the models that touches tenanting requires a documented legitimate-interest justification and less-discriminatory-alternative check.

Citations: [42 U.S.C. §3604](https://www.law.cornell.edu/uscode/text/42/3604); [FHAA 1988 (Pub. L. 100-430)](https://www.congress.gov/bill/100th-congress/house-bill/1158); [Inclusive Communities](https://www.law.cornell.edu/supremecourt/text/13-1371); [24 C.F.R. §100.500](https://www.law.cornell.edu/cfr/text/24/100.500); [HUD 2026 NPRM](https://www.federalregister.gov/documents/2026/01/14/2026-00590/).

## 4. Data-source register

Posture: **open/free-first.** Paid and ToS-restricted sources are catalogued but not load-bearing. Maintain a per-source license note in `data/_manifest.json` and a snapshot date for every pull.

### 4.1 Transactions, characteristics, assessment (Cook County — open, Socrata SODA API)
| Dataset | ID | Key fields | Cadence | URL |
|---|---|---|---|---|
| Assessor Parcel Sales | `wvhk-k5uv` | pin, sale_date, sale_price, class, nbhd, deed_type | monthly | [link](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Sales/wvhk-k5uv) |
| Assessor Assessed Values | `uzyt-m557` | mailed/certified/board land+bldg+tot, class | annual | [link](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Assessed-Values/uzyt-m557) |
| Single/Multi-Family Characteristics | `x54s-btds` | char_beds, char_fbath, char_bldg_sf, char_yrblt (≤6-unit; **not condos**) | annual | [link](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Single-and-Multi-Family-Improvement-Chara/x54s-btds) |
| Parcel Universe (geo crosswalk) | `nj4t-kc8j` | lat/lon, zip, community area, tract/block GEOIDs | monthly | [link](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Universe/nj4t-kc8j) |
| IL IDOR MyDec / PTAX-203 | data.illinois.gov | statutory sale_price/date origin | weekly | [link](https://tax.illinois.gov/localgovernments/property/mydecdatafiles.html) |

Access pattern: `https://datacatalog.cookcountyil.gov/resource/{id}.json?$where=...`; tooling at [github.com/ccao-data](https://github.com/ccao-data). **Gap:** condo bed/bath/sqft are **not** in CCAO open data (condos are a separate class); the 3BR-condo screen needs MLS or a parsed source.

### 4.2 Market price indices & supply/demand
| Source | Granularity | Notes | License |
|---|---|---|---|
| [Zillow Research](https://www.zillow.com/research/data/) ZHVI/ZORI/inventory | neighborhood, ZIP, metro; home-type + **bedroom (1–5BR)** cuts | trimmed-mean Zestimate index; supports a 3BR cut | attribution, no redistribution |
| [Redfin Data Center](https://www.redfin.com/news/data-center/) | down to neighborhood; property-type partition (Condo/SFR/Townhouse) | median price, $/sqft, inventory, months-supply, DOM, sale-to-list | free w/ citation |
| [Realtor.com Research](https://www.realtor.com/research/data/) | metro/county/ZIP | inventory, DOM, price; **Dec-2021 methodology break**; mirrored on FRED (Chicago CBSA `16980`) | citation required |
| [FHFA HPI](https://www.fhfa.gov/data/hpi) | MSA/division (Chicago `16980`) | **repeat-sales**, constant-quality; quarterly; public domain | public domain |
| [Case-Shiller Chicago](https://fred.stlouisfed.org/series/CHXRSA) | MSA only | repeat-sales, Jan-2000=100; via FRED | S&P licensed |
| **[DePaul IHS Cook County House Price Index](https://price-index.housingstudies.org/)** | 35 PUMA submarkets, quarterly | **hedonic, composition-controlled** — recommended local appreciation benchmark | open |
| [Chicago Building Permits](https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu) `ydr8-5enu` | parcel, lat/lon | new-construction pipeline; filter `permit_type='PERMIT - NEW CONSTRUCTION'` | open |

### 4.3 Rents
| Source | What | Caveat |
|---|---|---|
| [Zillow ZORI](https://www.zillow.com/research/data/) | repeat-rent index, ZIP-level, monthly | asking-rent, **blended across bedrooms** — trend not 3BR level |
| [HUD FMR / SAFMR](https://www.huduser.gov/portal/datasets/fmr.html) | Cook is mandatory **SAFMR** (ZIP) area; FY2025 metro 3BR = **$2,262** | 40th-pct gross-rent *floor*, not market asking; ZIP 3BR gated in HUD Excel |
| [Census ACS B25064/B25063](https://api.census.gov/data/2023/acs/acs5/groups/B25063.html) | median/dist gross rent, **tract-level** (5-yr) | stock-weighted (includes below-market legacy leases); **no bedroom dimension** (needs PUMS) |
| Aggregators (Zumper/RentCafe/RentHop) | neighborhood 3BR asking ~$4.1–5.0k LP | **ToS bars scraping**; manual context only |

### 4.4 Time-on-market (DOM)
- **For-sale DOM** is well-covered: [Redfin Data Center](https://www.redfin.com/news/data-center/) (neighborhood/ZIP) and Realtor.com via **FRED `MEDDAYONMAR16980`** (Chicago CBSA, programmatic, free). LP ZIP 60614 ≈ 56 days for-sale (Redfin, ~2026).
- **Rental days-to-lease is a structural gap** — no free/public neighborhood feed; lives in MLS (MRED), access-gated to licensed brokers. Proxy via aggregator listing recency or obtain via MLS agreement. This is the single biggest data gap for the family-tenant thesis.

### 4.5 Carrying-cost stack (cited typical values — to be parcel-verified)
| Item | Value/range | Basis | Source |
|---|---|---|---|
| Property tax — assessment mechanics | market × **10%** (Class 2) × **3.0355** equalizer − exemptions × local rate | statutory | [Assessor](https://www.cookcountyassessoril.gov/Chicago2024), [IL DOR equalizer](https://tax.illinois.gov/research/news/2024-cook-county-final-multiplier.html) |
| Property tax — effective rate | ~**1.66%** of market value (Chicago residential) | secondary | [SmartAsset](https://smartasset.com/taxes/cook-county-illinois-property-tax-calculator) |
| Homeowner exemption | −$10,000 EAV — **does NOT apply to a rental**; model full tax | statutory | [Assessor](https://www.cookcountyassessoril.gov/homeowner-exemption) |
| Reassessment cadence | Chicago reassessed **2024**; next **2027** | triennial | [ref](https://www.cutmytaxes.com/triennial-reassessments-explained/) |
| HOA / condo assessment | **$300–$600/mo** typical LP; listing/MLS-derived | secondary | [ref](https://condomanagement.com/what-are-the-average-hoa-fees-for-a-condo-association-in-chicago/) |
| Special-assessment risk | few hundred → ~$50k; frequent in **pre-1980** buildings; IL Condo Act §22.1 resale disclosure | statutory | [ref](https://www.fultongrace.com/blog/are-hoa-special-assessments-common-in-chicago-condos/) |
| Electric (ComEd) | EIA IL res. ~15.8→17.1¢/kWh (2025) | gov | [EIA IL](https://www.eia.gov/electricity/state/illinois/) |
| Gas (Peoples Gas) | ~$150+/mo heating season | secondary | [Crain's](https://www.chicagobusiness.com/utilities/average-peoples-gas-heating-bill-neared-four-figures-past-winter) |
| Water/sewer (Chicago) | ~$9.78 / 1,000 gal; **often bundled in HOA** (avoid double-count) | gov | [chicago.gov](https://www.chicago.gov/city/en/depts/fin/supp_info/utility-billing/water-and-sewer-rates.html) |
| Insurance — landlord HO-6/DP-3 | ~**$1,000–1,100/yr** (model landlord, not owner HO-6) | secondary | [Baselane](https://www.baselane.com/resources/illinois-landlord-insurance) |
| Vacancy allowance | metro ACS ~**5.1%** (model lower for LP 3BR family stock) | gov | [Census B25004](https://data.census.gov/table/ACSDT1Y2022.B25004) / [FRED ILRVAC](https://fred.stlouisfed.org/series/ILRVAC) |

### 4.6 Location: walkability, transit, amenities, schools
| Domain | Free/preferred | Paid/ToS-flagged |
|---|---|---|
| Walkability | **[EPA National Walkability Index](https://edg.epa.gov/EPADataCommons/public/OA/WalkabilityIndex.zip)** + Smart Location DB (block group, public domain) | Walk Score API ($115+/mo; **caching prohibited**) |
| Transit | **[CTA GTFS static](https://www.transitchicago.com/downloads/sch_data/google_transit.zip)** (no key) → distance-to-nearest-'L'; portal [8pix-ypme](https://data.cityofchicago.org/Transportation/CTA-System-Information-List-of-L-Stops/8pix-ypme); Divvy GBFS; Metra | CTA real-time API keys (not needed for buy-and-hold) |
| Amenities | **[OSM Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL)** (`around` radius, ODbL) + [Chicago Park District](https://data.cityofchicago.org/Parks-Recreation/Parks-Chicago-Park-District-Park-Boundaries-curren/ej32-qgdr) polygons | Google Places, Yelp Fusion |
| Schools | **CPS attendance-boundary GeoJSON** ([elem u959-tya7](https://data.cityofchicago.org/Education/CPS-elementary-school-attendance-boundaries/u959-tya7), [HS fkiq-5i7q](https://data.cityofchicago.org/Education/Chicago-Public-Schools-High-School-Attendance-Boun/fkiq-5i7q)) + [ISBE Illinois Report Card](https://www.isbe.net/ilreportcarddata) | GreatSchools (ToS) |

Key facts: North-Side four-track line serves **Red** (express; Fullerton, Belmont) + **Brown**/**Purple Express** (local: Armitage, Diversey, Wellington); **Fullerton** is the LP transfer node. Decisive family-tenant operation = **point-in-polygon of property → CPS attendance boundary**. Notable schools: **Lincoln Elementary** (top neighborhood draw), **Oscar Mayer** (the only CPS magnet with an *attendance boundary* — a documented price premium), **Newberry** (lottery magnet, Old Town), **Lincoln Park HS** (neighborhood + IB). **SQRP was retired (2025)** → reconstruct quality signal from ISBE Report Card metrics; legacy SQRP levels are historical-only.

### 4.7 Tenant-fit demographics (aggregate only — §3 boundary)
Census ACS (data.census.gov / API): B19013 median household income, B11003 family households with own children <18, B25003 tenure, B25004 vacancy — all tract-level (5-yr).

## 5. Current market snapshot (provisional; re-pull required)
| Metric | Geography | Value | YoY | As-of | Source |
|---|---|---|---|---|---|
| Median sale price | Lincoln Park | $700,000 | −5.9%* | Mar 2026 | [Redfin](https://www.redfin.com/neighborhood/28211/IL/Chicago/Lincoln-Park/housing-market) |
| Median $/sqft | Lincoln Park | $462 | +7.7% | Mar 2026 | Redfin |
| Median DOM (for-sale) | Lincoln Park | 47 days | ~flat | Mar 2026 | Redfin |
| ZHVI typical value | ZIP 60614 | $607,445 | +2.5% | Apr 2026 | [Zillow](https://www.zillow.com/home-values/84616/chicago-il-60614/) |
| Median sale price | Lake View (CA 6) | $520,000 | −0.4% | Mar 2026 | [Redfin](https://www.redfin.com/neighborhood/157585/IL/Chicago/Lake-View/housing-market) |
| Aggregator 3BR asking rent | Lincoln Park | ~$4.2–5.0k/mo | — | 2025–26 | aggregators (context only) |
| HUD FMR 3BR (floor) | Chicago metro | $2,262/mo | — | FY2025 | [HUD](https://www.huduser.gov/portal/datasets/fmr/fmr2025/FY2025_FMR_Schedule.pdf) |

\* The LP median −5.9% vs $/sqft +7.7% divergence is a **mix-shift artifact** (fewer high-end whole-home sales in the month); $/sqft and the IHS composition-controlled hedonic index are the more reliable appreciation signals. The City-of-Chicago median ($315k) is a citywide aggregate **not comparable** to LP — use neighborhood/ZIP series only.

## 6. Methodology (cited; no-arbitrary-threshold discipline)

All tunable values are data-derived or cited, never hand-set: Box-Cox λ by ML profile likelihood; HAC/Conley bandwidth at the distance where the residual Moran correlogram flattens (report sensitivity); block-bootstrap length disclosed; FDR q and scoring bands cited (§7–8).

- **Hedonic price & rent (Rosen 1974, [10.1086/260169](https://doi.org/10.1086/260169); Malpezzi 2003, [10.1002/9780470690680.ch5](https://doi.org/10.1002/9780470690680.ch5)).** Semi-log price/rent on structural + locational + neighborhood covariates with community-area/tract fixed effects; stage-1 reduced form (no stage-2 demand recovery needed for prediction). Box-Cox (1964) λ by ML; **cluster-robust SEs by submarket** (CR3 / wild-cluster bootstrap when clusters are few — Cameron-Gelbach-Miller 2008, [10.1162/rest.90.3.414](https://doi.org/10.1162/rest.90.3.414); *not* HC3, which assumes independence). Screen the collinear locational block (transit/walk/school) by VIF / condition index before interpreting coefficients.
- **Repeat-sales appreciation index (BMN 1963, [10.1080/01621459.1963.10480679](https://doi.org/10.1080/01621459.1963.10480679) — base log-difference estimator, OLS; Case-Shiller 1987/1989 add the 3-stage WLS holding-period heteroskedasticity correction; Calhoun 1996/FHFA the geometric weighting).** Constant-quality index from same-unit pairs. **Watch:** thin repeat-pair counts at sub-municipal scale inflate variance; index **revision** is a look-ahead trap (use the vintage knowable at decision time); filter renovation-contaminated pairs via a building-permit join (Chicago `ydr8-5enu`) between the two sale dates. Run hedonic + WRS in parallel as convergent validity.
- **Time-on-market survival (Cox 1972, [10.1111/j.2517-6161.1972.tb00899.x](https://doi.org/10.1111/j.2517-6161.1972.tb00899.x); AFT Wei 1992; PH diagnostics Grambsch-Therneau 1994, [10.1093/biomet/81.3.515](https://doi.org/10.1093/biomet/81.3.515); RE applications Kluger-Miller 1990, Anglin et al. 2003, Pryce-Gibb 2006).** Hazard of sale/lease on list-vs-value, configuration, micro-location, season; right-censoring native. Test scaled Schoenfeld residuals; if PH fails, stratify / time-interaction / switch to log-logistic AFT. Cluster SEs by PIN to handle repeated listing spells (Therneau-Grambsch robust variance).
- **Spatial dependence (Moran 1950; Conley 1999 spatial-HAC [10.1016/S0304-4076(98)00084-0](https://doi.org/10.1016/S0304-4076(98)00084-0); Anselin 1988; LeSage-Pace 2009).** Moran's I on hedonic residuals first; then **robust LM-lag vs LM-error (Anselin-Bera-Florax-Yoon 1996, [10.1016/0166-0462(95)02111-6](https://doi.org/10.1016/0166-0462(95)02111-6)) to identify the form.** If error-side (SEM) dependence dominates, Conley spatial-HAC SEs are the default fix (OLS stays consistent; only inference is corrected). If an endogenous spatial lag (SAR) dominates, OLS is **biased and inconsistent** and SAR/SDM estimation is required — report direct/indirect effects (LeSage-Pace 2009).
- **Investment math (Geltner, Miller, Clayton & Eichholtz, *Commercial RE Analysis & Investments*; CFA curriculum).** NOI, cap rate, cash-on-cash, DSCR, DCF/NPV, IRR (levered equity) — definitional, not tuned. Empirical discipline enters only when **forecasting inputs** (rent growth, exit cap, vacancy) from the §6 models.
- **Inference discipline (Benjamini-Hochberg 1995 FDR [10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x); Holm 1979; Efron 1979 bootstrap).** BH-FDR across the **whole pre-registered family** (Holm for the headline confirmatory claim); **block** bootstrap CIs (not i.i.d.) for serially dependent series; **walk-forward, never k-fold** (time + spatial leakage). Multiple-testing fixes inference; walk-forward fixes data leakage — both required.

## 7. Professional practice → KPI hierarchy (drives the UI)

Authoritative basis: Geltner et al.; CFA; USPAP three-approach valuation; practitioner tools (DealCheck, BiggerPockets, Roofstock, Mashvisor, Zillow/Redfin investor views). The convergent pattern: a compact KPI block + one composite risk signal above the fold; full model beneath (progressive disclosure).

**Tier 1 — above the fold (the 5 decision numbers):**
1. **Monthly cash flow ($)** — retail's anchor.
2. **Cash-on-cash return (%)** — return on actual dollars in (commonly-cited "good" 8–12%, *market-dependent*).
3. **Going-in cap rate (%) + spread over 10-yr Treasury** — price-vs-income sanity + headline risk gauge (normalized spread historically ~2–4%, [Wall Street Prep](https://www.wallstreetprep.com/knowledge/cap-rate-spread/); market-dependent).
4. **Levered 5–10yr IRR + equity multiple** — integrates cash flow + appreciation + financing + exit.
5. **DSCR** — financeability gate (<1.0 auto-no; ≥1.20–1.25 lender convention, *verify vs quotes*).

**Tier 2 — one screen down:** NOI + EGI→NOI→cash-flow waterfall; break-even occupancy ratio = (OpEx + debt service) / gross potential rent, flagged when >85–90% (rule-of-thumb screen, property-specific — read off the per-deal pro forma, not a fixed cutoff); LTV; GRM & OER for quick comp/efficiency framing; unlevered IRR (separates "good asset" from "good leverage").

**Tier 3 — risk flags (visual):** exit-cap sensitivity (the dominant tornado bar); P(negative return) from Monte Carlo on rent/vacancy/exit-cap/rate (the rate↔exit-cap correlation is a **placeholder to be estimated empirically** from paired 10-yr UST vs transaction-cap series and reported with CI — not a fixed prior); a Roofstock-style location composite (school/income/transit/amenity); rule-of-thumb tripwires (1%-rule, 50%-rule) **labeled "filter, not valuation."**

**Rules-of-thumb verdicts:** 1% rule = defensible *screen* (≈GRM ≤ 8.3), rare in appreciation-led metros like LP; 50% expense rule = defensible first-pass, *understates* in high-tax IL (verify line-by-line); 2% rule = folklore here; 70% rule = fix-and-flip, **out of scope**. Sources: [PropertyMetrics](https://propertymetrics.com/blog/real-estate-formulas/), [Geltner/Routledge](https://www.routledge.com/Commercial-Real-Estate-Analysis-for-Investment-Finance-and-Development/Geltner-Miller-VanDeMinne-Eichholtz-Lindenthal-Shen/p/book/9781041076391), [Wall Street Prep — cap-rate spread](https://www.wallstreetprep.com/knowledge/cap-rate-spread/).

> **UI design caveat (surface in-app):** every Tier-1 forward number (IRR, NPV, exit value) inherits three assumptions — **rent growth, exit cap rate, discount rate**. Expose those as the first-class sliders driving the sensitivity view; that is where professional underwriting concentrates scrutiny.

## 8. Deliverable & UX spec (stack = Streamlit + Quarto; see ADR-0002)

- **Interactive screener (Streamlit):** sidebar filters (neighborhood, beds=3BR default, price, min cap/cash-on-cash, max HOA) → ranked shortlist (great-tables, traffic-light go/no-go) → Folium/MapLibre map on **free OSM tiles** (property points by score; neighborhood choropleths for rent/price/appreciation; transit/walk/school overlays) → per-property drill-down (scorecard, DCF pro forma, amortization, comps, sensitivity tornado, carrying-cost stack).
- **Reproducible reports (Quarto, parameterized):** per-property deal memo, neighborhood profile, longitudinal market analysis → HTML/PDF, publishable as a static site to **Cloudflare Pages**.
- **Audience:** progressive disclosure (headline go/no-go → drill-down evidence) for a stats-literate non-specialist; honest uncertainty (CIs, P(loss)) shown accessibly.
- **Mapping:** Folium (small N) / pydeck (large N) on OSM/MapLibre; **no Mapbox lock-in**. Static report maps via matplotlib/contextily.

## 9. Data architecture recommendation
1. **Ingestion (open-first):** Socrata `/resource` (Cook County), Census API, FHFA/EPA/CTA GTFS direct download — all keyless, scriptable, logged with snapshot date + checksum into `data/_manifest.json`.
2. **Join spine:** Parcel Universe (`nj4t-kc8j`) lat/lon → block group (EPA walkability), GTFS stop distance, OSM amenity radius counts, CPS boundary point-in-polygon, ACS tract covariates.
3. **Structural gaps to design around (not hide):** (a) condo bed/bath/sqft absent from CCAO → MLS/parsed; (b) rental days-to-lease absent from free feeds → MLS or proxy; (c) HOA + special-assessment history per-listing only (IL Condo Act §22.1 disclosure docs at due-diligence). Each gap is a documented modeled-range input, not a silent imputation.
4. **No live ingestion in v0** — v0 runs on labeled **synthetic** data calibrated to the published aggregates in §5 (seeded, deterministic, regenerated from script; never implied to be real listings).

## 10. Hypothesis seeds (full register: `hypothesis_backlog.md`)
Each requires a citation/derivation and pre-registration before fit (no arbitrary thresholds). Initial Tier-1/2 candidates:
- **H1 (transit premium):** rent/price premium decays with network distance to nearest 'L' stop, controlling for configuration + tract FE (hedonic). Mechanism: accessibility capitalization (Rosen 1974).
- **H2 (school-catchment appreciation):** within-boundary properties for top-ISBE-rated / boundary-magnet (Oscar Mayer) schools show higher constant-quality appreciation. Mechanism: school-quality capitalization.
- **H3 (3BR liquidity):** 3BR family units exhibit shorter time-on-market / lower vacancy than 1–2BR in LP tracts (Cox survival). Mechanism: family-segment demand depth.
- **H4 (HOA drag):** higher HOA + special-assessment risk (pre-1980 vintage) materially lowers net yield at equal gross rent. Mechanism: carrying-cost capitalization.

## 11. Reproducibility plan
Every artifact-producing run emits a 13-field ReproLog (git HEAD, full pip-freeze SHA-256, dataset checksums, RNG seed, model hash, uv.lock env_id) per [emit-repro-log](https://github.com/s-koirala/dotfiles). Synthetic-data generation logs its seed; commits use `/commit-with-provenance` (Repro-Log-Path/SHA-256 + ICMJE AI-assistance trailers). Walk-forward splits, vintage-correct indices (no revision leakage), and `data/_manifest.json` checksums enforce point-in-time integrity.

## 12. Gaps, risks, open questions
- **Condo 3BR characteristics** and **rental days-to-lease** are not in free/public feeds → MLS (MRED) agreement is the highest-value paid acquisition to evaluate next.
- **HOA / special-assessment** data is per-listing; model as ranges with explicit uncertainty until MLS/disclosure ingestion.
- **Provider 403 blocking** (Zillow/Redfin/Realtor/IHS) → use sanctioned CSV/API + FRED mirrors; re-pull all §5 figures programmatically before analysis.
- **Disparate-impact regulation** (24 C.F.R. §100.500) rescission NPRM pending — track before publication.
- **Walk Score caching ban** → rely on EPA index; reserve any Walk Score calls for final-shortlist enrichment only.
- **Repeat-sales thin-cell instability** at LP scale → consider Bayesian/shrinkage variants; always cross-check vs IHS hedronic submarket index.

## References
Grouped DOIs/URLs are inline above. Primary method citations to be mirrored into `CITATION.cff` via `/cite-add`: Rosen 1974; Malpezzi 2003; Box-Cox 1964; Bailey-Muth-Nourse 1963; Case-Shiller 1987/1989; Calhoun 1996; Cox 1972; Grambsch-Therneau 1994; Wei 1992; Kluger-Miller 1990; Anglin et al. 2003; Pryce-Gibb 2006; Moran 1950; Conley 1999; Anselin 1988; LeSage-Pace 2009; Geltner et al.; Benjamini-Hochberg 1995; Holm 1979; Efron 1979.
