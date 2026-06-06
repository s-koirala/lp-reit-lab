# Audit trail — P4: data-contract boundary + provenance/empty-state polish

- **Date:** 2026-06-06
- **Artifact:** `web/src/lib/data/source.ts` (+ `README.md`), `web/src/components/ProvenanceNote.tsx`, `web/src/components/{AppShell,PropertyMap}.tsx`, `web/src/routes/{index,market}.tsx`.
- **Loop:** audit-remediate — 2 rounds (cap 3). Auditor: format-auditor (right-sized: P4 is a provenance/contract/honesty phase; the React code is small and verified green by tsc/lint/build).
- **Acceptance:** make the synthetic→real swap a clean single-boundary operation + honest provenance + real-data-ready empty states. No real schemas/models exist yet, so the deliverable is swap-readiness + honesty, not real data.

## Deliverables

- **Single boundary:** `source.ts` — `DATA_SOURCE` flag + `DATA_PROVENANCE` (label/vintage/basis). Verified the only real-vs-synthetic branch (greppable seam).
- **Honesty UI:** `ProvenanceNote` (per-section caption) + `EmptyState`; footer now data-driven from `DATA_PROVENANCE`; provenance shown on the screener + market views.
- **Real-data readiness:** empty states on the market charts and the map (props=0); the screener table already had one; `computeMetrics` fail-closed guard (P2).
- **Contract doc:** `web/src/lib/data/README.md` — the modules' exported types are the contract; per-module real-source mapping; the swap procedure.

## Round 1 findings + disposition (format-auditor)

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | major | `DATA_PROVENANCE.basis` overclaimed — named Cook County Assessor/FHFA/Zillow/Census as if the synthetic fixtures were calibrated to them (they are hand-set literals + LCG noise) → implies real-data grounding that doesn't exist | **Fixed:** basis softened to "hand-set to be representative … illustrative only, not derived from a specific dataset" |
| 2 | major | Inconsistent with methodology.tsx §08 (which names no feeds) — two provenance claims for the same data | **Fixed:** `source.ts` aligned down to the §08 wording; the named real feeds now live only in the README's "real source *when swapped*" table |
| 3 | minor | README "provenance shown wherever data appears" overstated (only footer + market) | **Fixed:** reworded to "footer + data views (screener, market)"; also added `ProvenanceNote` to the screener |
| 4 | minor | README empty-state claim overstated for the map (loading placeholder only) | **Fixed:** added a props=0 `EmptyState` to the map, so the claim holds |

format-auditor: identity hygiene clean; Fair-Housing market-demand framing intact (no tenant-screening copy introduced); `asOf 2026-06-05` matches the bootstrap/synthetic seed; magic-number posture clean.

## Verification (final)

`bunx tsc --noEmit` 0 · `bun run lint` 0 errors · `bun run test` 13/13 · `bun run build` 0 · overclaim string removed (grep 0).

## Residual / deferred

- Per-section `ProvenanceNote` is on the footer (global) + screener + market; the deal-memo and neighborhood routes rely on the global footer (acceptable; can extend later).
- The actual synthetic→real swap is gated on the ingestion lane + the P5 artifact compiler.
- Not committed (loop scope); new files (`source.ts`, `ProvenanceNote.tsx`, `README.md`) staged atomically.
