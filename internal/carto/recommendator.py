from io import StringIO
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from errors import CartoError
from scipy import stats


def recommend(csv_string):
    """
    Recommend visualization for each data column.

    Parameters:
    csv_string (str): CSV data as a string

    Returns:
    dict: Dictionary with column names as keys and {type, reason} as values
    """
    df = pd.read_csv(StringIO(csv_string))

    # Identify geographic columns, reserved columns, and data columns
    geo_cols = [col for col in df.columns if col.startswith("Geographic Area")]
    reserved = ["Region", "RegionLabel", "Color", "ColorGroup", "Inset"]
    reserved = [col for col in reserved if col in df.columns]
    reserved = reserved + geo_cols
    data_cols = [col for col in df.columns if col not in reserved]

    # Compute AreaLog (log of geographic area) which is used by some
    # feature functions (for example, slope vs log(area)). This will raise
    # a CartoError if no geographic column is present.
    df = add_arealog(df, geo_cols)

    # Load the prediction model for the chosen feature
    script_dir = Path(__file__).parent
    model = joblib.load(script_dir / "models" / (FEATURE_NAME + ".pkl"))

    results = {}
    # For each non-reserved column decide whether to recommend: color (intensive),
    # area/cartogram (extensive), or none.
    for col in data_cols:
        # 1) If the column is uniform there's nothing to visualize.
        is_uniform = df[col].nunique() <= 1
        if is_uniform:
            results[col] = {
                "type": "none",
                "reason": "This column contains identical values, so visualization won’t add any extra insight.",
            }
            continue

        # 2) If the values form an arithmetic progression (common for IDs)
        # then it's likely not a meaningful numeric variable to visualize.
        is_ordered = is_arithmetic_progression(df, col)
        if is_ordered:
            results[col] = {
                "type": "none",
                "reason": "The values follow a consistent pattern, like an arithmetic sequence. If this represents an ID or index, a visualization may not be meaningful.",
            }
            continue

        # 3) Compute the feature (e.g. Slope or CV). Return none if can't compute.
        feature_result = FEATURE_FUNC(df, col)

        # Unpack tuple (slope, r_squared) or handle scalar for CV
        if isinstance(feature_result, tuple):
            feature_value, r_squared = feature_result
        else:
            feature_value = feature_result
            r_squared = np.nan

        if not feature_value or np.isnan(feature_value):
            results[col] = {
                "type": "none",
                "reason": f"Cannot calculate {FEATURE_NAME}. Unfortunately, we cannot make the recommendation.",
            }
            continue

        # Confidence is R² (0–1), how well log(area) explains this variable
        confidence = round(float(r_squared), 3) if not np.isnan(r_squared) else None

        # 4) Ask the model for a prediction. The model returns a label such as 'intensive' or 'extensive'.
        feature_df = pd.DataFrame({FEATURE_NAME: [feature_value]})
        prediction = model.predict(feature_df)

        # 5) Interpret the model prediction and record the recommendation.
        if FEATURE_NAME == "Slope":
            is_scaled = "may scale" if prediction == "extensive" else "may not scale"
            reason = (
                f"The slope between {col} and the log of Geographic Area is {feature_value:.2f}, "
                f"suggesting they {is_scaled} proportionally with region area. "
            )
        elif FEATURE_NAME == "CV":
            reason = f"The Coefficient of Variation is {feature_value:.2f}. "
        else:
            reason = ""

        if prediction == "intensive":
            # Intensive variables (normalized measures) are best shown with color.
            results[col] = {
                "type": "color",
                "reason": reason
                + "We recommend using color to represent this variable in your visualization.",
                "confidence": confidence,
            }
        elif prediction == "extensive":
            # Extensive variables (counts, totals) map naturally to area/cartograms.
            results[col] = {
                "type": "area",
                "reason": reason
                + "We recommend using area to represent this variable in your visualization.",
                "confidence": confidence,
            }

            # If the series contains negative values, area-based mapping may
            # be problematic (areas can't be negative). Warn the user and
            # suggest using color or cleaning the data.
            is_negative_series = df[col] < 0
            if is_negative_series.any():
                results[col]["reason"] = (
                    results[col]["reason"]
                    + " However, some values are negative, which may cause issues when generating cartograms."
                    + " Please consider cleaning the data or using color instead."
                )
        else:
            # In case the model returns an unexpected label, fall back to none.
            results[col] = {
                "type": "none",
                "reason": reason + "Unfortunately, we cannot make the recommendation.",
            }

    return results


def is_arithmetic_progression(df: pd.DataFrame, column_name: str) -> bool:
    """
    Checks if the values in a specified DataFrame column are in a consistent
    arithmetic progression (e.g., 2, 3, 4 or 10, 8, 6).

    This is achieved by calculating the difference between consecutive elements
    and checking if all non-zero differences are the same.

    Args:
        df (pd.DataFrame): The DataFrame to check.
        column_name (str): The name of the numeric column to analyze.

    Returns:
        bool: True if the column is an arithmetic progression (constant step),
              False otherwise.
    """
    # 1. Calculate the difference between consecutive elements
    # The first element's difference will be NaN.
    diffs = df[column_name].diff().dropna()

    # Handle edge case: columns with 0 or 1 rows are trivially ordered.
    if len(diffs) < 1:
        return True

    # 2. Check for uniformity in the differences
    # nunique() counts the number of unique non-NaN values.
    # If the count is 1, all differences are the same, meaning a constant step.
    # This covers sequential (step 1 or -1) and other constant increments (step 2, -5, etc.)
    is_ordered = diffs.nunique() <= 1

    # Optional: If you strictly needed a step of 1 or -1,
    # you would check: (diffs.unique() == 1 or diffs.unique() == -1)

    return is_ordered


def add_arealog(df: pd.DataFrame, geo_cols: list[str]):
    """
    Calculate log of the first geographic area column found.

     Parameters
     ----------
     df : pd.DataFrame
         Input DataFrame that must contain at least one geographic column.
     geo_cols : list[str]
         List of column names that identify geographic area columns. The
         function uses the first entry (geo_cols[0]) as the numeric area
         value to compute the natural logarithm.

     Returns
     -------
     pd.DataFrame
         The same DataFrame instance with a new column `AreaLog` added.

     Raises
     ------
     CartoError
         If `geo_cols` is empty (no geographic area column found).

     Notes
     -----
     - Rows where the geographic area value is missing or non-positive will
       have `AreaLog` set to NaN (we only take log for values > 0).
     - The function mutates and returns the original DataFrame for
       convenience; callers should be aware that `df` is modified in place.
    """

    # Validate presence of at least one geographic column
    if not geo_cols or len(geo_cols) <= 0:
        raise CartoError(
            "Cannot recommend the visualization - Geographic Area column not found."
        )

    # Initialize AreaLog with NaN for all rows to avoid KeyErrors later.
    df["AreaLog"] = np.nan

    # Compute natural log of the geographic area only for positive values.
    # We use the first geographic column found (geo_cols[0]).
    # Non-positive or missing area values remain NaN.
    df.loc[df[geo_cols[0]] > 0, "AreaLog"] = np.log(
        df.loc[df[geo_cols[0]] > 0, geo_cols[0]]
    )

    return df


def calculate_slope(df: pd.DataFrame, value_col: str, area_col="AreaLog", max_p=None):
    """
    Compute the slope of a linear regression between a numeric value column
    and an area-related column (by default `AreaLog`).

    The function performs the following steps:
    1. Filters rows where both `area_col` and `value_col` are present.
    2. Coerces values to numeric and drops non-finite entries (NaN/inf).
    3. If there are at least two distinct x-values, fits a linear model
       with scipy.stats.linregress and returns the slope. Optionally the
       result is only returned if the regression p-value is below `max_p`.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    value_col : str
        Name of the dependent variable column (y).
    area_col : str, optional
        Name of the independent variable column (x). Defaults to "AreaLog".
    max_p : float or None, optional
        If provided, the slope is returned only when the regression p-value
        is less than `max_p`. If None, the slope is returned regardless of
        statistical significance.

    Returns
    -------
    tuple[float, float]
        A tuple of (slope, r_squared). Both are NaN if insufficient data or
        if significance criteria are not met.
    """

    # 1) Select rows where both the area and value columns are present
    valid_mask = df[area_col].notna() & df[value_col].notna()

    # 2) Convert to numeric; invalid parsing becomes NaN (coerce).
    x = pd.to_numeric(df.loc[valid_mask, area_col], errors="coerce")
    y = pd.to_numeric(df.loc[valid_mask, value_col], errors="coerce")

    # 3) Remove entries where either x or y are not finite (NaN/inf)
    valid_mask2 = np.isfinite(x) & np.isfinite(y)
    x = x[valid_mask2]
    y = y[valid_mask2]

    # 4) Require at least two observations and more than one unique x value
    # otherwise regression is not meaningful.
    if len(x) >= 2 and x.nunique() > 1:
        res = stats.linregress(x, y)

        # If max_p is provided treat p-value as a filter for statistical
        # significance; otherwise accept the slope regardless of p-value.
        if not max_p or res.pvalue < max_p:  # type: ignore
            return res.slope, res.rvalue ** 2  # type: ignore

    # If any check fails return NaN to signal an unavailable slope.
    return np.nan, np.nan


def calculate_cv(df: pd.DataFrame, value_col: str):
    """
    Calculates the Coefficient of Variation (CV) for a given pandas DataFrame.
    CV = (Standard Deviation / Mean) * 100

    The CV is unitless and is expressed as a percentage, indicating the
    relative variability of the data.

    Args:
        df (pd.DataFrame): The data frane for which to calculate the CV.

    Returns:
        float: The Coefficient of Variation as a percentage.
    """
    std_dev = df[value_col].std()
    mean = df[value_col].mean()

    # Check if the mean is close to zero to avoid division by zero error
    # and misleading results (CV is unstable when mean is near zero).
    if np.isclose(mean, 0):
        return np.nan  # Return NaN if mean is effectively zero

    cv = (std_dev / mean) * 100
    return cv


FEATURE_NAME = "Slope"
FEATURE_FUNC = calculate_slope
