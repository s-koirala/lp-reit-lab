# Audit trail — P3: TanStack Table search + react-leaflet map

- **Date:** 2026-06-06
- **Artifact:** `web/src/components/{PropertyMap,PropertyMapInner,ScreenerTable}.tsx`, `web/src/hooks/use-theme.ts`, `web/src/lib/data/{neighborhoods,properties}.ts`, `web/src/routes/{index,map}.tsx`.
- **Loop:** audit-remediate — 2 rounds (cap 3). Auditors: code-reviewer + format-auditor (frontend phase).
- **Acceptance:** scalable search/sort via TanStack Table; real OSM/Leaflet map replacing the SVG placeholder — built contract-first on synthetic data (real listing coordinates not yet available).

## Approach (no real data required)

- **Real geography, synthetic placement:** the 6 North Side submarkets now carry real (approximate) WGS84 centroids; properties get a synthetic lat/lng jittered ~±0.006° within their submarket (deterministic, clearly labeled demo data). The engine/parity gate is untouched (DCF uses price/rent/hoa only) — parity stays 13/13.
- **Map:** `react-leaflet` v5 + CARTO Positron/Dark tiles (free OSM, no Mapbox per ADR-0002). Leaflet is `lazy()`-loaded behind a mount gate so its `window` access never runs in SSR.
- **Search:** `@tanstack/react-table` global free-text filter (address/submarket) + sortable columns; replaced the manual table + sort-`<select>`.

## Round 1 findings + disposition

| # | Sev | Source | Finding | Disposition |
|---|---|---|---|---|
| 1 | major | code-reviewer | Map tiles + marker colors read once at mount; the dark toggle mutates a class without re-rendering the map → desync after toggle | **Fixed:** `useTheme()` (MutationObserver on `<html>` class) re-renders the map; `TileLayer` keyed on theme; colors re-read from live CSS vars |
| 2 | major | code-reviewer | `map.tsx` copy claimed "submarket polygons carry median price and net yield" — now name-only centroid markers | **Fixed:** neighborhood markers' Tooltip now shows median price + yield; copy → "submarket markers" |
| 3 | minor | code-reviewer | Shortlist subtitle "Top 3 by current sort key" stale (sort-select removed) | **Fixed:** → "Top 3 by blended yield + appreciation score" |
| 4 | minor | code-reviewer | Sortable `<th>` keyboard-inaccessible (WCAG 2.1.1) | **Fixed:** sort control is now a `<button>` inside `<th scope="col">` |
| 5 | minor | code-reviewer | `NUMERIC` Set duplicates column-numericness (drift) | **Deferred:** documented single alignment source; `meta.numeric` refactor noted (low-risk) |
| 6 | minor | code-reviewer | `globalFilterFn` bypasses the column model (desync) | **Deferred:** behavior correct + documented |
| 7 | minor | code-reviewer | Property-marker stroke `--background` low contrast / staleness | **Resolved by #1** (colors now track theme); visual tuning noted |
| 8 | minor | format-auditor | `tenantFitScore` comment "demand for 3BR+ family units" edges toward familial-status language (FHA) | **Fixed:** reworded to "market-demand proxy for 3BR+ units (size/school/transit driven)" |
| 9 | minor | format-auditor | filename convention | No change (consistent with vendored SPA convention) |

format-auditor: identity hygiene clean; CARTO+OSM attribution present/correct; no new tenant-screening language; ADR-0002 (no Mapbox) satisfied.

## Verification (final)

`bunx tsc --noEmit` 0 · `bun run lint` 0 errors · `bun run test` 13/13 (engine parity unaffected) · `bun run build` 0 → dist/client+server (Leaflet isolated in a client-only lazy chunk; SSR build clean).

## Residual / deferred

- **Runtime/visual rendering UNVERIFIED in this loop** (no browser): that Leaflet tiles + oklch-filled markers render, and that the theme live-switch repaints the map, are reasoned from the code (standard patterns, build green) but not screenshot-confirmed. Verify with `bun run dev`. CARTO tiles also require network at view time.
- Deferred minors: `meta.numeric` column refactor; `globalFilterFn` centralization.
- Real listing coordinates replace the synthetic lat/lng when MLS/real data lands (P3's only data dependency).
- Not committed (loop scope); new files (`PropertyMapInner.tsx`, `ScreenerTable.tsx`, `use-theme.ts`) + the leaflet/table deps must be staged atomically.
