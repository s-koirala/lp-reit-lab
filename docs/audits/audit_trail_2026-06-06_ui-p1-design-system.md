# Audit trail — UI Lane P1 design-system pass

- **Date:** 2026-06-06
- **Artifact:** `web/` front-end (TanStack Start + React 19 + Tailwind v4 + shadcn SPA) design-system pass, plus the `scripts/wcag_contrast_audit.py` tooling.
- **Loop:** [audit-remediate-loop](../../) — 2 rounds run (cap 3). Exit on zero critical+major.
- **Acceptance criteria (P1):** (1) tabular-nums app-wide; (2) WCAG 2.1 AA contrast for verdict colours used as text + verify `--muted-foreground`; (3) dark toggle with persistence + no flash-of-wrong-theme; (4) 8pt spacing grid tokens; (5) de-Lovable the vite config.

## Auditor selection

Routing per [audit-remediate-loop](../../) rules, self-selected for the artifact (a frontend CSS/TS/build change with **zero statistical content**):

- **Round 1 (parallel):** `code-reviewer`, `format-auditor`, `literature-check`, `reproducibility-verifier`.
- **Round 2 (confirmation, parallel):** `code-reviewer`, `reproducibility-verifier`.
- **`quant-auditor` deliberately omitted** — no statistical/numerical-method or backtest content to audit (deviation from the generic `/audit-loop` default of quant-auditor + literature-check + reproducibility-verifier; `code-reviewer` + `format-auditor` substituted per the routing rules for code-bearing + magic-number/identity-hygiene artifacts).

## Empirical basis for the WCAG token values

New verdict **text** tokens were not eyeballed. `scripts/wcag_contrast_audit.py` converts OKLCH → sRGB (Ottosson 2020) → WCAG 2.1 relative luminance, composites the real alpha-tinted backgrounds (badge `bg-*/10`, `hover:bg-secondary/60` rows), and searches the closest in-gamut `(L, C)` at fixed hue clearing 4.5:1. `--muted-foreground` was measured at 6.3–7.3:1 and left unchanged (the planning note to "fix" it was not borne out by measurement). The script now **parses `styles.css`** so `--assert` audits the shipped values, and is wired as a pre-commit gate.

| token | light | dark |
|---|---|---|
| `--go-strong` | `oklch(0.506 0.1225 155)` 4.60:1 | `oklch(0.608 0.13 155)` 4.63:1 |
| `--watch-strong` | `oklch(0.528 0.11 75)` 4.64:1 | `oklch(0.72 0.15 75)` 6.20:1 |
| `--nogo-strong` | `oklch(0.54 0.2 22)` 4.61:1 | `oklch(0.642 0.1925 22)` 4.60:1 |

## Round 1 findings + disposition

| # | Sev | Source | Finding | Disposition |
|---|---|---|---|---|
| R1-1 | major | code-reviewer | `PropertyMap.tsx` hardcodes light-mode SVG fills/text → invisible on dark theme (reachable via `/map` + every deal memo) | **Fixed** R2: routed polygon fill→`var(--secondary)`, labels→`var(--foreground)`/`var(--muted-foreground)`, dot fills→`var(--go/--watch/--nogo)`, dot+polygon strokes→`var(--foreground)`/`var(--border)` |
| R1-2 | major | repro-verifier, format-auditor | WCAG `--assert` validated hardcoded Python literals, not the shipped CSS (false-green risk) | **Fixed** R2: script now parses `web/src/styles.css` (single source of truth); proven live by R2 negative test |
| R1-3 | major | repro-verifier | New theme files untracked → clean HEAD checkout would not build | **Open → commit-time:** atomic staging required (see Residual risks) |
| R1-4 | minor | code-reviewer | Nitro `cloudflare-module` fallback / sandbox auto-enable dropped | **Documented** in `PROVENANCE.md` (intentional narrowing; opt-in via `NITRO_PRESET`) |
| R1-5 | minor | code-reviewer | `viteReact()` pushed after the array literal (readability) | **Fixed** R2: clarifying comment added |
| R1-6 | minor | code-reviewer | `toggleTheme()` lacks own SSR guard | **Fixed** R2: `typeof document` guard added |
| R1-7 | minor | code-reviewer | Blue chart accent `oklch(0.55 0.12 220)` hardcoded in 4 files (= `--ring`) | **Deferred** (DRY-only; legible on both themes) |
| R1-8 | minor | format-auditor | Ottosson matrix block lacked inline source tag | **Fixed** R2: inline citation added |
| R1-9 | minor | format-auditor | `0.20`/`0.2` notation drift between script and CSS | **Dissolved** by R1-2 fix (script now reads CSS) |
| R1-10 | minor | format-auditor | No CI/pre-commit wiring for the `--assert` gate | **Fixed** R2: `wcag-contrast` pre-commit hook added |
| R1-11 | minor | literature-check | `0.04045` differs from the `0.03928` in WCAG glossary text | **Fixed** R2: comment noting the IEC/W3C-erratum value |
| R1-12 | minor | literature-check | `.font-mono` `tnum` is inert on mono, contradicting the script's claim | **Fixed** R2: comment marking it a defensive no-op for proportional fallbacks |
| R1-13 | minor | literature-check | Large-text (≥18pt/24px) carve-out omitted from rationale | **Fixed** R2: docstring note added |
| R1-14 | minor | repro-verifier | JS toolchain (bun/node) unpinned | **Fixed** R2: `packageManager` + `engines` in `package.json` |
| R1-15 | minor | repro-verifier | `dist/client/index.html` absent / deploy uses server entry; env contract | **Documented** in `PROVENANCE.md` |

Identity hygiene (format-auditor): **clean** — no real email/name/OS-username in any new/changed file; only the `s-koirala` pseudonym in the upstream URL. All numeric constants (WCAG thresholds, Rec.709 luma, sRGB transfer, Ottosson matrices, contrast formula, SC 1.4.11) **CONFIRMED** against primary sources by literature-check.

## Round 2 findings + disposition

| # | Sev | Source | Finding | Disposition |
|---|---|---|---|---|
| R2-1 | minor | code-reviewer | Polygon **stroke** `oklch(0.45 0.05 80)` still non-inverting (decorative) | **Fixed:** → `var(--border)` |
| R2-2 | major | repro-verifier | `scripts/wcag_contrast_audit.py` itself untracked → pre-commit hook references a missing file on clean checkout | **Open → commit-time:** fold into atomic staging (3 files total) |
| R2-3 | minor | repro-verifier | Pre-commit hook uses bare `python` (Store-stub on Windows) | **Accepted:** matches existing seed-guard/citation-cff/data-manifest hooks (pre-commit `language: system` env, not raw shell) |

R2 confirmation: PropertyMap major **closed** for all load-bearing content; WCAG gate **proven live** (mutating `--watch-strong` → FAIL + exit 1; byte-exact revert → exit 0). No regression introduced by any remediation.

## Verification (final)

| check | command | result |
|---|---|---|
| typecheck | `bunx tsc --noEmit` | 0 |
| lint | `bun run lint` | 0 errors (6 pre-existing shadcn react-refresh warnings) |
| build | `bun run build` | 0 → `dist/client` + `dist/server/server.js` (no Nitro, matches P0 baseline) |
| WCAG gate | `py scripts/wcag_contrast_audit.py --assert` | 0 (all 8 text pairs ≥ 4.5:1) |
| Python lint | `uv run ruff check scripts/wcag_contrast_audit.py` | 0 |
| lockfile | `bun install --frozen-lockfile` | no drift; `@lovable.dev/*` subtree absent |

## Residual risks / open items

1. **Atomic staging (R1-3, R2-2) — REQUIRED at commit.** Three load-bearing files are untracked: `scripts/wcag_contrast_audit.py`, `web/src/lib/theme.ts`, `web/src/components/ThemeToggle.tsx`. They MUST be committed in the same commit as their importers (`AppShell.tsx`, `__root.tsx`) and the `.pre-commit-config.yaml` hook that calls the script, or a clean checkout fails to build / ships a dead gate. Push requires lane coordination (shared `main`, separate orchestrator clone).
2. **Deferred (out of P1 scope):** blue chart accent `oklch(0.55 0.12 220)` tokenization (DRY-only; R1-7); fuller dark-mode tuning of the multi-series chart palette (mid-luminance, currently legible).
3. **Out of scope / not a regression:** `web/src/lib/error-page.ts` hardcodes light colours, but it is the SSR-failure fallback shell with no access to the app stylesheet/theme class.
4. **Pre-existing P0 debt addressed incidentally:** first-ever lint run in this checkout surfaced repo-wide CRLF (Windows `core.autocrlf`) + unformatted P0 files; fixed via `.gitattributes` `eol=lf` for web source, EOL normalization, prettier baseline, ignoring the generated `routeTree.gen.ts`, and typing two `any`s in `market.tsx`.

## Acceptance-criteria status

- [x] tabular-nums — body `font-variant-numeric: tabular-nums` + `.tabular` utility on data tables/cards.
- [x] WCAG AA contrast — `--*-strong` text tokens (computed, gated); `--muted-foreground` measured-and-kept.
- [x] dark toggle — `theme.ts` + `ThemeToggle` + no-FOUC `<head>` script + `suppressHydrationWarning`; charts + map made theme-aware.
- [x] 8pt tokens — documented `--spacing` 8pt-grid token + convention; nav padding snapped to grid.
- [x] de-Lovable vite — `@lovable.dev/*` removed from config, `package.json`, `bunfig.toml`, `bun.lock`; standard plugin stack; build parity verified.
