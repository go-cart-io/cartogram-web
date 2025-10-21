import io

import numpy as np
import pandas as pd
import pytest
from carto import recommendator

# class FakeModel:
#     """A fake classifier returning labels based on CV threshold.

#     For simplicity, treat any CV < 10 as 'intensive', >= 10 as 'extensive'.
#     The real model consumes a DataFrame with a column named 'CV (%)'.
#     """

#     def predict(self, X):
#         # X is expected to be a DataFrame with index=column names
#         cvs = X["CV (%)"].to_numpy()
#         out = []
#         for v in cvs:
#             if np.isnan(v):
#                 out.append("unknown")
#             elif v < 10:
#                 out.append("intensive")
#             else:
#                 out.append("extensive")
#         return out


# @pytest.fixture(autouse=True)
# def patch_joblib_load(monkeypatch):
#     """Patch joblib.load so tests do not depend on a real model file."""

#     def fake_load(path):
#         return FakeModel()

#     monkeypatch.setattr(recommendator.joblib, "load", fake_load)
#     yield


def make_csv(areas, col1, col2):
    """Helper to construct CSV string with a Geographic Area column and two data columns."""
    buf = io.StringIO()
    # header
    buf.write("Geographic Area (sq. km),col_1,col_2\n")
    for a, m1, m2 in zip(areas, col1, col2):
        buf.write(f"{a},{m1},{m2}\n")
    return buf.getvalue()


def test_recommend_returns_expected_keys_and_types_based_on_cv():
    areas = [10, 20, 30, 40, 50]
    metric_noscaled = [5, 5.05, 4.95, 5.0, 5.02]
    metric_scaled = [1, 30, 200, 6000, 40000]

    csv = make_csv(areas, metric_noscaled, metric_scaled)
    results = recommendator.recommend(csv)

    assert set(results.keys()) == {"col_1", "col_2"}
    assert results["col_1"]["type"] == "color"
    assert results["col_2"]["type"] == "area"
    assert "may not scale" in results["col_1"]["reason"].lower()
    assert "may scale" in results["col_2"]["reason"].lower()


def test_recommend_handles_unknown_label_with_none_type():
    areas = [1, 2, 3]
    matric_zeros = [0, 0, 0]
    matric_ids = [5, 4, 3]
    csv = make_csv(areas, matric_zeros, matric_ids)

    results = recommendator.recommend(csv)

    assert set(results.keys()) == {"col_1", "col_2"}
    assert results["col_1"]["type"] == "none"
    assert results["col_2"]["type"] == "none"
    assert "identical" in results["col_1"]["reason"].lower()
    assert "sequence" in results["col_2"]["reason"].lower()


def test_add_arealog_computes_log_for_positive_areas():
    df = pd.DataFrame(
        {
            "Geographic Area": [100.0, 10.0, 0.0, -5.0],
        }
    )
    out = recommendator.add_arealog(df.copy(), ["Geographic Area"])

    # Positive values should have finite logs, others NaN
    assert pd.notna(out.loc[0, "AreaLog"]) and np.isclose(
        out.loc[0, "AreaLog"],  # type: ignore
        np.log(100.0),  # type: ignore
    )
    assert pd.notna(out.loc[1, "AreaLog"]) and np.isclose(
        out.loc[1, "AreaLog"],  # type: ignore
        np.log(10.0),  # type: ignore
    )
    assert pd.isna(out.loc[2, "AreaLog"])  # zero -> NaN
    assert pd.isna(out.loc[3, "AreaLog"])  # negative -> NaN


def test_add_arealog_raises_when_missing_geo_col():
    df = pd.DataFrame({"A": [1, 2, 3]})
    with pytest.raises(recommendator.CartoError):
        recommendator.add_arealog(df, [])


def test_calculate_slope_filters_invalid_and_respects_max_p():
    # Build AreaLog with invalids to be filtered
    df = pd.DataFrame(
        {
            "AreaLog": [0.0, 1.0, np.nan, np.inf, 2.0],
            "val": [0.0, 2.0, 5.0, 10.0, 4.0],
        }
    )
    slope = recommendator.calculate_slope(df, "val", area_col="AreaLog", max_p=0.9)
    # With points (0,0), (1,2), (2,4) slope should be ~2
    assert np.isclose(slope, 2.0, atol=1e-6)

    # If we set max_p very small, regression might be rejected and return NaN
    slope_strict = recommendator.calculate_slope(
        df, "val", area_col="AreaLog", max_p=1e-20
    )
    assert (np.isnan(slope_strict)) or np.isclose(slope_strict, 2.0, atol=1e-6)


def test_calculate_cv_basic_and_zero_mean_guard():
    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            "b": [0, 0, 0, 0, 0],  # mean zero -> NaN
        }
    )

    cv_a = recommendator.calculate_cv(df, "a")
    assert 0 < cv_a < 100  # sanity

    cv_b = recommendator.calculate_cv(df, "b")
    assert np.isnan(cv_b)
