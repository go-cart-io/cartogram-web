import csv
import re
from io import StringIO

import numpy as np
import pandas as pd
from errors import CartoError
from utils import file_utils


def process_data(
    csv_string: str, vis_types: dict, area_data_path: str | None = None
) -> tuple[dict, dict[str, str]]:
    df = read_data(csv_string)
    df, map_regions_dict = format_regions(df)
    df = drop_empty_color_inset(df)
    df, data_cols = reorder_columns(df)

    data_names = {}
    for column in data_cols:
        df, name = format_data_column(df, column, vis_types)
        data_names[column] = name

    if area_data_path:
        with open(area_data_path, "w") as outfile:
            outfile.write(df.to_csv(index=False))

    return map_regions_dict, data_names


def read_data(csv_string: str) -> pd.DataFrame:
    # Read with Python's csv module to preserve empty strings
    rows = []
    csv_reader = csv.DictReader(StringIO(csv_string))
    for row in csv_reader:
        rows.append(row)

    return pd.DataFrame(rows)


def format_regions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    map_names_dict = {}

    # Convert region names to string and replace invalid characters (\ ")
    df["Region"] = df["Region"].astype(str)
    df["Region"] = df["Region"].str.replace(r'\\|"', "_", regex=True)

    # Replace empty strings with NaN, then drop rows with NaN in the 'Region' column
    initial_nrows = len(df)
    df = df.replace(r"^\s*$", np.nan, regex=True).dropna(subset=["Region"])

    # Create name map
    if "RegionMap" in df.columns:
        if not df["RegionMap"].equals(df["Region"]) or initial_nrows != len(df):
            map_names_dict = dict(zip(df["RegionMap"], df["Region"]))
        df = df.drop(columns=["RegionMap"])

    return df, map_names_dict


def drop_empty_color_inset(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["Color", "Inset"]:
        if col in df.columns and df[col].isna().all():
            df = df.drop(columns=[col])
    return df


def reorder_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    # Just to make sure ColorGroup column exists. Color assignment should be done during geojson processing
    df["ColorGroup"] = df["ColorGroup"] if "ColorGroup" in df else ""

    # Priority columns (may not all exist in df)
    priority = ["Region", "RegionLabel", "Color", "ColorGroup", "Inset"]

    # Keep only those that are actually in df
    priority = [col for col in priority if col in df.columns]

    # Columns starting with "Geographic Area"
    geo_cols = [col for col in df.columns if col.startswith("Geographic Area")]

    # Remaining columns (not in priority or geo)
    remaining = [col for col in df.columns if col not in priority + geo_cols]

    # New column order
    new_order = priority + geo_cols + remaining
    return df[new_order], remaining


def format_data_column(df: pd.DataFrame, column: str, vis_types: dict):
    file_utils.validate_filename(column)

    m = re.match(r"(.+)\s?\((.+)\)$", column)
    if m:
        name = m.group(1).strip()
    else:
        name = column.strip()

    df[column] = pd.to_numeric(df[column], errors="coerce")

    if name == "":
        raise CartoError(
            "Missing data name. Please ensure each data column has a name in its header."
        )

    if df[column].isna().all():
        raise CartoError(
            f"Cannot process {column}: All rows are empty. Please enter some numeric values or remove the column."
        )

    sum = df[column].sum()
    if column in vis_types["cartogram"] and sum == 0:
        raise CartoError(
            f"Cannot process {column}: Sum is zero. Please ensure the sum of data is not zero."
        )

    return df, name
