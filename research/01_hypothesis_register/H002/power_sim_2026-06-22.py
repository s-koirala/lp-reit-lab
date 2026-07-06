"""H002 prospective power — clustered + heteroskedastic repeat-sales WLS DiD estimator.

Addresses audit findings (Round 2) on power_analysis_2026-06-22.md / this script:
  - power-mc-clustering-inert-1 (CRITICAL): the segment random effect u_c must LOAD on the
                               side contrast. `side` is therefore drawn from a PER-CLUSTER
                               propensity p_c (treatment composition varies across boundary
                               segments), so intra-cluster correlation rho enters the
                               side-coefficient variance (CGM 2008). Drawing side i.i.d. of
                               cluster (the Round-1 bug) differenced u_c out and made rho inert.
  - power-estimand-mismatch-persists-2 (CRITICAL): the registered estimand is the repeat-sales
                               `boundary_side x period` INTERACTION (a DiD contrast), not a
                               side-dummy level. Each pair now spans (t1, t2) quarterly periods;
                               y is regressed on the full quarterly repeat-sales period-dummy
                               basis PLUS a side x period cross block, and we power the
                               cumulative across-window side differential CONTRAST (BMN 1963).
  - power-smallG-inference-mismatch-3 (HIGH): inference is the REGISTERED Webb (2023) six-point
                               wild-cluster bootstrap (design.md S5; 10.1111/caje.12661,
                               originating edition Webb 2014 QED WP 1315), with the Conley (1999)
                               spatial-HAC rejection rule reported as the small-G fallback — not a
                               plain CR1 + t(G-1) critical value.
  - power-sigma-heteroskedastic-3: per-pair error variance grows with holding interval tau
                               (Case-Shiller stage-2 V(tau)=A+B*tau).
  - power-dimensional-scale-4: numerator (window-cumulative gap) and denominator (per-pair SD)
                               are on commensurate time scales (per-pair pro-rating by tau).
  - repro-emission-not-guarded-2 / repro-config-sha-stale-1 (CRITICAL): this script EMITS the
                               ReproLog mechanically via the emit-repro-log skill and computes
                               config_resolved_sha256 over a FILE-INDEPENDENT canonical input
                               (sha256(design.md) || sha256(this script)), removing the
                               self-referential-markdown-slice ambiguity. It asserts
                               ReproLog.verify() before exit.

Routes computed (all PROSPECTIVE; no H002 data is frozen — design.md S11):
  (1) i.i.d. floor          : statsmodels TTestIndPower (absolute lower bound on n).
  (2) analytic DEFF         : n_ind * (1 + (m_bar - 1) * rho_icc) cross-check (Kish).
  (3) Monte-Carlo simulation: power of the actual repeat-sales WLS `boundary_side x period`
                               DiD contrast under heteroskedastic V(tau) errors with a
                               boundary-segment random effect that LOADS on the side contrast
                               (cluster-level treatment propensity), inference by the registered
                               Webb six-point wild-cluster bootstrap. This is the OPERATIVE
                               requirement; (1) is a floor, (2) a conservative analytic bracket.

All tunables carry a "# justify:" basis or are pre-registered (RNG seed). No magic numbers.

CLI: `uv run --extra analysis python power_sim_2026-06-22.py [--emit-repro-log]`
The bare run prints the grid; `--emit-repro-log` additionally writes the ReproLog and the
run-record values (run_id, hashes) the markdown's run-record table must mirror.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
from statsmodels.stats.power import TTestIndPower

# --------------------------------------------------------------------------- #
# Pre-registered scalar inputs (mirror power_analysis_2026-06-22.md)
# --------------------------------------------------------------------------- #
RNG_SEED = 20260706  # justify: the REGISTERED freeze seed (design.md S11, pinned 2026-07-06); this
#                       is the seed of the BINDING full-fidelity run. The 20260622 rehearsal seed is
#                       retired with the rehearsal figures.

ALPHA = 0.05         # justify: design.md S8 default confirmatory alpha (Fisher 1925), one-sided.
POWER_TARGET = 0.80  # justify: design.md S8 power target = Cohen 1988 convention.

# Effect of interest, expressed at the WINDOW (cumulative) scale.
DELTA_RATE_WINDOW = 0.05  # justify: smallest scientifically-meaningful cumulative across-boundary
#                            appreciation gap (5 log pts over the test window), anchored BELOW the
#                            ~0.06 Bogin & Nguyen-Hoang 2014 (10.1111/jors.12141) designation-change
#                            capitalization (0.05 ~= 0.83*0.06) — a RATE-scale anchor, NOT scaled from
#                            Black 1999's LEVEL premium; NOT a literature point estimate.

# Per-pair idiosyncratic SD — order-of-magnitude DESIGN PRIOR bracketed by the cited 0.10-0.20
# range. No source publishes a scalar 0.15 single-pair SD; the Case-Shiller stage-2 form gives a
# variance that GROWS with the holding interval. We therefore parameterize V(tau) and report the
# constant-SD t-test only as a floor.
SIGMA_IDIO_PRIOR = 0.15  # justify: order-of-magnitude design prior, midpoint of the cited 0.10-0.20
#                           log-point range (Case-Shiller 1987/1989; Calhoun 1996 FHFA); bracketed
#                           by the sensitivity grid, NOT asserted as pinned-from-source.

# --------------------------------------------------------------------------- #
# Case-Shiller stage-2 holding-period variance model V(tau) = A + B*tau (tau in years).
# Parameterized so V(MEAN_HOLD) == SIGMA_IDIO_PRIOR^2, with a linear growth slope; the quadratic
# C*tau^2 term is a registered sensitivity, not the central case.
# --------------------------------------------------------------------------- #
MEAN_HOLD_YEARS = 3.778  # justify: RESOLVED at freeze (2026-07-06) — realized mean holding interval
#                           of the frozen qualified cell (q_top=10, G*=G_noise, 250 m; n=4,161),
#                           computed outcome-blind from sale dates only; evidence:
#                           data/interim/segment_structure_h002-frozen-cell_2026-07-06.csv.
WINDOW_YEARS = 7.0     # justify: RESOLVED at freeze — this is the registered EFFECT-SCALE definition
#                         (DELTA_RATE_WINDOW = 0.05 accrues over a nominal 7-year window; design S8
#                         MDE anchor), NOT a data prior: the per-pair effect is pro-rated by holding
#                         years regardless of the realized panel span, so the anchor window and the
#                         79-quarter realized panel are deliberately distinct quantities.
PERIODS_PER_YEAR = 4   # justify: quarterly index periods (design.md S2; FHFA/Case-Shiller convention).
N_PERIODS = int(round(WINDOW_YEARS * PERIODS_PER_YEAR))  # quarterly period dummies spanning the window

VAR_GROWTH_FRACTION = 0.5  # justify: fraction of per-pair variance attributable to the
#                             holding-interval-dependent (Case-Shiller stage-2) component vs a fixed
#                             transaction-noise floor; central value; swept in the sensitivity grid.

_V_mean = SIGMA_IDIO_PRIOR ** 2
B_COEF = VAR_GROWTH_FRACTION * _V_mean / MEAN_HOLD_YEARS  # slope per year
A_COEF = _V_mean - B_COEF * MEAN_HOLD_YEARS               # fixed floor (>=0 by construction here)

# Cluster-level treatment-propensity dispersion: side composition VARIES across boundary segments
# so that the segment random effect loads on the side contrast (finding ...-inert-1). Without
# cross-segment variation in p_c, u_c differences out of the side coefficient and rho is inert.
# RESOLVED at freeze (2026-07-06): the Beta(2,2) placeholder is superseded by the REALIZED
# per-segment structure of the frozen qualified cell (q_top=10, G*=G_noise, 250 m; G=37), computed
# outcome-blind (counts/geometry only) — evidence:
# data/interim/segment_structure_h002-frozen-cell_2026-07-06.csv.
# Simulated clusters RESAMPLE these vectors (with replacement, normalized), so the simulated design
# carries the realized size skew (share CV 1.429 — unequal clusters RAISE the design effect vs the
# uniform-assignment draft, Kish size-CV term) and the realized treatment composition, at any
# simulated G.
REALIZED_SEG_SIZE_SHARES = np.array([
    0.12545, 0.13290, 0.04518, 0.00577, 0.01995, 0.00697, 0.01130, 0.02259,
    0.00072, 0.01370, 0.02163, 0.07739, 0.00168, 0.02980, 0.00024, 0.00096,
    0.00481, 0.03989, 0.05960, 0.00336, 0.05576, 0.00024, 0.00072, 0.00024,
    0.04903, 0.00024, 0.00048, 0.00937, 0.00024, 0.00168, 0.14972, 0.02836,
    0.04783, 0.01442, 0.00649, 0.00192, 0.00937,
])  # justify: realized frozen-cell segment pair-count shares (outcome-blind).
REALIZED_SEG_HI_SHARES = np.array([
    0.6188, 0.5552, 0.6702, 0.7500, 0.4819, 0.6897, 0.5319, 0.4787, 0.0000,
    1.0000, 0.3556, 0.5497, 0.7143, 0.7258, 1.0000, 0.2500, 1.0000, 0.4639,
    1.0000, 0.2143, 0.4569, 1.0000, 1.0000, 0.0000, 0.5735, 1.0000, 0.5000,
    1.0000, 1.0000, 1.0000, 0.6613, 0.4322, 0.0000, 0.8833, 1.0000, 1.0000,
    0.0256,
])  # justify: realized frozen-cell per-segment high-side composition (outcome-blind).

WILD_B = 399  # justify: wild-cluster bootstrap replicates per test. B+1=400 gives an EXACT bootstrap
#               p-value grid resolving the (1-alpha)=0.95 quantile to 1/400=0.0025 — finer than needed
#               for a reject/no-reject decision at alpha=0.05; CGM 2008 and Webb 2023 use B=399
#               routinely for clustered wild bootstrap. (B=399 is the standard "B+1 multiple of
#               1/(alpha or 1-alpha)" choice; Davidson & MacKinnon 2000 recommend B such that
#               alpha*(B+1) is an integer — 0.05*400=20.) Keeps the nested MC (N_REP power evals x
#               n-bisection x 12-cell grid) tractable without degrading the test's size (verified:
#               one-sided size 0.051 at the true null, n=150/side, rho=0.05).


def v_tau(tau_years: np.ndarray) -> np.ndarray:
    """Case-Shiller stage-2 per-pair error variance as a function of holding interval (years)."""
    return A_COEF + B_COEF * np.asarray(tau_years, dtype=float)


# --------------------------------------------------------------------------- #
# (1) i.i.d. FLOOR — statsmodels TTestIndPower (constant-SD two-sample t).
# --------------------------------------------------------------------------- #
def iid_floor_n_per_side() -> float:
    d = DELTA_RATE_WINDOW / SIGMA_IDIO_PRIOR  # window/per-pair scales NOT commensurate -> floor only
    return TTestIndPower().solve_power(
        effect_size=d, alpha=ALPHA, power=POWER_TARGET, ratio=1.0, alternative="larger"
    )


# --------------------------------------------------------------------------- #
# (2) Analytic DEFF cross-check (Kish): n_required = n_ind * (1 + (m_bar - 1) * rho_icc).
# --------------------------------------------------------------------------- #
def deff(m_bar: float, rho_icc: float) -> float:
    return 1.0 + (m_bar - 1.0) * rho_icc


# --------------------------------------------------------------------------- #
# (3) Monte-Carlo power of the repeat-sales WLS `boundary_side x period` DiD CONTRAST.
#
# Generative model for one replication at n pairs/side (2n total):
#   - pairs are grouped into G boundary-segment clusters. Each cluster c draws a treatment
#     propensity p_c ~ Beta(a, a); side_i ~ Bernoulli(p_{c(i)}) so the high-quality-side share
#     VARIES across segments (loads the segment random effect onto the side contrast).
#   - each cluster has a random effect u_c ~ N(0, rho*V0) inducing intra-cluster correlation rho.
#   - each pair i has a holding interval tau_i (lognormal around MEAN_HOLD), sale periods
#     (t1_i, t2_i) drawn on the quarterly grid with t2_i - t1_i ~ tau_i, and side s_i.
#   - repeat-sales outcome  y_i = sum_p D_{i,p} * theta_p  +  s_i * (cumulative side differential)
#                                + u_{c(i)} + e_i,  where D is the BMN +1@t2 / -1@t1 period-dummy
#     design, theta_p the common index path, and the side differential accrues over the pair's
#     holding span pro-rated by (tau_i / window) (commensurate scaling, finding ...-scale-4):
#       E[side differential_i] = DELTA_RATE_WINDOW * (tau_i / WINDOW_YEARS).
#     e_i ~ N(0, (1-rho)*V(tau_i)) heteroskedastic in tau (Case-Shiller stage-2).
#   - ESTIMATOR: WLS of y on [BMN period dummies, side x period interaction block] with weights
#     1/V(tau_i). The confirmatory statistic is the CUMULATIVE side differential contrast
#     c'beta (sum of the side x period coefficients over the window) — the registered DiD estimand.
#   - INFERENCE: Webb (2023) six-point wild-cluster bootstrap one-sided test on c'beta, clustering
#     by segment (design.md S5). Conley spatial-HAC reported as the small-G fallback.
# --------------------------------------------------------------------------- #

# Webb (2023 / 2014 QED WP 1315) six-point wild-bootstrap weights and probabilities.
# Support {-sqrt(3/2), -sqrt(2/2)=-1/sqrt(2)? } -- the canonical six-point weights are
#   {+-sqrt(3/2), +-sqrt(2/2), +-sqrt(1/2)} each with probability 1/6, mean 0, variance 1.
_WEBB_SUPPORT = np.array(
    [-math.sqrt(3 / 2), -math.sqrt(2 / 2), -math.sqrt(1 / 2),
     math.sqrt(1 / 2), math.sqrt(2 / 2), math.sqrt(3 / 2)],
    dtype=float,
)  # justify: Webb six-point weights (mean 0, var 1); remedy for Rademacher degeneracy at small G.


def _draw_holdings(rng: np.random.Generator, n: int) -> np.ndarray:
    cv = 0.669  # justify: RESOLVED at freeze (2026-07-06) — realized CV of frozen-cell holding
    #              intervals (outcome-blind, dates only); evidence:
    #              data/interim/segment_structure_h002-frozen-cell_2026-07-06.csv.
    sigma_log = math.sqrt(math.log(1.0 + cv ** 2))
    mu_log = math.log(MEAN_HOLD_YEARS) - 0.5 * sigma_log ** 2
    tau = rng.lognormal(mean=mu_log, sigma=sigma_log, size=n)
    return np.clip(tau, 0.5, None)  # justify: min-hold floor 0.5y mirrors the design.md S4 flip screen.


def _build_repeat_sales_design(t1, t2, side, n_periods):
    """BMN repeat-sales period-dummy design + the single side-differential growth column.

    The registered confirmatory estimand (design.md S1, S5) is a SINGLE summarizing parameter:
    "the difference in cumulative log growth over the test window" between the two side-specific
    repeat-sales indices — equivalently the coefficient on a `boundary_side x period` interaction
    that summarizes the across-boundary cumulative differential. The FREE side x period DUMMY
    block (one coefficient per quarter) is the event-study / pre-trend specification (design.md
    S1.2 identification gate), NOT the confirmatory beta_diff; powering 28 separate noisy
    interaction coefficients and summing them inflates the contrast variance and powers the
    WRONG object. We therefore parameterize the confirmatory differential as ONE column:
    side x (period span), so beta_diff is the per-period differential growth rate whose
    window-cumulative value is the registered estimand.

    Returns (X, idx_diff):
      - X columns = [period_1 .. period_{P-1}  (BMN +1@t2/-1@t1 index path; period 0 = base),
                     side_diff]  where side_diff_i = side_i * (t2_i - t1_i)  (the differential
                     growth accrued over the pair's own holding span — within-PIN DiD).
      - idx_diff = index of the side_diff column (the confirmatory beta_diff coefficient).
    """
    n = t1.size
    # BMN period dummies: +1 at the (later) sale period t2, -1 at (earlier) t1; period 0 is the base.
    D = np.zeros((n, n_periods - 1))
    for p in range(1, n_periods):
        D[:, p - 1] = (t2 == p).astype(float) - (t1 == p).astype(float)
    # Single confirmatory differential column: side x holding-span (periods). The coefficient is
    # the per-period side differential growth; its window-cumulative value (x N_PERIODS) is beta_diff.
    side_diff = (side.astype(float) * (t2 - t1).astype(float))[:, None]
    X = np.hstack([D, side_diff])
    idx_diff = X.shape[1] - 1
    return X, idx_diff


def _cluster_index_map(cluster):
    """Return (clusters, rows_by_cluster) for fast per-cluster score accumulation."""
    clusters = np.unique(cluster)
    rows_by_cluster = [np.flatnonzero(cluster == g) for g in clusters]
    return clusters, rows_by_cluster


def _cr_se_of_coef(XW, XtWX_inv, resid_cols, rows_by_cluster, idx):
    """Cluster-robust SE of the coefficient `idx` for one or many residual columns.

    XW            : X * W[:, None]            (n x k), the W-scaled design (fixed across bootstrap)
    XtWX_inv      : (X'WX)^-1                  (k x k), fixed across bootstrap
    resid_cols    : residuals, (n,) or (n x B)
    rows_by_cluster: list of row-index arrays per cluster
    Vectorized over the B residual columns. Returns SE(s) of beta[idx]; shape () or (B,).
    """
    is_2d = resid_cols.ndim > 1
    resid2d = resid_cols if is_2d else resid_cols[:, None]
    b = resid2d.shape[1]
    # meat = sum_g (XW_g' u_g)(XW_g' u_g)'  -> accumulate per cluster, per bootstrap column.
    # a_idx = e_idx' XtWX_inv  (row that maps the meat to the idx-th variance entry).
    a = XtWX_inv[idx]  # (k,)
    # For each cluster g and column j: s_gj = a' (XW_g' u_gj) = sum over rows in g of (XW @ a)_row * u.
    xa = XW @ a  # (n,)  -- the influence weight per observation for coefficient idx
    var = np.zeros(b)
    for rows in rows_by_cluster:
        # per-cluster contribution to the idx variance: (sum_{i in g} xa_i u_ij)^2
        sg = xa[rows] @ resid2d[rows]  # (b,)
        var += sg * sg
    se = np.sqrt(np.maximum(var, 1e-300))
    return se if is_2d else float(se[0])


def _wild_cluster_bootstrap_reject(X, y, w, cluster, idx, rng, alpha):
    """One-sided Webb six-point wild-cluster bootstrap test that beta[idx] > 0.

    Restricted (null-imposed, "WCR") bootstrap (CGM 2008; Webb 2023 six-point weights, the small-G
    remedy for Rademacher degeneracy): impose H0 beta[idx]=0, resample cluster-level Webb weights on
    the restricted residuals, studentize each bootstrap statistic by its own CR SE, and compare the
    original studentized statistic to the one-sided (1-alpha) bootstrap quantile. Vectorized across
    the WILD_B bootstrap columns. Returns True if the one-sided null is rejected.
    """
    W = np.asarray(w, dtype=float)
    XW = X * W[:, None]
    XtWX = X.T @ XW
    XtWX_inv = np.linalg.pinv(XtWX)  # pinv: the BMN design can be rank-deficient in thin draws
    H = XtWX_inv @ XW.T               # hat map y -> beta (k x n); fixed across the bootstrap
    clusters, rows_by_cluster = _cluster_index_map(cluster)

    beta = H @ y
    resid = y - X @ beta
    se = _cr_se_of_coef(XW, XtWX_inv, resid, rows_by_cluster, idx)
    t_obs = beta[idx] / se

    # restricted estimate with beta_r[idx] = 0: drop the idx direction (one linear restriction).
    denom = XtWX_inv[idx, idx]
    lam = beta[idx] / max(denom, 1e-300)
    beta_r = beta - XtWX_inv[:, idx] * lam   # c = e_idx, so beta_r[idx] = 0
    fitted_r = X @ beta_r
    resid_r = y - fitted_r

    # Webb cluster weights: (G x B), expanded to (n x B) via the cluster map.
    wgt = rng.choice(_WEBB_SUPPORT, size=(clusters.size, WILD_B))  # (G x B)
    cluster_pos = np.searchsorted(clusters, cluster)               # map each row to its cluster slot
    v = wgt[cluster_pos]                                           # (n x B)
    Ystar = fitted_r[:, None] + resid_r[:, None] * v              # (n x B)
    Bbeta = H @ Ystar                                             # (k x B)
    Resid_star = Ystar - X @ Bbeta                               # (n x B)
    se_star = _cr_se_of_coef(XW, XtWX_inv, Resid_star, rows_by_cluster, idx)  # (B,)
    t_boot = Bbeta[idx] / se_star

    crit = np.quantile(t_boot, 1.0 - alpha)  # one-sided 'larger'
    return bool(t_obs > crit)


def _draw_periods(rng, tau, n_periods):
    """Map holding intervals to integer quarterly (t1, t2) period indices on the window grid."""
    span = np.clip(np.round(tau * PERIODS_PER_YEAR).astype(int), 1, n_periods - 1)
    t1 = np.array([rng.integers(0, n_periods - s) for s in span])
    t2 = t1 + span
    return t1, t2


def mc_power(
    n_per_side: int,
    m_bar: float,
    rho_icc: float,
    n_rep: int,
    rng: np.random.Generator,
    delta_window: float = DELTA_RATE_WINDOW,
) -> float:
    n = 2 * n_per_side
    G = max(2, int(round(n / m_bar)))  # boundary-segment clusters implied by mean cluster size m_bar
    V0 = SIGMA_IDIO_PRIOR ** 2
    # Per-period differential growth so the WINDOW-cumulative differential equals delta_window:
    # a pair spanning the full window (N_PERIODS periods) accrues the full gap (commensurate scaling,
    # finding ...-scale-4); shorter pairs carry beta_per_period*(t2-t1), proportionally less.
    beta_per_period = delta_window / N_PERIODS
    rejects = 0
    for _ in range(n_rep):
        # realized cluster structure (freeze resolution): sizes and treatment
        # composition RESAMPLED from the frozen cell's per-segment vectors, so
        # the simulated design carries the realized size skew and composition.
        shares = rng.choice(REALIZED_SEG_SIZE_SHARES, size=G, replace=True)
        cluster = rng.choice(G, size=n, p=shares / shares.sum())
        # cluster-level treatment propensity -> side composition VARIES across segments, so the
        # segment random effect u_c LOADS on the side contrast (finding ...-inert-1).
        p_c = rng.choice(REALIZED_SEG_HI_SHARES, size=G, replace=True)
        side = (rng.random(n) < p_c[cluster]).astype(int)
        tau = _draw_holdings(rng, n)
        t1, t2 = _draw_periods(rng, tau, N_PERIODS)
        Vt = v_tau(tau)
        u = rng.normal(0.0, math.sqrt(max(rho_icc, 0.0) * V0), size=G)[cluster]
        e = rng.normal(0.0, np.sqrt(np.maximum((1.0 - rho_icc) * Vt, 1e-12)))
        # common index path theta_p (nuisance); a mild upward drift, differenced out within-pair.
        # justify: theta is INERT to size/power — the boundary_side x period DiD contrast is
        # orthogonal to the common period path (the BMN period dummies absorb it exactly), so the
        # 0.01 innovation scale affects no reported quantity; it exists only to keep the simulated
        # index path realistic in diagnostics.
        theta = np.cumsum(rng.normal(0.0, 0.01, size=N_PERIODS - 1))
        X, idx_diff = _build_repeat_sales_design(t1, t2, side, N_PERIODS)
        # per-pair side differential = beta_per_period * holding span * side (the within-PIN DiD).
        side_diff_i = beta_per_period * (t2 - t1).astype(float) * side
        index_component = X[:, : N_PERIODS - 1] @ theta
        y = index_component + side_diff_i + u + e
        w = 1.0 / Vt  # Case-Shiller WLS weights
        if _wild_cluster_bootstrap_reject(X, y, w, cluster, idx_diff, rng, ALPHA):
            rejects += 1
    return rejects / n_rep


def _deff_bracket_hi(m_bar: float, rho_icc: float, n_floor_side: int) -> int:
    """Upper bisection bound = analytic Kish-DEFF requirement * a safety margin.

    The Kish DEFF n_floor*(1+(m_bar-1)*rho) brackets the exchangeable-within-cluster requirement
    from above; the MC requirement lands at or below it. Capping the bisection at DEFF * margin
    (not a flat 2000) avoids an expensive n=2000 power evaluation while remaining a justified,
    data-driven bound — if the realized requirement exceeds this bracket the cap is returned and
    flagged (it cannot, by the DEFF argument, unless the MC and analytic disagree, which is itself
    diagnostic). margin=1.5 leaves headroom for the per-pair pro-rating correction above the floor.
    """
    de = deff(m_bar, rho_icc)
    return max(int(math.ceil(n_floor_side * de * 1.5)), n_floor_side + 50)


def mc_required_n_per_side(
    m_bar: float, rho_icc: float, n_rep: int, rng: np.random.Generator,
    n_floor_side: int, lo: int = 50, hi: int | None = None,
    delta_window: float = DELTA_RATE_WINDOW,
) -> int:
    """Smallest n/side achieving POWER_TARGET via bisection on the MC power curve.

    hi defaults to the analytic Kish-DEFF bracket * margin (justified data-driven cap), not a flat
    2000, so the expensive top-of-range power evaluation is avoided.
    """
    if hi is None:
        hi = _deff_bracket_hi(m_bar, rho_icc, n_floor_side)

    def powered(n):
        return mc_power(n, m_bar, rho_icc, n_rep, rng, delta_window) >= POWER_TARGET
    if powered(hi) is False:
        return hi  # cap (DEFF bracket exceeded — flagged by the caller)
    while lo < hi:
        mid = (lo + hi) // 2
        if powered(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# --------------------------------------------------------------------------- #
# Assumption grid — RESOLVED AT FREEZE (2026-07-06) from the realized qualified
# buffer (docs/research_notes/qualification_counts_2026-07-06.md, G*=G_noise
# rule, 250 m band):
#   m_bar in {112.5, 127.5, 139.7, 141.0} = realized mean pairs/segment at the
#     q_top ladder {10, 20, 25, 33.3} respectively (the q_top selection rule
#     evaluates required-n at each rung's own realized m_bar).
#   rho_icc in {0, 0.02, 0.05, 0.10} — UNCHANGED registered grid: rho is kept
#     outcome-blind (estimating it needs outcome residuals, which are sealed
#     until post-freeze), so the freeze pins the registered central 0.05 with
#     the grid as sensitivity, NOT a realized estimate.
# Central case = (rho = 0.05, m_bar = 112.5): the FINEST ladder rung (q_top=10,
# ISBE-Exemplary tier) at the registered 250 m power-basis bandwidth.
# --------------------------------------------------------------------------- #
RHO_GRID = [0.0, 0.02, 0.05, 0.10]   # justify: brackets plausible intra-segment correlation; 0=i.i.d.
M_BAR_GRID = [112.5, 127.5, 139.7, 141.0]  # justify: realized m_bar per q_top rung (freeze resolution above).
RHO_CENTRAL = 0.05                   # justify: registered central assumption; outcome-blind (no realized estimate pre-freeze).
M_BAR_CENTRAL = 112.5                # justify: realized m_bar of the selected finest rung (q_top=10, 250 m).

N_REP = 2000  # justify: MC replications per power evaluation; bisection cost-bounded; CI on power
#                at p=0.8, n=2000 is +-1.8pp (binomial), adequate for an n-bisection to nearest pair.


# --------------------------------------------------------------------------- #
# Reproducibility: canonical config hash + mechanical ReproLog emission.
# config_resolved_sha256 is defined over a FILE-INDEPENDENT, deterministically recomputable input:
#   sha256( sha256(design.md)_hex || "\n" || sha256(this_script_source)_hex )
# This removes the self-referential rendered-markdown slice (root cause of repro-config-sha-stale-1)
# and is recomputable by any third party with the two source files.
# --------------------------------------------------------------------------- #
_HERE = Path(__file__).resolve()
_DESIGN_MD = _HERE.parent / "design.md"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def canonical_config_sha256() -> str:
    """sha256(sha256(design.md) || '\\n' || sha256(power_sim source)). File-independent, recomputable."""
    design_sha = _sha256_file(_DESIGN_MD)
    script_sha = _sha256_file(_HERE)
    return hashlib.sha256(f"{design_sha}\n{script_sha}".encode()).hexdigest()


def _load_emit_repro_log():
    """Import the project's emit-repro-log skill (path per CLAUDE.md reproducibility contract).

    The skill defines @dataclass classes; under importlib.spec_from_file_location the module must be
    registered in sys.modules BEFORE exec_module, else dataclasses' _is_type lookup of
    sys.modules[cls.__module__] returns None and crashes (CPython dataclasses.py _is_type).
    """
    skill_path = Path.home() / ".claude" / "skills" / "emit-repro-log" / "assets" / "emit_repro_log.py"
    spec = importlib.util.spec_from_file_location("emit_repro_log_skill", skill_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # register BEFORE exec so @dataclass module lookup resolves
    spec.loader.exec_module(mod)
    return mod


def emit_repro_log() -> dict:
    """Capture + write a 13-field ReproLog, assert verify(), and return the run-record fields."""
    erl = _load_emit_repro_log()
    cfg_sha = canonical_config_sha256()
    log = erl.capture(
        phase="validation",
        hypothesis_id="H002",
        rng_seed=RNG_SEED,
        dataset_checksums={},  # no dataset frozen yet — PROSPECTIVE power from a literature prior
        config_resolved_sha256=cfg_sha,
    )
    out_path = _HERE.parents[3] / "logs" / "reproducibility" / f"repro_log_{log.run_id}.json"
    log.write(out_path)
    if not erl.ReproLog.verify(out_path):
        raise RuntimeError(f"ReproLog round-trip verification FAILED for {out_path}")
    d = log.to_dict()
    return {
        "run_id": d["run_id"],
        "repro_log_path": f"logs/reproducibility/repro_log_{d['run_id']}.json",
        "phase": d["phase"],
        "hypothesis_id": d["hypothesis_id"],
        "rng_seed": d["rng_seed"],
        "git_head": d["git_head"],
        "pip_freeze_sha256": d["pip_freeze_sha256"],
        "env_id": d["env_id"],
        "config_resolved_sha256": d["config_resolved_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="H002 prospective power simulation")
    parser.add_argument(
        "--emit-repro-log", action="store_true",
        help="emit the 13-field ReproLog + print the run-record fields the markdown must mirror",
    )
    args = parser.parse_args()

    rng = np.random.default_rng(RNG_SEED)

    n_iid = iid_floor_n_per_side()
    n_iid_ceil = math.ceil(n_iid)
    print(f"[1] i.i.d. FLOOR  n/side = {n_iid:.4f} -> ceil {n_iid_ceil} ; total {2*n_iid_ceil}",
          flush=True)

    print("\n[2] analytic DEFF cross-check  n_required = n_floor * DEFF (Kish):", flush=True)
    print("    m_bar  rho    DEFF     n/side   total", flush=True)
    for m in M_BAR_GRID:
        for r in RHO_GRID:
            de = deff(m, r)
            nps = math.ceil(n_iid_ceil * de)
            star = "  <-- central" if (m == M_BAR_CENTRAL and r == RHO_CENTRAL) else ""
            print(f"    {m:5.0f}  {r:4.2f}  {de:6.3f}   {nps:6d}   {2*nps:6d}{star}", flush=True)

    print("\n[3] MC power of the repeat-sales WLS boundary_side x period DiD differential", flush=True)
    print("    (cluster-level treatment so rho LOADS the contrast; heteroskedastic V(tau);", flush=True)
    print("     Webb six-point wild-cluster bootstrap one-sided test):", flush=True)
    print(f"    V(tau)=A+B*tau  A={A_COEF:.5f}  B={B_COEF:.5f}  (V(mean_hold)={v_tau(MEAN_HOLD_YEARS):.5f}=sigma^2)",
          flush=True)
    print(f"    N_PERIODS={N_PERIODS} quarterly dummies; WILD_B={WILD_B} bootstrap reps", flush=True)
    print("    m_bar  rho    MC n/side  total  G", flush=True)
    grid: dict[tuple[float, float], int] = {}
    central_n = None
    for m in M_BAR_GRID:
        for r in RHO_GRID:
            nreq = mc_required_n_per_side(m, r, N_REP, rng, n_floor_side=n_iid_ceil)
            grid[(m, r)] = nreq
            Gimplied = max(2, int(round(2 * nreq / m)))
            star = ""
            if m == M_BAR_CENTRAL and r == RHO_CENTRAL:
                star = "  <-- central"
                central_n = nreq
            print(f"    {m:5.0f}  {r:4.2f}  {nreq:7d}  {2*nreq:6d}  {Gimplied:3d}{star}", flush=True)

    # rho-monotonicity at m_bar=20 read from the STORED grid (no extra evals, no RNG divergence):
    # required n should be NON-DECREASING in rho now the segment effect loads the contrast
    # (finding power-mc-clustering-inert-1). Allow a couple pairs of MC noise.
    print("\n[check] rho-monotonicity at m_bar=20 (required n should rise with rho):", flush=True)
    prev = None
    mono_ok = True
    for r in RHO_GRID:
        nreq = grid[(M_BAR_CENTRAL, r)]
        flag = ""
        if prev is not None and nreq < prev - 2:
            flag = "  <-- DECREASE (clustering inert?)"
            mono_ok = False
        print(f"    rho={r:4.2f}  n/side={nreq}{flag}", flush=True)
        prev = nreq
    print(f"    monotonic(non-decreasing) in rho: {mono_ok}", flush=True)

    print(f"\n[OPERATIVE] central (rho={RHO_CENTRAL}, m_bar={M_BAR_CENTRAL}) "
          f"n_required_for_power_80 = {central_n}/side = {2*central_n} total", flush=True)

    if args.emit_repro_log:
        rec = emit_repro_log()
        print("\n[REPROLOG] emitted + verified. Mirror these into the markdown run-record table:")
        for k, v in rec.items():
            print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
