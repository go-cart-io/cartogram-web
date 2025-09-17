import json
from io import StringIO

import handlers
import pandas as pd
import settings
from errors import CartoError
from models import CartogramEntry
from utils import file_utils, format_utils


def parse_project(data: dict) -> tuple[str, str, dict, str, str | None]:
    """
    Parse and validate a complete project data from input data.

    This is the main parsing function that extracts all necessary components
    for creating a project, including data validation and cleaning.

    Args:
        data (dict): Raw project data containing user inputs such as handler, key,
                    visualization types, and CSV data or reference

    Returns:
        tuple: A 5-tuple containing:
            - handler_name (str): Name of the data handler to use
            - string_key (str): Sanitized unique project identifier
            - cleaned_vis_types (dict): Validated visualization type mappings
            - datacsv (str): CSV data as string
            - edit_from (str): Original input path if data was edited from another project

    Raises:
        CartoError: If any validation fails during parsing
    """
    handler_name = parse_handler(data)
    string_key = parse_key(data)

    datacsv = data["csv"] if "csv" in data else format_utils.get_csv(data)
    df = pd.read_csv(StringIO(datacsv))
    vis_types = parse_vis_types(data, df)

    # If regions are edited, handler should be custom
    edit_from = data.get("editedFrom", None)
    if (
        handler_name != "custom"
        and "RegionMap" in df.columns
        and not df["RegionMap"].equals(df["Region"])
    ):
        edit_from = handlers.get_gen_file(handler_name)
        handler_name = "custom"

    return handler_name, string_key, vis_types, datacsv, edit_from


def parse_handler(data: dict) -> str:
    """
    Extract and validate the data handler name from project data.

    This function ensures the specified handler exists in the system.

    Args:
        data (dict): Project data containing handler specification

    Returns:
        str: Validated handler name

    Raises:
        CartoError: If handler name is invalid or doesn't exist (except "custom")
    """
    handler_name = data.get("handler", "")
    if not handlers.has_handler(handler_name) and handler_name != "custom":
        raise CartoError("Invalid map.", log=False)

    return handler_name


def parse_key(data: dict, required=True, must_unique=True) -> str:
    """
    Extract and validate the project database key from input data.

    The key serves as a unique identifier for storing and sharing cartogram projects.
    It undergoes sanitization and uniqueness validation.

    Args:
        data (dict): Project data containing the mapDBKey
        required (bool, optional): Whether the key is required. Defaults to True.
        must_unique (bool, optional): Whether to enforce uniqueness in database.
                                    Defaults to True.

    Returns:
        str: Sanitized and validated project key

    Raises:
        CartoError: If key is missing when required, or if key already exists
                   in database when uniqueness is enforced
    """
    string_key = data.get("mapDBKey")
    if required and not string_key:
        raise CartoError("Missing sharing key.", log=False)

    string_key = file_utils.sanitize_filename(string_key)

    if must_unique and settings.USE_DATABASE:
        cartogram_entry = CartogramEntry.query.filter_by(string_key=string_key).first()

        if cartogram_entry is not None:
            raise CartoError("Duplicated database key.", suggest_refresh=True)

    return string_key


def parse_vis_types(data: dict, df: pd.DataFrame) -> dict[str, str]:
    """
    Parse and validate visualization type specifications from project data.

    Visualization types define how different data columns should be displayed
    (e.g., as cartograms, choropleth maps, etc.). This function validates
    the JSON structure and enforces limits on cartogram count.

    Args:
        data (dict): Project data containing visTypes as JSON string
        df (pd.DataFrame): Dataframe of csv

    Returns:
        dict: Parsed visualization types mapping columns to visualization methods

    Raises:
        CartoError: If JSON is malformed, filenames are invalid, or cartogram
                   limit is exceeded
    """
    try:
        vis_types = json.loads(data.get("visTypes", ""))
    except Exception:
        raise CartoError("Invalid visualization specification.")

    count = 0
    for col_name, col_type in vis_types.items():
        file_utils.validate_filename(col_name)

        if col_type == "cartogram":
            count = count + 1

        if settings.CARTOGRAM_COUNT_LIMIT and count > settings.CARTOGRAM_COUNT_LIMIT:
            raise CartoError(
                f"Limit of {settings.CARTOGRAM_COUNT_LIMIT} cartograms per data set."
            )

        if col_name not in df.columns:
            raise CartoError(
                f"{col_name} does not exist in the data", suggest_refresh=True
            )

    return vis_types


def parse_storage(data_path: str, types_str: str):
    """
    Parse storage data to create visualization configurations for the frontend viewer.

    Args:
        data_path (str): Path to the CSV data file
        types_str (str): JSON string containing visualization type mappings for each column

    Returns:
        tuple: (carto_versions, choro_versions, carto_equal_area_bg)
            - carto_versions (dict): List of columns and infomation for cartograms
            - choro_versions (list): List of columns for choropleth maps
            - carto_equal_area_bg (bool): Whether to use equal area background for cartographic display
    """
    # Parse the JSON string to get visualization types for each column
    vis_types = json.loads(types_str)

    # Load the CSV data using a safe path utility
    df = pd.read_csv(file_utils.get_safepath(data_path))

    # Initialize flag for equal area background (used for noncontiguous visualizations)
    carto_equal_area_bg = False

    # Initialize cartogram versions dictionary with geographic area entry
    carto_versions = {}
    carto_versions["0"] = {
        "key": "0",
        "header": "Geographic Area (sq. km)",
        "name": "Geographic Area",
        "unit": "sq. km",
    }

    # Offset counter for cartogram versions (starts at 1 since "0" is reserved)
    offset = 1

    # Initialize list to store columns suitable for choropleth mapping
    choro_versions = []

    # Iterate through all columns in the dataframe
    for col in df.columns:
        # Skip columns that are metadata or have no visualization type assigned
        if (
            col
            in [
                "Region",
                "RegionLabel",
                "Color",
                "ColorGroup",
                "Inset",
            ]
            or col.startswith("Geographic Area")  # Skip geographic area columns
            or vis_types.get(col, "none") == "none"  # Skip columns with no vis type
        ):
            continue

        # If column is designated for choropleth visualization, add to choropleth list
        if vis_types[col] == "choropleth":
            choro_versions.append(col)
        else:
            # Create cartographic version entry with metadata
            info = format_utils.label_to_name_unit(col)

            carto_versions[str(offset)] = {
                "key": str(offset),
                "header": info["header"],
                "name": info["name"],
                "unit": info["unit"],
                "type": vis_types[col],
            }

        # Set equal area background flag if any column uses noncontiguous visualization
        carto_equal_area_bg = (
            True if vis_types[col] == "noncontiguous" else carto_equal_area_bg
        )

        # Increment offset for next cartogram version key
        offset = offset + 1

    return carto_versions, choro_versions, carto_equal_area_bg
