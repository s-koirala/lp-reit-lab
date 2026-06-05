# `web/` provenance

This directory is a **vendored snapshot** of the front-end product UI, governed by
[ADR-0003](../docs/decisions/ADR-0003.md) and the
[methodology memo](../docs/methodology/methodology_react-merge_2026-06-05.md).

| Field | Value |
|---|---|
| Upstream | [github.com/s-koirala/north-side-property-compass](https://github.com/s-koirala/north-side-property-compass) (Lovable-generated React app) |
| Vendored commit | `bff9b480cbf75e221d85452373a9083ef26e6872` ("Built Property Lab app", 2026-06-05) |
| Vendor method | `git archive HEAD \| tar -x` — tracked files only (no `.git`, no `node_modules`, no build output) |
| Date vendored | 2026-06-05 |

## Modifications applied at vendoring (P0)

- Removed Lovable platform scaffolding: `.lovable/` and `src/lib/lovable-error-reporting.ts`
  (the runtime telemetry sink that exfiltrated errors + route to `window.__lovableEvents`).
- Excised the telemetry import and call from `src/routes/__root.tsx` (replaced with
  local-only `console.error`).

## Outstanding Lovable build coupling (P1 follow-on)

Not removed in P0 (decoupling risks the Nitro/Cloudflare static build; deferred to P1):

- `@lovable.dev/vite-tanstack-config` — imported in `vite.config.ts`; wires the
  Nitro/Cloudflare target and bundles dev-only `lovable-tagger`.
- A dead `@lovable.dev/mcp-js` entry in `bunfig.toml` `minimumReleaseAgeExcludes`
  (the package is not a dependency; the exclude bypasses the 24 h supply-chain guard
  for nothing — drop it in P1).

## Note on the front-end math

`src/lib/data/properties.ts::computeMetrics` is magic-number mock math and is
**superseded** by a parity-gated TypeScript mirror of the Python engine
(ADR-0003 §Decision). It is retained only until **P2** replaces it.
