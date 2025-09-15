import csv
import re
from io import StringIO

import pandas as pd
from errors import CartoError
from utils import file_utils


class CartoCsv:
    """
    A class for holding and processing CSV data.

    This class handles the complete pipeline of reading CSV data, cleaning region names,
    formatting data columns, and preparing the data for mapping visualization.
    """

    #: Processed CSV data
    df: pd.DataFrame

    def __init__(self, csv_string: str, vis_types: dict):
        """
        Initialize the class with csv data and visualization type configurations.

        Args:
            csv_string: Raw CSV data as a string
            vis_types: Dictionary containing visualization type configurations
        """
        #: Visualization type configurations
        self.vis_types = vis_types
        #: Mapping dictionary if region names are modified as { new_name: old:name }
        self.map_regions_dict = {}
        #: Data columns
        self.data_cols = []
        #: Mapping of data columns and data names (i.e., data columns without unit)
        self.data_names = {"Geographic Area": "Geographic Area"}

        # Read csv to Dataframe
        self.df = self._read_data(csv_string)

        # Clean and standardize region names, get mapping dictionary if region names are modified
        self._format_regions()

        # Remove Color and Inset columns if they are completely empty
        self._drop_empty_color_inset()

        # Reorganize columns in logical order and identify data columns
        self._reorder_columns()

        # Process each data column and extract display names
        self._format_data_columns()

    def _read_data(self, csv_string: str) -> pd.DataFrame:
        """
        Read CSV string data into a pandas DataFrame while preserving empty strings.

        Uses Python's csv module instead of pandas.read_csv() to maintain
        empty string values rather than converting them to NaN.

        Args:
            csv_string: CSV data as a string

        Returns:
            pd.DataFrame: Parsed CSV data
        """
        # Read with Python's csv module to preserve empty strings
        rows = []
        csv_reader = csv.DictReader(StringIO(csv_string))
        for row in csv_reader:
            rows.append(row)

        return pd.DataFrame(rows, dtype=str)

    def _format_regions(self) -> None:
        """
        Clean and standardize region names in the DataFrame.

        Performs the following operations:
        - Converts region names to strings
        - Replaces invalid characters (backslashes and quotes) with underscores
        - Removes rows with empty/whitespace-only region names
        - Creates a mapping dictionary if RegionMap column exists
        """
        self.map_regions_dict = {}

        # Replace empty strings with NA, then drop rows with NA in the 'Region' column
        initial_nrows = len(self.df)
        self.df["Region"] = self.df["Region"].replace(r"^\s*$", pd.NA, regex=True)
        self.df = self.df.dropna(subset=["Region"])

        # Replace invalid characters (\ ")
        self.df["Region"] = self.df["Region"].replace(r'\\|"', "_", regex=True)

        # Create name mapping dictionary if RegionMap column exists and there are changes
        if "RegionMap" in self.df.columns:
            self.df["RegionMap"] = self.df["RegionMap"].replace(
                r"^\s*$", pd.NA, regex=True
            )
            self.df["RegionMap"] = self.df["RegionMap"].fillna(self.df["Region"])
            self.df["RegionMap"] = self.df["RegionMap"].replace(
                r'\\|"', "_", regex=True
            )

            # Only create mapping if there are actual differences or rows were dropped
            if not self.df["RegionMap"].equals(
                self.df["Region"]
            ) or initial_nrows != len(self.df):
                # Use old name if new name is empty
                self.map_regions_dict = dict(
                    zip(self.df["RegionMap"], self.df["Region"])
                )
            self.df = self.df.drop(columns=["RegionMap"])

    def _drop_empty_color_inset(self) -> None:
        """
        Remove Color and Inset columns if they contain only NaN values.

        This cleanup step removes columns that would not contribute
        any useful information to the visualization.
        """
        for col in ["Color", "Inset"]:
            if col in self.df.columns:
                self.df[col] = self.df[col].replace(r"^\s*$", pd.NA, regex=True)
                if self.df[col].isna().all():
                    self.df = self.df.drop(columns=[col])

    def _reorder_columns(self) -> None:
        """
        Reorganize DataFrame columns in a logical order for processing.

        Column order priority:
        1. Core columns: Region, RegionLabel, Color, ColorGroup, Inset
        2. Geographic Area columns
        3. All remaining columns (considered data columns)

        Also ensures ColorGroup column exists (creates empty if missing).
        """
        # Ensure ColorGroup column exists (color assignment happens during geojson processing)
        self.df["ColorGroup"] = self.df["ColorGroup"] if "ColorGroup" in self.df else ""

        # Priority columns (may not all exist in df)
        priority = ["Region", "RegionLabel", "Color", "ColorGroup", "Inset"]

        # Keep only priority columns that actually exist in the DataFrame
        priority = [col for col in priority if col in self.df.columns]

        # Find columns starting with "Geographic Area"
        geo_cols = [col for col in self.df.columns if col.startswith("Geographic Area")]

        # Remaining columns are considered data columns (not in priority or geo)
        remaining = [col for col in self.df.columns if col not in priority + geo_cols]

        # Reorder: priority columns, then geographic columns, then data columns
        new_order = priority + geo_cols + remaining
        self.df = self.df[new_order]

        self.data_cols = remaining

    def _format_data_columns(self) -> None:
        """
        Process and validate all data columns.

        For each data column, performs validation and extracts display names.
        Updates the instance's data_names dictionary.
        """
        self.data_names = {"Geographic Area": "Geographic Area"}
        for column in self.data_cols:
            name = self._format_single_data_column(column)
            self.data_names[column] = name

    def _format_single_data_column(self, column: str) -> str:
        """
        Process and validate a single data column.

        Performs the following operations:
        - Validates the column name as a valid filename
        - Extracts display name from column header (removes units in parentheses)
        - Converts values to numeric, replacing invalid values with NaN
        - Validates that column is not completely empty
        - For cartogram visualizations, ensures sum is not zero

        Args:
            column: Name of the column to process

        Returns:
            str: Cleaned column name for display purposes

        Raises:
            CartoError: If column name is empty, all values are empty,
                       or sum is zero for cartogram columns
        """
        # Validate that column name can be used as a filename
        file_utils.validate_filename(column)

        # Extract display name from column header (remove units in parentheses)
        m = re.match(r"(.+)\s?\((.+)\)$", column)
        if m:
            name = m.group(1).strip()  # Use part before parentheses as display name
        else:
            name = column.strip()  # Use full column name if no parentheses found

        # Convert column values to numeric, replacing non-numeric values with NaN
        self.df[column] = pd.to_numeric(self.df[column], errors="coerce")

        # Validate that column has a non-empty name
        if name == "":
            raise CartoError(
                "Missing data name. Please ensure each data column has a name in its header."
            )

        # Validate that column contains some numeric data
        if self.df[column].isna().all():
            raise CartoError(
                f"Cannot process {column}: All rows are empty. Please enter some numeric values or remove the column."
            )

        # Special validation for cartogram visualizations: sum cannot be zero
        if column in self.vis_types["cartogram"]:
            column_sum = self.df[column].sum()
            if column_sum == 0:
                raise CartoError(
                    f"Cannot process {column}: Sum is zero. Please ensure the sum of data is not zero."
                )

        return name

    def save(self, project_path: str, filename: str) -> str:
        """
        Save the processed DataFrame to a CSV file.

        Args:
            project_path: Folder path where the CSV should be saved
            filename: File name of the CSV

        Returns:
            str: File path where the CSV is saved
        """
        area_data_path = file_utils.get_safepath(project_path, filename)
        with open(area_data_path, "w") as outfile:
            outfile.write(self.df.to_csv(index=False))

        return area_data_path
