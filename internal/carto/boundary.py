import os

import numpy as np
from carto.dataframe import CartoDataFrame
from carto.datajson import CartoJson
from carto.generators.cpp_wrapper import run_binary
from carto.mapcolor import assign_colors
from carto.storage import CartoStorage
from errors import CartoError
from utils import file_utils, format_utils


def preprocess(input, mapDBKey="temp_filename"):
    """
    Core preprocessing function for boundary data that handles file loading,
    geometry validation, and data preparation for creating equal area map.

    Args:
        input: Input data (file path string or file object) containing boundary geometries
        mapDBKey: Unique identifier for the map data

    Returns:
        dict: Dictionary containing processed geojson data (equal area) and list of unique columns
    """

    storage = CartoStorage(mapDBKey)

    # Input can be anything that is supported by geopandas.read_file
    # Standardize input to geojson file path for consistent processing
    file_path = storage.get_safe_tmp_file_path("Input.json")
    storage.create_tmp()
    if isinstance(input, str):  # input is path
        input_path = input
        input_path = file_utils.get_safepath(input_path)
    else:  # input is file object
        input_path = storage.get_safe_tmp_file_path(input.filename)
        input.save(input_path)

    # Load the geographic data into a CartoDataFrame
    cdf = CartoDataFrame.read_file(input_path)

    # Remove the original file if input is file object
    if not isinstance(input, str):
        if input_path.startswith(storage.tmp_path):
            os.remove(input_path)
        else:
            raise CartoError("Attempted to remove file outside allowed temp directory")

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

    tmp_cdf = cdf

    # Fill in attributes
    if not any(cdf.columns.str.startswith("Geographic Area")):
        cdf["Geographic Area (sq. km)"] = tmp_cdf.area / 10**6
        cdf["Geographic Area (sq. km)"] = cdf["Geographic Area (sq. km)"].astype(float)

    if "ColorGroup" not in cdf.columns:
        cdf["ColorGroup"] = assign_colors(tmp_cdf)

    if "cartogram_id" not in cdf.columns:
        cdf["cartogram_id"] = range(1, len(cdf) + 1)

    # Convert to WGS84 (EPSG:4326) before input to cpp
    if not cdf.is_projected:
        cdf.to_crs("EPSG:4326", inplace=True)
        cdf = determine_world(cdf)

    equal_area_json = generate_equal_area(cdf, file_path, None)

    return {"geojson": equal_area_json.json_data, "unique": unique_columns}


def determine_world(cdf: CartoDataFrame) -> CartoDataFrame:
    """
    Guess if the map is world map.

    Args:
        cdf: CartogramDataFrame containing the geographic data and metadata
    """
    # Don't guess if the data frame is not in lat-long format
    if cdf.is_projected:
        return cdf

    # Don't guess if explicit world attribute is detected
    if cdf.is_world:
        return cdf

    # Get bounding box after potential +360° fix for western polygons
    adjusted_bbox = get_adjusted_bbox(cdf)

    # Add world attribute
    long_diff = adjusted_bbox[2] - adjusted_bbox[0]
    if long_diff > 180:
        cdf.extra_attributes["extent"] = "world"
        cdf.is_world = True

    return cdf


def get_adjusted_bbox(cdf: CartoDataFrame):
    """
    Calculate the bounding box after adjusting for dual hemisphere layout.
    If geometries span both hemispheres with sufficient gap, western hemisphere
    bounds are translated by +360 degrees before computing the final bbox.

    Parameters:
    -----------
    cdf : CartoDataFrame
        CartoDataFrame with geometries in geographic coordinates (longitude/latitude)

    Returns:
    --------
    tuple
        (minx, miny, maxx, maxy) of adjusted bounding box
    """
    # Get all bounds of each polygons at once
    cdf_exploded = cdf.explode(index_parts=True, ignore_index=True)
    bounds = cdf_exploded.bounds

    # Find hemisphere bounds
    # max_lon_west = xmax < 0 ? std::max(xmax, max_lon_west) : max_lon_west;
    west_mask = bounds["maxx"] < 0
    east_mask = bounds["minx"] >= 0
    max_lon_west = bounds.loc[west_mask, "maxx"].max() if west_mask.any() else -np.inf
    min_lon_east = bounds.loc[east_mask, "minx"].min() if east_mask.any() else np.inf

    # Check if adjustment is needed
    if (
        max_lon_west >= -180.0
        and min_lon_east <= 180.0
        and min_lon_east - max_lon_west >= 180
    ):
        # Adjust western hemisphere bounds by +360
        adjusted_bounds = bounds.copy()
        west_geom_mask = bounds["minx"] < 0
        adjusted_bounds.loc[west_geom_mask, ["minx", "maxx"]] += 360

        # Calculate final bounding box
        return (
            adjusted_bounds["minx"].min(),
            adjusted_bounds["miny"].min(),
            adjusted_bounds["maxx"].max(),
            adjusted_bounds["maxy"].max(),
        )

    # No adjustment needed, return original total bounds
    return cdf.total_bounds


def generate_equal_area(
    cdf: CartoDataFrame,
    input_path: str,
    data_path: str | None = None,
    flags: list[str] = [],
) -> CartoJson:
    """
    Generate an equal area projection of geographic data for cartogram creation.

    This function takes geographic data and converts it to an equal area projection,
    which is essential for creating accurate cartograms where area distortions need
    to be minimized. The function handles different scenarios based on whether the
    data is already projected and whether additional data is provided.

    Args:
        cdf: CartogramDataFrame containing the geographic data and metadata
        input_path: Path to the input geographic data file
        data_path: Optional path to additional data file for inset calculations
        equal_area_path: Optional output path to save the equal area projection
        flags: List of command-line flags to pass to the binary

    Returns:
        CartoJson: Object containing the equal area projected geographic data
    """

    # Save the cartogram data frame to a GeoJSON file
    geojson = cdf.to_carto_file(input_path)
    is_projected = cdf.is_projected

    if cdf.is_world:
        flags = flags + ["--world"]

    # Determine appropriate flags based on projection status and data availability
    # Case 0: No additional data and already projected - simply use the input
    # Case 1: No additional data and not already projected - generate equal area map
    if not data_path and not is_projected:
        flags = flags + ["--output_equal_area_map"]

    # Case 2: Has data and already projected - output shifted insets, skip projection
    if data_path and is_projected:
        flags = flags + [
            "--output_shifted_insets",
            "--skip_projection",
            "--area",
            "Geographic Area (sq. km)",
        ]
    # Case 3: Has data but not projected - generate equal area map with insets
    elif data_path:
        flags = flags + [
            "--output_equal_area_map",
            "--area",
            "Geographic Area (sq. km)",
        ]

    # Run the projection binary if data needs processing (case 1-3)
    equal_area_json = None
    if not cdf.is_projected or data_path:
        equal_area_json = run_binary(input_path, data_path, "Geographic Area", flags)

    # Handle projection failure by falling back to original data
    if equal_area_json is None:
        equal_area_json = geojson
        # TODO: warn the user about projection failure

    # Apply post-processing
    equal_area_json = CartoJson(equal_area_json, cdf.is_world)
    equal_area_json.postprocess()

    return equal_area_json
