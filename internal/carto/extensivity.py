"""
Extensivity guardrail: test whether a variable scales linearly with
geographic area using a Gamma GAM with log link.

Uses a custom thin-plate regression spline (TPRS) implementation that
closely matches R's mgcv (Wood 2003). No external GAM library needed.
"""

import warnings
import numpy as np
import pandas as pd

from carto.tprs import fit_gam_gamma_log

# z_crit for one-sided alpha=0.05
_Z_CRIT = 1.6448536269514729  # scipy.stats.norm.ppf(0.95)
_K_GRID = [4, 6, 8]
_N_MIN = 10


def check_extensivity(
    df,
    value_col,
    population_col,
    area_col="area_km2",
    delta=0.2,
):
    """
    Test whether a variable satisfies area-extensivity using a GAM.

    Fits y ~ x + s(z, k, bs="tp") with Gamma(log) for each k in [4,6,8],
    where x = log(area) and z = log(population/area).
    Uses thin-plate regression splines matching R's mgcv.

    Returns dict with:
    - "extensivity_violated": bool
    - "gamma_max": float or None
    - "reason_code": str ("fit_ok", "abstain:...", "fit_failed")
    - "gamma_hat": float or None
    - "se_gamma": float or None
    """
    # ── Validate columns exist ─────────────────────────────
    required = [value_col, population_col, area_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return _abstain(f"missing_columns_{'_'.join(missing)}")

    # ── Check numeric ──────────────────────────────────────
    for col in required:
        if not np.issubdtype(df[col].dtype, np.number):
            return _abstain(f"non_numeric_{col}")

    # ── Subset to finite, positive rows ────────────────────
    mask = pd.Series(True, index=df.index)
    for col in required:
        vals = df[col]
        mask = mask & np.isfinite(vals) & (vals > 0)

    clean = df.loc[mask].copy()

    if len(clean) == 0:
        return _abstain("all_observations_missing")

    if len(clean) < _N_MIN:
        return _abstain(f"too_few_regions_n{len(clean)}_min{_N_MIN}")

    # ── Derive log-scale predictors ────────────────────────
    y = clean[value_col].values.astype(float)
    x = np.log(clean[area_col].values.astype(float))
    z = np.log(
        clean[population_col].values.astype(float)
        / clean[area_col].values.astype(float)
    )

    X_linear = x.reshape(-1, 1)

    # ── Fit GAM for each k ─────────────────────────────────
    results = []
    for k_val in _K_GRID:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = fit_gam_gamma_log(X_linear, z, y, k_val)

            if not fit["converged"]:
                continue

            gamma_hat = float(fit["linear_coef"][0])
            se_gamma = float(fit["linear_se"][0])

            if np.isfinite(gamma_hat) and np.isfinite(se_gamma):
                gamma_max = gamma_hat + _Z_CRIT * se_gamma
                results.append(
                    {
                        "k": k_val,
                        "gamma_hat": gamma_hat,
                        "se_gamma": se_gamma,
                        "gamma_max": gamma_max,
                    }
                )
        except Exception:
            continue

    if not results:
        return {
            "extensivity_violated": None,
            "gamma_max": None,
            "reason_code": "fit_failed",
            "gamma_hat": None,
            "se_gamma": None,
        }

    # ── Headline: max gamma_max across k values ────────────
    best = max(results, key=lambda r: r["gamma_max"])
    threshold = 1.0 - delta

    return {
        "extensivity_violated": best["gamma_max"] < threshold,
        "gamma_max": best["gamma_max"],
        "reason_code": "fit_ok",
        "gamma_hat": best["gamma_hat"],
        "se_gamma": best["se_gamma"],
    }


def check_extensivity_csv(csv_string, columns, delta=0.2):
    """
    Check extensivity for multiple columns in a CSV string.

    Parameters
    ----------
    csv_string : str
        CSV data as a string (same format as the recommend endpoint).
    columns : list[str]
        Column names to check (typically those selected as cartogram/area).
    delta : float
        Threshold parameter: flag if gamma_max < 1 - delta.

    Returns
    -------
    dict
        Mapping of column name -> check result dict for each column.
        Only includes columns where a check was actually performed.
    """
    df = pd.read_csv(pd.io.common.StringIO(csv_string))

    # Auto-detect area column
    area_col = _find_area_col(df)
    if area_col is None:
        return {}

    # Auto-detect population column
    pop_col = _find_population_col(df)
    if pop_col is None:
        return {}

    results = {}
    for col in columns:
        if col not in df.columns:
            continue
        # Skip checking the population or area column itself
        if col == pop_col or col == area_col:
            continue
        result = check_extensivity(
            df, col, pop_col, area_col=area_col, delta=delta
        )
        if result["reason_code"].startswith("abstain:"):
            continue
        results[col] = result

    return results


def _find_area_col(df):
    """Find the geographic area column in the DataFrame."""
    for col in df.columns:
        if col.startswith("Geographic Area"):
            return col
    if "area_km2" in df.columns:
        return "area_km2"
    return None


def _find_population_col(df):
    """Find a population column in the DataFrame."""
    for col in df.columns:
        col_lower = col.lower()
        if "population" in col_lower or col_lower in (
            "pop_gpw", "pop_ghsl", "pop_wp", "pop",
        ):
            return col
    return None


def _abstain(reason):
    return {
        "extensivity_violated": None,
        "gamma_max": None,
        "reason_code": f"abstain:{reason}",
        "gamma_hat": None,
        "se_gamma": None,
    }
