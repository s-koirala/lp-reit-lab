# `web/` provenance

This directory is a **vendored snapshot** of the front-end product UI, governed by
[ADR-0003](../docs/decisions/ADR-0003.md) and the
[methodology memo](../docs/methodology/methodology_react-merge_2026-06-05.md).

| Field           | Value                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Upstream        | [github.com/s-koirala/north-side-property-compass](https://github.com/s-koirala/north-side-property-compass) (Lovable-generated React app) |
| Vendored commit | `bff9b480cbf75e221d85452373a9083ef26e6872` ("Built Property Lab app", 2026-06-05)                                                          |
| Vendor method   | `git archive HEAD \| tar -x` — tracked files only (no `.git`, no `node_modules`, no build output)                                          |
| Date vendored   | 2026-06-05                                                                                                                                 |

## Modifications applied at vendoring (P0)

- Removed Lovable platform scaffolding: `.lovable/` and `src/lib/lovable-error-reporting.ts`
  (the runtime telemetry sink that exfiltrated errors + route to `window.__lovableEvents`).
- Excised the telemetry import and call from `src/routes/__root.tsx` (replaced with
  local-only `console.error`).

## Lovable build coupling — removed in P1

Resolved 2026-06-06 (design-system pass). The Lovable build dependency was
replaced with the standard plugin stack it wrapped:

- `@lovable.dev/vite-tanstack-config` removed from `package.json`. `vite.config.ts`
  now composes `@tailwindcss/vite`, `vite-tsconfig-paths`,
  `@tanstack/react-start/plugin/vite` (client import-protection + `server` entry),
  and `@vitejs/plugin-react` directly — the exact non-sandbox plugin set the
  wrapper produced. Dropped the Lovable-only, dev/sandbox-gated pieces
  (`lovable-tagger` componentTagger, dev SSR/server-fn error loggers, hmr-gate,
  dev-server bridge) and the sandbox `::`/`8080` host/port coercion. The
  Cloudflare/Nitro target is preserved as an opt-in via the `NITRO_PRESET` env
  var; the default `bun run build` emits `dist/client` + `dist/server`, identical
  to the pre-removal output.
- The dead `@lovable.dev/mcp-js` and the now-unused `@lovable.dev/vite-tanstack-config`
  entries were removed from `bunfig.toml` `minimumReleaseAgeExcludes` (now empty);
  the whole `@lovable.dev/*` subtree (incl. `lovable-tagger`, its esbuild and
  Tailwind 3 baggage) is gone from `bun.lock`.

Verified: `bunx tsc --noEmit`, `bun run lint`, and `bun run build` all pass; the
build output structure matches the P0 baseline.

### Build & deploy notes (intentional behavioural narrowing)

- **Nitro is now opt-in strictly via `NITRO_PRESET`.** The wrapper auto-enabled
  Nitro inside the Lovable sandbox and defaulted the preset to `cloudflare-module`;
  both the sandbox auto-enable and that fallback were dropped. For a Cloudflare
  Pages deploy, run `NITRO_PRESET=cloudflare-module bun run build`.
- **The default build is SSR, not a static folder.** `dist/client` holds the
  assets and `dist/server/server.js` is the entry (our `src/server.ts` error
  wrapper); there is no `dist/client/index.html`. The deploy step must use the
  server entry / Nitro path, not a bare static upload of `dist/client`.
- **Env contract:** the build reads `VITE_*` vars (baked into `import.meta.env`)
  and `NITRO_PRESET`. None are set by default (no tracked `.env`), so the default
  build is deterministic; record any values used for a deploy build.
- **Toolchain:** pinned via `package.json` `packageManager` (`bun@1.3.14`) and
  `engines` (node `>=22 <25`); `bun.lock` pins the dependency graph.

## Note on the front-end math

`src/lib/data/properties.ts::computeMetrics` is magic-number mock math and is
**superseded** by a parity-gated TypeScript mirror of the Python engine
(ADR-0003 §Decision). It is retained only until **P2** replaces it.
