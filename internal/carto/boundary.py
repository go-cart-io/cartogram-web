import os

import mapclassify
from utils import format_utils

from .cpp_wrapper import call_binary
from .dataframe import CartoDataFrame
from .formatter import postprocess_geojson
from .storage import CartoStorage


def preprocess(input, mapDBKey="temp_filename"):
    """
    Core preprocessing function for boundary data that handles file loading,
    geometry validation, and data preparation for cartogram generation.

    Args:
        input: Input data (file path string or file object) containing boundary geometries
        mapDBKey: Unique identifier for the map data

    Returns:
        dict: Dictionary containing processed geojson data and list of unique columns
    """

    storage = CartoStorage(mapDBKey)

    # Input can be anything that is supported by geopandas.read_file
    # Standardize input to geojson file path for consistent processing
    file_path = storage.get_tmp_file_path("Input.json")
    storage.create_tmp()
    if isinstance(input, str):  # input is path
        input_path = input
    else:  # input is file object
        input_path = storage.get_tmp_file_path(input.filename)
        input.save(input_path)

    # Load the geographic data into a CartoDataFrame and save as cartogram file
    cdf = CartoDataFrame.read_file(input_path)
    cdf.to_carto_file(file_path)

    # Remove the original file if input is file object
    if not isinstance(input, str):
        os.remove(input_path)

    # Remove invalid geometries
    cdf = cdf[cdf.geometry.notnull()]
    cdf = cdf[cdf.geometry.type.isin(["Polygon", "MultiPolygon"])].reset_index(
        drop=True
    )

    # Process columns to identify unique identifier columns
    unique_columns = []
    for column in cdf.columns:
        if column == "geometry" or column == "label":
            continue
        cdf[column] = format_utils.convert_col_to_serializable(cdf[column])
        if cdf[column].is_unique:
            unique_columns.append(column)

    if not cdf.is_projected:
        # Temporary project it so we can calculate the area
        # NSIDC EASE-Grid 2.0 Global https://epsg.io/6933
        cdf.to_crs("EPSG:6933", inplace=True)
        color_method = "centroid"
    else:
        color_method = "count"

    tmp_cdf = cdf

    if not any(cdf.columns.str.startswith("Geographic Area")):
        cdf["Geographic Area (sq. km)"] = round(tmp_cdf.area / 10**6)
        cdf["Geographic Area (sq. km)"] = cdf["Geographic Area (sq. km)"].astype(int)

    if "ColorGroup" not in cdf.columns:
        cdf["ColorGroup"] = mapclassify.greedy(
            tmp_cdf, min_colors=6, balance=color_method
        )
        cdf["ColorGroup"] = cdf["ColorGroup"].astype(int)

    if "cartogram_id" not in cdf.columns:
        cdf["cartogram_id"] = range(1, len(cdf) + 1)

    if not cdf.is_projected:
        # Always convert to WGS84 (EPSG:4326) before input to cpp
        cdf.to_crs("EPSG:4326", inplace=True)
        geojson = cdf.to_carto_file(file_path)
        flags = ["--output_equal_area_map"]
        if cdf.is_world:
            flags += ["--world"]
        equal_area_json = call_binary(mapDBKey, file_path, None, flags)
        if equal_area_json is None:
            equal_area_json = geojson
        else:
            equal_area_json = postprocess_geojson(equal_area_json)
    else:
        geojson = cdf.to_carto_file(file_path)
        equal_area_json = postprocess_geojson(geojson)

    return {"geojson": equal_area_json, "unique": unique_columns}
