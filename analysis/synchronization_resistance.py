#!/usr/bin/env python3
"""
Synchronization Resistance (SR) — v2
BAION Bounce v3.1

The idea: instead of reporting R at a single K, measure how hard it is
to make the models synchronize. This combines snapshot (K=0) and dynamics
(coupling response) into a single number per dimension.

THE MATH
--------
Given R(K) — the Kuramoto order parameter as a function of coupling strength:

  R₀ = R(K=0)           — static agreement (snapshot)
  α  = dR/dK ≈ ΔR/ΔK   — coupling susceptibility (how responsive to coupling)
  τ  = threshold         — gate pass/block boundary (e.g., 0.70)

Synchronization Resistance:

        ┌ 0                          if R₀ ≥ τ  (already synchronized)
  SR =  ┤ min((τ - R₀) / α, SR_MAX) if α > ε    (synchronizable)
        ├ ∞ (SR_MAX)                 if |α| ≤ ε  (coupling-inert)
        └ ∞ (SR_MAX)                 if α < -ε   (anti-synchronizing)

  SR_MAX = 2.0  — values above this are extrapolation, not measurement
  ε = 0.01      — minimum detectable slope (see note below)

SR = the coupling strength K_c needed to cross the threshold, capped at SR_MAX.

EPSILON JUSTIFICATION
---------------------
  ε = 0.01 means: "a slope that would move R by 0.01 over K ∈ [0, 1]."
  Below this, the signal is indistinguishable from noise given 6 peers
  and typical R uncertainty of ±0.02–0.05. Validated empirically when
  10-point sweep data is available.

INTERPRETATION
--------------
  SR = 0.0     → Models already agree. No coupling needed. (Factual)
  SR ∈ (0, 1)  → Moderate resistance. Coupling reveals latent agreement.
  SR ≈ 1.0     → High resistance. Coupling at experimental max barely works.
  SR = SR_MAX  → Resistant. Either coupling-inert, anti-synchronizing,
                 or would require K beyond experimental range.

ERROR PROPAGATION
-----------------
  Residual bootstrap: K is a fixed design grid, so we resample the linear-fit
  residuals onto the unchanged K grid (K=0 always present), refit, and recompute
  SR N times, reporting a percentile CI. This captures uncertainty in R₀ and α
  without assuming Gaussian errors and without altering the experimental design
  (resampling (K, R) pairs would drop/duplicate design points, including K=0).

TWO-POINT SHORTCUT
------------------
You only need K=0 and one test K (e.g., K=0.5):

  α ≈ (R(K_test) - R₀) / K_test
  SR = K_test · (τ - R₀) / (R(K_test) - R₀)

This means the replay tool needs exactly 2 runs, not 5.
Shortcut error vs full sweep TBD — needs systematic comparison in Battery 3.
"""

import json
import sys
import numpy as np
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────
SR_MAX = 2.0       # Cap: SR above this is extrapolation, not measurement
EPSILON = 0.01     # Minimum detectable slope (see docstring)
DEFAULT_TAU = 0.70 # Gate pass threshold
BOOTSTRAP_N = 1000 # Resamples for uncertainty estimation


def compute_sr(r_values: list[tuple[float, float]], threshold: float = DEFAULT_TAU,
               bootstrap: bool = True) -> dict:
    """
    Compute Synchronization Resistance from K-sweep data.

    Args:
        r_values: list of (K, R) tuples
        threshold: gate pass threshold (default 0.70)
        bootstrap: if True, compute confidence interval via bootstrap

    Returns:
        dict with R0, alpha, SR, uncertainty, fit quality
    """
    ks = np.array([k for k, r in r_values])
    rs = np.array([r for k, r in r_values])

    # Linear fit first: R(K) = R₀ + α·K
    if len(ks) >= 2:
        coeffs = np.polyfit(ks, rs, 1)  # [slope, intercept]
        alpha = coeffs[0]
        r0_fit = coeffs[1]

        # R² goodness of fit
        rs_pred = np.polyval(coeffs, ks)
        ss_res = np.sum((rs - rs_pred) ** 2)
        ss_tot = np.sum((rs - np.mean(rs)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    else:
        alpha = 0
        r0_fit = float(rs[0]) if len(rs) else 0.0
        r_squared = 0

    # R₀ is DEFINED as R at K=0. Use the measured K=0 point when present;
    # otherwise fall back to the fitted intercept — a principled extrapolation
    # to K=0 (the docstring's "or interpolated"), never an arbitrary raw point.
    # The old `rs[0]` fallback silently relabeled R at the first-listed K as if
    # it were R₀ whenever no K=0 gate existed, corrupting SR with no signal.
    # R0_is_measured records which path was taken so downstream never confuses
    # a measured baseline with an extrapolated one.
    has_k0 = bool((ks == 0.0).any())
    r0 = float(rs[ks == 0.0][0]) if has_k0 else float(r0_fit)

    # Synchronization Resistance with edge case handling
    sr, status = _classify_sr(r0, alpha, threshold)

    result = {
        "R0": round(r0, 4),
        "R0_is_measured": has_k0,
        "R0_fit": round(r0_fit, 4),
        "alpha": round(alpha, 4),
        "SR": round(sr, 4),
        "SR_MAX": SR_MAX,
        "threshold_used": threshold,
        "status": status,
        "fit_r_squared": round(r_squared, 4),
        "data_points": len(ks),
    }

    # Bootstrap uncertainty
    if bootstrap and len(ks) >= 3:
        ci = _bootstrap_ci(ks, rs, threshold)
        result["SR_ci_lower"] = ci[0]
        result["SR_ci_upper"] = ci[1]
        result["SR_uncertainty"] = round((ci[1] - ci[0]) / 2, 4)

    return result


def _classify_sr(r0: float, alpha: float, threshold: float) -> tuple[float, str]:
    """Classify SR value with proper edge case handling."""
    if r0 >= threshold:
        return 0.0, "already_synchronized"

    if alpha < -EPSILON:
        # Coupling makes agreement WORSE
        return SR_MAX, "anti_synchronizing"

    if abs(alpha) <= EPSILON:
        # Coupling has no detectable effect
        return SR_MAX, "coupling_inert"

    # Normal case: positive coupling response
    sr_raw = (threshold - r0) / alpha
    sr_capped = min(sr_raw, SR_MAX)
    status = "synchronizable" if sr_capped < SR_MAX else "resistant"
    return sr_capped, status


def _bootstrap_ci(ks: np.ndarray, rs: np.ndarray, threshold: float,
                  confidence: float = 0.90) -> tuple[float, float]:
    """
    Residual bootstrap confidence interval for SR.

    K is a FIXED experimental design grid, not a random sample. Resampling
    (K, R) pairs with replacement — the old approach — randomly dropped and
    duplicated design points (frequently dropping K=0, which R₀ is defined at,
    and then silently falling back to the min-K point) and distorted the
    regression leverage, so the CI reflected a design that was never run.

    Instead we resample the fit RESIDUALS with replacement and add them back at
    the ORIGINAL fixed K grid, refit, and recompute SR. Every K — including
    K=0 — is present in every resample; only the measurement noise is
    resampled. Uses 90% CI by default (5th–95th percentile).
    """
    rng = np.random.default_rng(42)  # Reproducible
    n = len(ks)

    # R₀ is defined at K=0; without a measured K=0 gate an honest SR CI cannot
    # be formed (the point estimate falls back to the fitted intercept, but
    # bootstrapping that would understate uncertainty). Signal, don't fake it.
    if n < 2 or not bool((ks == 0.0).any()):
        return (0.0, SR_MAX)

    coeffs = np.polyfit(ks, rs, 1)
    fitted = np.polyval(coeffs, ks)
    resid = rs - fitted
    sr_samples = []

    for _ in range(BOOTSTRAP_N):
        # Fixed design: resample residuals onto the unchanged K grid.
        rs_b = fitted + resid[rng.integers(0, n, size=n)]
        r0_b = rs_b[ks == 0.0][0]  # K grid fixed → K=0 always present
        alpha_b = np.polyfit(ks, rs_b, 1)[0]

        sr_b, _ = _classify_sr(r0_b, alpha_b, threshold)
        sr_samples.append(sr_b)

    if not sr_samples:
        return (0.0, SR_MAX)

    lo = (1 - confidence) / 2 * 100
    hi = (1 + confidence) / 2 * 100
    return (
        round(float(np.percentile(sr_samples, lo)), 4),
        round(float(np.percentile(sr_samples, hi)), 4),
    )


def two_point_sr(r0: float, r_test: float, k_test: float,
                 threshold: float = DEFAULT_TAU) -> float:
    """Two-point shortcut: only needs K=0 and one test K."""
    if r0 >= threshold:
        return 0.0
    delta_r = r_test - r0
    if delta_r < -EPSILON * k_test:
        # Anti-synchronizing
        return SR_MAX
    if abs(delta_r) <= EPSILON * k_test:
        # Coupling-inert
        return SR_MAX
    sr_raw = k_test * (threshold - r0) / delta_r
    return min(sr_raw, SR_MAX)


# ── Main: analyze K-sweep data ──

if __name__ == "__main__":
    # Load K-sweep gate outputs
    sweep_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    k_files = sorted(Path(sweep_dir).glob("gate_K*.json"))
    if not k_files:
        print("No gate_K*.json files found in", sweep_dir)
        sys.exit(1)

    # Parse K value from filename and load r-values
    dim_data = {"conclusion": [], "basis": [], "effort": []}

    for f in k_files:
        # Extract K from filename like gate_K0.5.json
        k_str = f.stem.replace("gate_K", "")
        k_val = float(k_str)

        d = json.loads(f.read_text())
        # Fail closed: a missing or malformed r_values MUST abort, never silently
        # become [0,0,0] — zero-substitution corrupts R0/α/SR without any signal.
        rv = d.get("r_values")
        if rv is None:
            sys.exit(f"FAIL-CLOSED: {f} has no 'r_values' key; refusing to substitute zeros.")
        if not isinstance(rv, list) or len(rv) != 3:
            sys.exit(f"FAIL-CLOSED: {f} 'r_values' must be a 3-element list, got {rv!r}.")
        try:
            rv = [float(x) for x in rv]
        except (TypeError, ValueError):
            sys.exit(f"FAIL-CLOSED: {f} 'r_values' has a non-numeric entry: {rv!r}.")

        dim_data["conclusion"].append((k_val, rv[0]))
        dim_data["basis"].append((k_val, rv[1]))
        dim_data["effort"].append((k_val, rv[2]))

    print("=" * 60)
    print("  SYNCHRONIZATION RESISTANCE ANALYSIS (v2)")
    print("=" * 60)
    print(f"  SR_MAX = {SR_MAX}  (values above this are extrapolation)")
    print(f"  ε = {EPSILON}  (minimum detectable slope)")
    print()

    for dim_name, data in dim_data.items():
        result = compute_sr(data)
        print(f"  {dim_name.upper()}")
        print(f"    R₀ (static)     = {result['R0']}")
        print(f"    α (suscept.)    = {result['alpha']}")
        print(f"    SR              = {result['SR']}")
        print(f"    Status          = {result['status']}")
        print(f"    Fit R²          = {result['fit_r_squared']}")
        if "SR_ci_lower" in result:
            print(f"    90% CI          = [{result['SR_ci_lower']}, {result['SR_ci_upper']}]")
            print(f"    Uncertainty     = ±{result['SR_uncertainty']}")
        print()

    # Two-point shortcut demo
    print("-" * 60)
    print("  TWO-POINT SHORTCUT (K=0 and K=0.5 only)")
    print("-" * 60)
    for dim_name, data in dim_data.items():
        r0 = dict(data).get(0.0, 0)
        r05 = dict(data).get(0.5, 0)
        sr2 = two_point_sr(r0, r05, 0.5)
        print(f"    {dim_name:12s}  SR = {sr2:.4f}")

    print()
    print("  FORMULA:")
    print("    SR = min((τ - R₀) / α, SR_MAX)")
    print(f"    where τ = {DEFAULT_TAU}, SR_MAX = {SR_MAX}")
    print()
