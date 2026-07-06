# Hypothesis backlog

Append-only register of research hypotheses for this project. Per
SKIE-Universe convention (verified via `gh api` 2026-05-15). New entries added
via [/hypothesis-new](https://github.com/s-koirala/dotfiles/tree/main/claude/commands/hypothesis-new.md)
(R3-1 — pending). Append-only: archived hypotheses retain their row with
`status: archived`.

## Status legend

| Status | Meaning |
|---|---|
| `proposed` | Logged in backlog; mechanism cited; not yet pre-registered |
| `designed` | Pre-registration frozen via /preregister (R3-2a); design.md SHA recorded |
| `validated` | validate-data PASS on input dataset |
| `powered` | power-analysis run; n meets registered effect-of-interest |
| `running` | walk-forward / fit in progress |
| `kpi-reported` | KPI report card emitted to reports/{HID}/ |
| `promoted` | passed multipletest-gate; deployed to production |
| `archived` | null result kept (no deletion per non-loss policy); see failure_log.md |

## Backlog

| HID | Tier | Title | Status | Mechanism citation | Notes |
|---|---|---|---|---|---|
| H001 | 1 | Transit premium: rent/price decays with network distance to nearest 'L' stop | proposed | Rosen 1974 ([10.1086/260169](https://doi.org/10.1086/260169)) | hedonic; control beds/sqft + tract FE; CTA GTFS distance \| DEFERRED 2026-06-22 — needs MLS structural attrs (beds/sqft) absent from CCAO open data; see methodology_data-feasibility_2026-06-22.md |
| H002 | 2 | School-catchment capitalization: top-ISBE / Oscar Mayer boundary raises constant-quality appreciation | designed | Black 1999 ([10.1162/003355399556070](https://doi.org/10.1162/003355399556070)) — verify via /cite-add | boundary point-in-polygon; repeat-sales index \| FROZEN 2026-07-06 via /preregister; frozen_sha256=2ff817cb9fb6; freeze ReproLog run_id=ac27dca8402e43a5846c26e1102b61d5; n_required=1,105/side vs realized low-side 1,718 (futility PASS); confirmatory = ELEMENTARY boundaries, q_top=10, G*=G_noise=4.944, 250 m |
| H003 | 1 | 3BR liquidity: 3BR units sell/lease faster than 1–2BR in LP tracts | proposed | Anglin-Rutherford-Springer 2003 ([10.1023/A:1021526332732](https://doi.org/10.1023/A:1021526332732)) | Cox survival; PIN-clustered SEs \| DEFERRED 2026-06-22 — needs MLS days-to-lease (DOM); MRED-gated |
| H004 | 2 | HOA drag: higher HOA + pre-1980 special-assessment risk lowers net yield at equal gross rent | proposed | Geltner et al. (NOI/cap capitalization) — verify via /cite-add | carrying-cost; IL Condo Act §22.1 disclosure \| DEFERRED 2026-06-22 — needs MLS HOA + special-assessment history; per-listing only |

## Tiers

- **Tier 1:** Mechanism well-cited in peer-reviewed lit; high prior probability.
- **Tier 2:** Mechanism plausible from theory; weaker empirical support.
- **Tier 3:** Exploratory; structural hypothesis testing the substrate.
- **Tier 4:** Methodology/gate hypotheses (e.g., multiple-testing family scope).
- **Tier 5:** Replication / reanalysis of prior work.

## Reserved ID blocks

To avoid HID collision across parallel exploration:

| Block | Range | Reserved for |
|---|---|---|
| Main | H001–H099 | core hypotheses |
| Reanalysis | H100–H199 | replication of prior work |
| Methodology | H900–H999 | gate / framework hypotheses |
