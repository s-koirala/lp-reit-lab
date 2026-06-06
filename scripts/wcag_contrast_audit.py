#!/usr/bin/env python3
"""WCAG 2.1 contrast audit + repair search for the web/ design-system OKLCH tokens.

Purpose
-------
The web front-end (``web/src/styles.css``) defines its colour palette in OKLCH.
Per the user-global "zero arbitrary thresholds / magic numbers" directive, any
colour chosen for *text* must be justified against a measured contrast ratio,
not eyeballed. This module:

  1. converts an OKLCH triple to sRGB via the exact Ottosson transform,
  2. computes the WCAG 2.1 relative luminance and contrast ratio,
  3. composites alpha-tinted backgrounds (e.g. Tailwind ``bg-watch/10`` and the
     ``hover:bg-secondary/60`` table rows) the way a browser does
     (source-over, non-premultiplied, in gamma-encoded sRGB),
  4. audits every (text-token, background) pair that actually occurs in the app
     against WCAG 2.1 SC 1.4.3, and
  5. for any failing token, finds the *closest* OKLCH (L, C) repair at fixed hue
     that clears the threshold and stays in sRGB gamut.

Why search (L, C) at fixed hue: hue carries the verdict's semantic identity
(amber=watch, green=go, red=no-go) and must not drift. Within a hue, the AA
repair closest to the original colour in the perceptual L–C plane is the
least-disruptive fix (Ottosson 2020, https://bottosson.github.io/posts/oklab/).
A 1-D lightness-only search is insufficient: at the brand chroma, no in-gamut
lightness reaches 4.5:1 for amber/green on the light paper, so chroma must also
relax.

Design consequence
------------------
Verdict colours are used both as decoration (status dot, 10% tint, border) and
as text. A graphic needs only 3:1 (SC 1.4.11) but text needs 4.5:1 (SC 1.4.3).
Rather than desaturate the dot to satisfy the text rule, the repair introduces
separate AA-safe *text* tokens (``--go-strong`` / ``--watch-strong`` /
``--nogo-strong``) used only for ``text-*``; the decorative ``--go/--watch/--nogo``
keep their vivid brand value for fills and borders.

References
----------
* OKLab/OKLCH transform & matrices: Björn Ottosson (2020),
  https://bottosson.github.io/posts/oklab/
* WCAG 2.1 relative luminance & contrast ratio:
  https://www.w3.org/TR/WCAG21/#dfn-relative-luminance ,
  https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio
* sRGB transfer function: IEC 61966-2-1.

Usage
-----
    py scripts/wcag_contrast_audit.py            # audit + suggest repairs
    py scripts/wcag_contrast_audit.py --assert   # exit 1 if any text pair fails

Stdlib only; runs without the project venv.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# --- WCAG 2.1 thresholds (SC 1.4.3 / 1.4.11) ---------------------------------
# All verdict text in the app renders below the SC 1.4.3 "large text" boundary
# (>= 18pt/24px, or >= 14pt/18.66px bold), so it is audited as NORMAL (4.5:1).
# WCAG_AA_LARGE (3:1) is the bar for large text and for non-text/graphic objects
# (SC 1.4.11) such as the decorative verdict dots/tints.
WCAG_AA_NORMAL = 4.5
WCAG_AA_LARGE = 3.0
WCAG_LUMINANCE_OFFSET = 0.05

# --- sRGB transfer function (IEC 61966-2-1) ----------------------------------
# 0.04045 is the IEC / W3C-erratum-corrected decode threshold; the WCAG 2.1
# glossary text prints 0.03928, but its published erratum confirms 0.04045.
SRGB_DECODE_THRESH = 0.04045
SRGB_ENCODE_THRESH = 0.0031308
SRGB_GAMMA = 2.4
SRGB_A = 0.055
SRGB_LINEAR_SLOPE = 12.92

# --- WCAG relative-luminance coefficients (Rec. 709) -------------------------
LUMA_R, LUMA_G, LUMA_B = 0.2126, 0.7152, 0.0722

# --- repair-search grid (numerical-solver resolution, not a domain threshold) -
SEARCH_MARGIN = 0.10  # target ratio = threshold + margin, guards rounding
GRID_L_STEP = 0.002
GRID_C_STEP = 0.0025
GRID_L_LO, GRID_L_HI = 0.10, 0.95


def _srgb_encode(c: float) -> float:
    c = max(0.0, min(1.0, c))
    if c <= SRGB_ENCODE_THRESH:
        return c * SRGB_LINEAR_SLOPE
    return (1 + SRGB_A) * (c ** (1 / SRGB_GAMMA)) - SRGB_A


def _wcag_linearize(c: float) -> float:
    if c <= SRGB_DECODE_THRESH:
        return c / SRGB_LINEAR_SLOPE
    return ((c + SRGB_A) / (1 + SRGB_A)) ** SRGB_GAMMA


def _oklch_linear_rgb(L: float, C: float, H_deg: float):
    # Ottosson 2020 M1 (OKLab -> LMS') and M2 (LMS -> linear sRGB); coefficients
    # verbatim from https://bottosson.github.io/posts/oklab/ reference code.
    h = math.radians(H_deg)
    a, b = C * math.cos(h), C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return r, g, bb


def oklch_to_srgb(L: float, C: float, H_deg: float):
    return tuple(_srgb_encode(c) for c in _oklch_linear_rgb(L, C, H_deg))


def in_gamut(L: float, C: float, H_deg: float) -> bool:
    eps = 1e-4
    return all(-eps <= v <= 1 + eps for v in _oklch_linear_rgb(L, C, H_deg))


def luminance(srgb) -> float:
    r, g, b = (_wcag_linearize(c) for c in srgb)
    return LUMA_R * r + LUMA_G * g + LUMA_B * b


def contrast_ratio(fg, bg) -> float:
    l1, l2 = luminance(fg), luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + WCAG_LUMINANCE_OFFSET) / (lo + WCAG_LUMINANCE_OFFSET)


def composite(fg_srgb, bg_srgb, alpha: float):
    """Source-over alpha composite in gamma-encoded sRGB (CSS default)."""
    return tuple(alpha * f + (1 - alpha) * b for f, b in zip(fg_srgb, bg_srgb, strict=True))


@dataclass(frozen=True)
class Oklch:
    L: float
    C: float
    H: float

    def srgb(self):
        return oklch_to_srgb(self.L, self.C, self.H)


# --- Token palette parsed from web/src/styles.css (single source of truth) ---
# Rather than duplicate the OKLCH values here (which could silently drift from
# the shipped CSS), parse them straight out of styles.css so `--assert` audits
# exactly what the app renders. The dark palette is the light (:root) palette
# overlaid with the .dark overrides, mirroring the CSS cascade — the decorative
# verdict colours are not overridden in .dark, so they inherit :root.
STYLES_CSS = Path(__file__).resolve().parent.parent / "web" / "src" / "styles.css"

# Tokens consumed by the scenarios below; all are authored as literal oklch() in
# styles.css (not var() aliases), so a direct parse is unambiguous.
_TOKENS = (
    "paper",
    "card",
    "secondary",
    "ink",
    "muted-foreground",
    "go",
    "watch",
    "nogo",
    "go-strong",
    "watch-strong",
    "nogo-strong",
)
_OKLCH_DECL = re.compile(r"--([\w-]+):\s*oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\)")


def _parse_block(css: str, selector: str) -> dict:
    """Extract {token: Oklch} for every literal oklch() decl in a flat CSS block."""
    m = re.search(re.escape(selector) + r"\s*\{", css)
    if not m:
        raise ValueError(f"{selector} block not found in {STYLES_CSS}")
    end = css.index("}", m.end())  # :root / .dark blocks here are flat (no nesting)
    return {
        name: Oklch(float(ll), float(cc), float(hh))
        for name, ll, cc, hh in _OKLCH_DECL.findall(css[m.end() : end])
    }


def _load_palettes(css_path: Path = STYLES_CSS):
    css = css_path.read_text(encoding="utf-8")
    root = _parse_block(css, ":root")
    dark = {**root, **_parse_block(css, ".dark")}  # .dark cascades over :root
    missing = [t for t in _TOKENS if t not in root]
    if missing:
        raise ValueError(f"tokens missing from :root of {css_path}: {missing}")
    return root, dark


LIGHT, DARK = _load_palettes()


def _palette(mode: str):
    return LIGHT if mode == "light" else DARK


def _bg(mode: str, spec):
    """Resolve a background spec to sRGB.

    spec forms:
      "card"                         -> opaque token
      ("tint", token, alpha, base)   -> token@alpha over base token
    """
    pal = _palette(mode)
    if isinstance(spec, str):
        return pal[spec].srgb()
    _, token, alpha, base = spec
    return composite(pal[token].srgb(), pal[base].srgb(), alpha)


def _bg_label(spec):
    if isinstance(spec, str):
        return spec
    _, token, alpha, base = spec
    return f"{token}/{int(alpha * 100)}@{base}"


# Each scenario: (mode, text_token, [background specs], threshold, note).
# Worst (min) contrast across the listed backgrounds is the binding constraint.
SECONDARY_HOVER = ("tint", "secondary", 0.60, "card")  # hover:bg-secondary/60 rows
SCENARIOS = []
for _mode in ("light", "dark"):
    for _v in ("go", "watch", "nogo"):
        SCENARIOS.append(
            (
                _mode,
                f"{_v}-strong",
                [("tint", _v, 0.10, "card"), "card", "paper", SECONDARY_HOVER],
                WCAG_AA_NORMAL,
                f"{_v.upper()} verdict text (badge tint / card / paper / hover row)",
            )
        )
    SCENARIOS.append(
        (
            _mode,
            "muted-foreground",
            ["card", "paper", SECONDARY_HOVER],
            WCAG_AA_NORMAL,
            "secondary/muted text",
        )
    )


def worst_contrast(mode, text_token, bg_specs):
    fg = _palette(mode)[text_token].srgb()
    return min(contrast_ratio(fg, _bg(mode, s)) for s in bg_specs)


def worst_contrast_for(cand: Oklch, mode, bg_specs):
    return min(contrast_ratio(cand.srgb(), _bg(mode, s)) for s in bg_specs)


def suggest_repair(mode, text_token, bg_specs, threshold):
    """Closest in-gamut OKLCH (L, C) at fixed hue clearing threshold+margin."""
    base = _palette(mode)[text_token]
    target = threshold + SEARCH_MARGIN
    best, best_dist = None, None
    n_l = int((GRID_L_HI - GRID_L_LO) / GRID_L_STEP) + 1
    n_c = int(base.C / GRID_C_STEP) + 1
    for i in range(n_l):
        L = round(GRID_L_LO + i * GRID_L_STEP, 4)
        for j in range(n_c):
            C = round(j * GRID_C_STEP, 4)
            if not in_gamut(L, C, base.H):
                continue
            cand = Oklch(L, C, base.H)
            if worst_contrast_for(cand, mode, bg_specs) < target:
                continue
            dist = math.hypot(L - base.L, C - base.C)
            if best_dist is None or dist < best_dist:
                best, best_dist = cand, dist
    return best


def run(do_assert: bool) -> int:
    print("WCAG 2.1 contrast audit - web/src/styles.css OKLCH text tokens")
    print(f"thresholds: normal {WCAG_AA_NORMAL}:1, large/graphic {WCAG_AA_LARGE}:1")
    print(f"repair target: >= {WCAG_AA_NORMAL + SEARCH_MARGIN}:1 (margin {SEARCH_MARGIN})\n")
    header = f"{'mode':5} {'text token':16} {'min ratio':>9}  {'req':>4}  {'status':6}  binding bg"
    print(header)
    print("-" * len(header))
    failures = []
    for mode, tok, bgs, thr, note in SCENARIOS:
        fg = _palette(mode)[tok].srgb()
        ratios = [(contrast_ratio(fg, _bg(mode, s)), s) for s in bgs]
        wc, binding = min(ratios, key=lambda t: t[0])
        ok = wc >= thr
        status = "PASS" if ok else "FAIL"
        print(
            f"{mode:5} {tok:16} {wc:9.2f}  {thr:4.1f}  {status:6}  {_bg_label(binding)}  | {note}"
        )
        if not ok:
            failures.append((mode, tok, bgs, thr))

    if failures:
        print("\nClosest in-gamut AA repairs (hue fixed):")
        for mode, tok, bgs, thr in failures:
            base = _palette(mode)[tok]
            fix = suggest_repair(mode, tok, bgs, thr)
            if fix is None:
                print(f"  [{mode}] {tok}: no in-gamut (L,C) reaches target at hue {base.H}")
                continue
            new_wc = worst_contrast_for(fix, mode, bgs)
            print(
                f"  [{mode}] {tok}: oklch({base.L} {base.C} {base.H}) "
                f"-> oklch({fix.L} {fix.C} {fix.H})  [min {new_wc:.2f}:1]"
            )
    else:
        print("\nAll audited text pairs meet WCAG AA.")

    return 1 if (do_assert and failures) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--assert",
        dest="do_assert",
        action="store_true",
        help="exit non-zero if any text pair fails AA",
    )
    sys.exit(run(ap.parse_args().do_assert))
