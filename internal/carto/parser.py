"""
Project Data Parser Module

This module provides functions to parse and validate project data from user input.
It handles the extraction and validation of project components including handlers, keys,
visualization types, and CSV data, with appropriate error handling and data cleaning.
"""

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
    vis_types = parse_vis_types(data)
    datacsv = data["csv"] if "csv" in data else format_utils.get_csv(data)

    df = pd.read_csv(StringIO(datacsv))
    cleaned_vis_types = format_utils.clean_map_types(vis_types, df.columns)

    # If regions are edited, handler should be custom
    edit_from = data.get("editedFrom", None)
    if (
        handler_name != "custom"
        and "RegionMap" in df.columns
        and not df["RegionMap"].equals(df["Region"])
    ):
        edit_from = handlers.get_gen_file(handler_name)
        handler_name = "custom"

    return handler_name, string_key, cleaned_vis_types, datacsv, edit_from


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


def parse_vis_types(data: dict) -> dict:
    """
    Parse and validate visualization type specifications from project data.

    Visualization types define how different data columns should be displayed
    (e.g., as cartograms, choropleth maps, etc.). This function validates
    the JSON structure and enforces limits on cartogram count.

    Args:
        data (dict): Project data containing visTypes as JSON string

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

    for key in vis_types:
        for header in vis_types[key]:
            file_utils.validate_filename(header)

        if (
            "cartogram" in vis_types
            and settings.CARTOGRAM_COUNT_LIMIT
            and len(vis_types["cartogram"]) >= settings.CARTOGRAM_COUNT_LIMIT
        ):
            raise CartoError(
                f"Limit of {settings.CARTOGRAM_COUNT_LIMIT} cartograms per data set."
            )

    return vis_types
