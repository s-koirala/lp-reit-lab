# `web/src/lib/data/` — the data contract

The SPA renders **precomputed artifacts** (ADR-0003). Every module here is a
deterministic **synthetic fixture** today, but the exported TypeScript types are
the **contract** the real artifacts must satisfy. Swapping synthetic → real is a
fixture-body replacement behind unchanged types, plus flipping one flag.

## The single boundary

[`source.ts`](source.ts) exports:

- `DATA_SOURCE: "synthetic" | "real"` — the one switch. Nothing else in the app
  branches on real-vs-synthetic except via this flag / `DATA_PROVENANCE`, so the
  seam is greppable.
- `DATA_PROVENANCE` — user-facing label, vintage (`asOf`), and calibration/source
  basis. Surfaced by the global footer ([AppShell](../../components/AppShell.tsx))
  and the per-section [`ProvenanceNote`](../../components/ProvenanceNote.tsx).

## Modules = contract

| Module             | Exports (contract)                       | Real source when swapped                                                                 |
| ------------------ | ---------------------------------------- | ---------------------------------------------------------------------------------------- |
| `properties.ts`    | `Property`, `PROPERTIES`                 | hedonic/rent/DOM model **outputs** + listing facts (P5 artifact compiler + MLS/assessor) |
| `neighborhoods.ts` | `Neighborhood`, `NEIGHBORHOODS`          | Census ACS + Chicago community-area geo + submarket aggregates                           |
| `market.ts`        | `PRICE_INDEX`, `RENT_INDEX`, `LIQUIDITY` | FHFA HPI / repeat-sales, Zillow ZORI, MLS days-on-market                                 |

Note the split: the **deterministic finance engine** ([`../engine`](../engine)) is
already real and parity-gated (P2). What remains synthetic is the **model inputs**
the engine consumes (`predictedPrice`, `predictedRent`, `expectedAppreciation`,
…) — these are _fitted-model outputs_, produced by the forecast/MC artifact
compiler (P5, pre-registration-governed) once real data lands.

## Swap procedure (per module)

1. Replace the fixture body with a loader that imports the committed real artifact
   (JSON emitted by the Python compiler), keeping the exported type identical.
2. Ensure the artifact satisfies the type (a golden-vector-style check, as the
   engine config already uses).
3. Flip `DATA_SOURCE` to `"real"` and update `DATA_PROVENANCE`.

## Real-data readiness already in place

- Fail-closed scoring: `computeMetrics` returns a NO-GO sentinel for non-positive
  price/rent (real feeds can carry blanks) — see `properties.ts`.
- Empty states: the screener table, the map, and the market charts all render an
  explicit empty/loading state (synthetic fixtures are never empty; real feeds can
  be).
- Honesty: provenance + vintage in the global footer and on the data views (screener, market); Fair-Housing
  market-demand framing throughout.
