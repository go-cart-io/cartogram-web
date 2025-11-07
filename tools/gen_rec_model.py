import os
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree

sys.path.append(os.path.join(os.path.dirname(__file__), "../internal"))

from carto import recommendator
from handler_metadata import cartogram_handlers  # type: ignore

SCRIPT_DIR = Path(__file__).parent
MODEL_DIR = SCRIPT_DIR.parent / "internal" / "carto" / "models"


"""Create and persist a small ML recommendator model for cartogram visualization.

This script collects features from World Bank data and the local `cartdata`
handlers, trains a small decision-tree classifier to predict a visualization
``Type`` from a numeric feature produced by :mod:`recommendator.FEATURE_FUNC`, 
and writes the trained model to ``internal/carto/model.pkl``.

The module is intended as a developer utility to rebuild the recommendator
model. It is not part of the server runtime.

Key functions:
- get_WB(): build features from World Bank CSVs
- get_gocart(): build features from local cartdata handlers
- predict(): train and evaluate a classifier

Assumptions:
- CSV files referenced by the script exist under ``tools/model-data`` and
    ``internal/static/cartdata``.
"""


def get_WB():
    """Load World Bank CSVs, compute feature values, and return a DataFrame.

    The function reads two CSVs from ``tools/model-data``:
    - ``WB_data.csv``: the numeric observations used to compute the feature
      via ``recommendator.FEATURE_FUNC``.
    - ``WB_meta.csv``: metadata that maps ``Indicator.Code.x`` to a target
      visualization ``Type``.

    Returns:
        pandas.DataFrame: DataFrame with columns ``Type`` and
            ``recommendator.FEATURE_NAME`` suitable for training.
    """

    data_file = SCRIPT_DIR / "model-data" / "WB_data.csv"
    csv_data = pd.read_csv(data_file)

    # Add an arealog column used by FEATURE_FUNC to compute slopes/features
    csv_data = recommendator.add_arealog(csv_data, ["Area"])
    feature_df = (
        csv_data.groupby("Indicator.Code.x")
        .apply(recommendator.FEATURE_FUNC, "Value", include_groups=False)  # type: ignore
        .to_frame(name=recommendator.FEATURE_NAME)
    )

    feature_df.index.name = "Indicator.Code.x"
    feature_df = feature_df.reset_index()

    meta_file = SCRIPT_DIR / "model-data" / "WB_meta.csv"
    meta_data = pd.read_csv(meta_file)
    meta_data = meta_data.dropna(subset=["Type"])

    merged_df = pd.merge(
        meta_data[["Indicator.Code.x", "Type"]],
        feature_df,
        on="Indicator.Code.x",
        how="inner",
    )

    # Return only the target 'Type' and the single computed feature column
    return merged_df[["Type", recommendator.FEATURE_NAME]]


def get_gocart():
    """Collect feature values from local cartdata handlers and return a DataFrame.

    The function iterates over entries in ``handler_metadata.cartogram_handlers``,
    reads each handler's ``data.csv`` from ``internal/static/cartdata/<handler>/``,
    computes the feature using ``recommendator.FEATURE_FUNC``, and records the
    associated visualization type from the handler metadata.

    Returns:
        pandas.DataFrame: DataFrame with columns ``Type`` and
            ``recommendator.FEATURE_NAME``.
    """

    CARTDATA_PATH = os.path.join(
        os.path.dirname(__file__), "../internal/static/cartdata"
    )
    data_folder = Path(CARTDATA_PATH)
    data = {"Type": [], recommendator.FEATURE_NAME: []}

    for handler in cartogram_handlers:
        csv_path = data_folder / handler / "data.csv"
        df = pd.read_csv(csv_path)
        df = recommendator.add_arealog(df, ["Geographic Area (sq. km)"])

        # Default visualization type map; handlers may provide an explicit map
        vis_types = {
            "Population (people)": "contiguous",
        }
        if "types" in cartogram_handlers[handler]:
            vis_types = cartogram_handlers[handler]["types"]

        # If population is present, add a derived population density field
        if (
            "Geographic Area (sq. km)" in df.columns
            and "Population (people)" in vis_types
            and "Population Density (per sq. km)" not in vis_types
        ):
            df["Population Density (per sq. km)"] = (
                df["Population (people)"] / df["Geographic Area (sq. km)"]
            )
            vis_types["Population Density (per sq. km)"] = "choropleth"

        for col in vis_types:
            if vis_types[col] == "choropleth":
                data["Type"].append("intensive")
            elif vis_types[col] == "contiguous" or vis_types[col] == "noncontiguous":
                data["Type"].append("extensive")
            else:
                continue

            slope = recommendator.FEATURE_FUNC(df, col)
            data[recommendator.FEATURE_NAME].append(slope)

    # Return the collected data as a DataFrame so callers can concat with other
    # data sources (matches the return shape of get_WB()).
    return pd.DataFrame(data)


def predict(train, test, features):
    """Train a classifier on the provided train/test splits and return it.

    Args:
        train (pandas.DataFrame): Training frame containing a ``Type`` column
            and one or more feature columns.
        test (pandas.DataFrame): Test frame with the same columns as ``train``.
        features (list[str]): List of column names in ``train``/``test`` to use
            as input features.

    Returns:
        sklearn.base.BaseEstimator: Trained scikit-learn classifier instance.

    Behavior:
        Uses a small Decision Tree (entropy criterion, max_depth=3) which is
        deterministic and easy to inspect. Prints the macro F1 score on the
        provided test set for quick feedback.
    """

    X_train = train[features]
    X_test = test[features]
    y_train = train["Type"]
    y_test = test["Type"]

    # Use a small decision tree for explainability and stable results
    model = DecisionTreeClassifier(
        criterion="entropy",
        max_depth=3,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
    )

    # Train the classifier on the training data
    model.fit(X_train, y_train)

    # Predict the labels of the testing data
    y_pred = model.predict(X_test)

    # Calculate the F1 score as a quick evaluation metric
    f1 = f1_score(y_test, y_pred, average="macro")
    print("F1:", f1)

    # Visualize the tree
    plt.figure(figsize=(20, 10))  # Adjust size for better readability
    plot_tree(
        model,
        feature_names=[recommendator.FEATURE_NAME],
        class_names=[
            "extensive",
            "intensive",
        ],  # Names of each of the target classes in ascending numerical order
        filled=True,  # Color nodes to indicate the majority class
    )
    plt.savefig(MODEL_DIR / (recommendator.FEATURE_NAME + ".png"))
    plt.close()

    return model


data1 = get_WB()
data2 = get_gocart()
data = pd.concat([data1, data2])
# print(data)

train, test = train_test_split(data, test_size=0.2, random_state=42)
model = predict(train, test, [recommendator.FEATURE_NAME])

model_file = MODEL_DIR / (recommendator.FEATURE_NAME + ".pkl")
joblib.dump(model, model_file)
