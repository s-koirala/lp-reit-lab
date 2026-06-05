# Audit Trail — P0 React-base merge (foundations & consolidation)

| Field | Value |
|---|---|
| Artifact | `docs/decisions/ADR-0003.md`, `docs/decisions/ADR-0002.md` (status edit), `docs/methodology/methodology_react-merge_2026-06-05.md`, `web/**` (vendored React app), `web/PROVENANCE.md`, `web/src/routes/__root.tsx` (telemetry strip) |
| Pattern | audit-remediate-loop (parallel-specialist ensemble), 3-round cap |
| Round | 1 (exited — 1 major + 3 minor remediated; 0 critical) |
| Auditors | format-auditor, code-reviewer, reproducibility-verifier (parallel) |
| Date | 2026-06-05 |
| Branch | `feat/react-merge-p0` (uncommitted) |
| Gate state | identity-hygiene scan PASS; telemetry strip verified (0 dangling refs); vendored tree cruft-free (84 files, no node_modules/dist/.git) |
| Decision record | [ADR-0003](../decisions/ADR-0003.md); plan [methodology memo](../methodology/methodology_react-merge_2026-06-05.md) |

## Critical — none

## Major — remediated
| # | Issue | Disposition |
|---|---|---|
| R1-1 | Provenance gap: vendored `web/` recorded no upstream commit SHA; `git archive` strips history, so the source commit existed only in the local clone (unrecoverable once deleted). | **Fixed** — captured upstream `bff9b480cbf75e221d85452373a9083ef26e6872` ("Built Property Lab app", 2026-06-05); recorded in new [web/PROVENANCE.md](../../web/PROVENANCE.md), [ADR-0003](../decisions/ADR-0003.md) References, and methodology memo §7. |

## Minor — remediated
| # | Issue | Disposition |
|---|---|---|
| R1-2 | `~250 ms` debounce/motion figure asserted adjacent to the Nielsen citation, which contains only 0.1/1/10 s — magic-number-policy violation (no distinct basis). | **Fixed** — reframed in memo §3 and §4 as an *operational default (~200–250 ms) to be tuned*, not a fixed cited threshold. |
| R1-3 | `@lovable.dev/mcp-js` exclude in `web/bunfig.toml` (a dead Lovable build coupling) absent from the de-coupling inventory; flagged by both format-auditor and reproducibility-verifier. | **Fixed (documented)** — added to the P1 de-coupling checklist in memo §7 and [web/PROVENANCE.md](../../web/PROVENANCE.md); the live removal is a P1 build-config item. |
| R1-4 | Citation-format drift: memo §11 is author-year only while the sibling research memo carries DOIs. No fabricated DOIs found. | **Fixed** — added a memo §11 note deferring DOIs to `CITATION.cff` via `/cite-add` (research-memo house style), making the asymmetry intentional. |

## code-reviewer — 0 findings
Telemetry strip verified clean: `web/src/lib/lovable-error-reporting.ts` deleted; zero references to `reportLovableError`/`__lovableEvents`/`lovable-error-reporting` in `web/src`; `__root.tsx` valid TSX (all imports live, `useEffect` deps correct, `console.error` local-only matching existing convention).

## Accepted residual (carried to P1)
- The `@lovable.dev/vite-tanstack-config` build coupling (Nitro/Cloudflare target) and dead `@lovable.dev/mcp-js` exclude are **not yet removed** — deferred to P1 to avoid breaking the static build (ADR-0003 Consequences).
- `web/` is **not** `bun install`ed; no runtime build verification performed in P0 (P1 runs it).
- The front-end magic-number `computeMetrics` remains in place until **P2** replaces it with the parity-gated TS mirror.

## Residual risk
P0 is documentation + a clean source vendoring with no ReproLog obligation (nothing written to `artifacts/`/`logs/`). Identity hygiene is clean (no real email/name/username in any committed file). The single substantive risk — an unrecoverable vendoring provenance gap — is closed by recording the upstream SHA in three locations before commit. The architecture's reproducibility design (Python-generated `golden_vectors.json` consumed by pytest + Vitest; residual-derived `rtol`; forecasting confined to the venv where `emit-repro-log` fires; `run_id`-stamped artifacts) was reviewed as coherent. Nothing is committed yet; commit via `/commit-with-provenance --role=multi` is the next step.
