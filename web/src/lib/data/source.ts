// Single boundary for the synthetic -> real data swap.
//
// Per ADR-0003 the SPA renders precomputed Python-engine artifacts. Today every
// module in this folder is a deterministic synthetic fixture calibrated to
// published aggregates; the TypeScript types here ARE the contract the real
// artifacts must satisfy. When the ingestion lane + the forecast/MC artifact
// compiler (P5) land, the swap is: replace the fixture bodies with loaders that
// read the committed artifacts (same exported types), and flip DATA_SOURCE.
// Nothing else in the app should branch on real-vs-synthetic except via this flag
// and DATA_PROVENANCE, so the seam is greppable and the UI stays honest.

export type DataSource = "synthetic" | "real";

export const DATA_SOURCE: DataSource = "synthetic";

export interface DataProvenance {
  source: DataSource;
  /** Short user-facing label. */
  label: string;
  /** ISO date the fixtures were calibrated / the artifacts were built. */
  asOf: string;
  /** What the data is calibrated to (synthetic) or sourced from (real). */
  basis: string;
}

export const DATA_PROVENANCE: DataProvenance = {
  source: DATA_SOURCE,
  label: DATA_SOURCE === "synthetic" ? "Synthetic demonstration data" : "Real market data",
  asOf: "2026-06-05",
  // Truthful, non-overclaiming: the fixtures are hand-set to be representative of
  // Chicago North Side levels — illustrative, NOT derived from any specific feed.
  // (The real sources each module will draw from once swapped are listed in
  // web/src/lib/data/README.md.) Must stay consistent with methodology.tsx §08.
  basis:
    "Hand-set to be representative of Chicago North Side price and rent levels — illustrative only, not derived from a specific dataset. No real listing is referenced.",
};
