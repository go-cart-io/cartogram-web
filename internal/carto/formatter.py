import math
import re
from io import StringIO

import numpy as np
import pandas as pd
import shapely
from errors import CartoError
from utils import file_utils, geojson_utils


def process_data(csv_string, vis_types):
    df = pd.read_csv(StringIO(csv_string), keep_default_na=False, na_values=[""])
    for col in df.columns:
        file_utils.validate_filename(col)

    df["Color"] = df["Color"] if "Color" in df else None
    df["Inset"] = df["Inset"] if "Inset" in df else None
    is_empty_color = df["Color"].isna().all()
    is_empty_inset = df["Inset"].isna().all()

    # Convert region names to string and replace invalid characters (\ ")
    df["Region"] = df["Region"].astype(str)
    df["Region"] = df["Region"].str.replace(r'\\|"', "_", regex=True)

    map_names_dict = {}
    # Replace empty strings with NaN, then drop rows with NaN in the 'Region' column
    initial_nrows = len(df)
    df = df.replace(r"^\s*$", np.nan, regex=True).dropna(subset=["Region"])
    # Create name map
    if "RegionMap" in df.columns:
        if not df["RegionMap"].equals(df["Region"]) or initial_nrows != len(df):
            map_names_dict = dict(zip(df["RegionMap"], df["Region"]))
        df = df.drop(columns=["RegionMap"])

    data_cols = []
    cols_order = ["Region", "RegionLabel", "Color", "ColorGroup", "Inset"]
    for column in df.columns:
        if column.startswith("Geographic Area"):
            cols_order.insert(5, column)

        elif column not in [
            "Region",
            "RegionLabel",
            "Color",
            "ColorGroup",
            "Inset",
        ] and not column.startswith("Geographic Area"):
            cols_order.append(column)
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

            if column in vis_types.get("cartogram", []):
                data_cols.append({"name": name, "column_name": column})

    df = df.reindex(columns=cols_order)

    # Just to make sure ColorGroup column exists. Color assignment should be done during geojson processing
    if "ColorGroup" not in df:
        df["ColorGroup"] = ""

    if is_empty_color:
        df.drop(columns="Color", inplace=True)

    if is_empty_inset:
        df.drop(columns="Inset", inplace=True)

    return df.to_csv(index=False), data_cols, map_names_dict


def postprocess_geojson(json_data, target_area=None, target_centroid=None):
    geometries = [
        shapely.geometry.shape(feature["geometry"]) for feature in json_data["features"]
    ]
    geoms_info = geojson_utils.get_geoms_info(geometries)

    # Scale and translate to match with the target area and centroid
    if target_area and target_centroid:
        scale_factor = math.sqrt(target_area / geoms_info["area"])
        origin_x = geoms_info["centroid"]["x"]
        origin_y = geoms_info["centroid"]["y"]
        diff_x = target_centroid["x"] - origin_x
        diff_y = target_centroid["y"] - origin_y

        for index, feature in enumerate(json_data["features"]):
            geometries[index] = shapely.affinity.scale(
                geometries[index],
                xfact=scale_factor,
                yfact=scale_factor,
                origin=(origin_x, origin_y),
            )
            geometries[index] = shapely.affinity.translate(
                geometries[index],
                xoff=diff_x,
                yoff=diff_y,
            )
            feature["geometry"] = shapely.geometry.mapping(geometries[index])

        if "dividers" in json_data:
            adjusted_dividers = shapely.affinity.scale(
                shapely.geometry.shape(json_data["dividers"]["geometry"]),
                xfact=scale_factor,
                yfact=scale_factor,
                origin=(origin_x, origin_y),
            )
            adjusted_dividers = shapely.affinity.translate(
                adjusted_dividers,
                xoff=diff_x,
                yoff=diff_y,
            )
            json_data["dividers"]["geometry"] = shapely.geometry.mapping(
                adjusted_dividers
            )

        geoms_info["bbox"][0] = (
            origin_x + (geoms_info["bbox"][0] - origin_x) * scale_factor
        ) + diff_x
        geoms_info["bbox"][1] = (
            origin_y + (geoms_info["bbox"][1] - origin_y) * scale_factor
        ) + diff_y
        geoms_info["bbox"][2] = (
            origin_x + (geoms_info["bbox"][2] - origin_x) * scale_factor
        ) + diff_x
        geoms_info["bbox"][3] = (
            origin_y + (geoms_info["bbox"][3] - origin_y) * scale_factor
        ) + diff_y

    # Get point to place the label
    for index, feature in enumerate(json_data["features"]):
        point = geometries[index].representative_point()
        feature["properties"]["label"] = {"x": point.x, "y": point.y}

    # Fix format of dividers
    if "dividers" in json_data:
        json_data["dividers"] = [json_data["dividers"]]

    # Make sure that json file have bbox
    json_data["bbox"] = geoms_info["bbox"]

    return json_data
