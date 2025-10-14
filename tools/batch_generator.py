# Script to regenerate cartograms in a folder or folders
# Also include utility script to update cartdata folder with sample_data

import argparse
import json
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "../internal"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../internal/executable"))

from carto import boundary, project
from carto.dataframe import CartoDataFrame
from handler_metadata import cartogram_handlers  # type: ignore

CARTDATA_PATH = os.path.join(os.path.dirname(__file__), "../internal/static/cartdata")
KEY_COL = 0
DATA_COL = 1

parser = argparse.ArgumentParser(
    description="Tools for adding maps and generating cartograms."
)
parser.add_argument(
    "--overwrite",
    action="store_true",
    help="replace existing data with current one (default: skip processing if data already exists)",
)
parser.add_argument(
    "--prompt_friendly_name",
    action="store_true",
    help="prompt for map friendly name (default: use the folder name)",
)
parser.add_argument(
    "--vis_types",
    help="the visualization configuration in the format { column_name: type }, "
    'e.g., { "Population": "contiguous", "Population2": "noncontiguous", "Population density": "choropleth" }. '
    "Leave it blank to make all data columns contiguous cartograms.",
)
subparsers = parser.add_subparsers(help="subcommand help")

parser_add_folders = subparsers.add_parser(
    "add_folders",
    help="copy subfolders from the based folder, generate cartograms for each subfolder, "
    "then add each of them to the map list. Must have one geojson and at least one csv in each subfolder. "
    "In each csv, the first column must be region names and the second column must be the data (e.g. population). "
    "Use 'Label' column for labels in visualization.",
)
parser_add_folders.add_argument(
    "based_folder", help="the based folder (e.g., cartogram-cpp/sample_data)"
)

parser_add_map = subparsers.add_parser(
    "add_map",
    help="copy the specified folder, generate cartograms for each subfolder, "
    "then add each of them to the map list. Must have one geojson and at least one csv in each subfolder. "
    "In each csv, the first column must be region names and the second column must be the data (e.g. population). "
    "Use 'Label' column for labels in visualization.",
)
parser_add_map.add_argument(
    "src_map_folder",
    help="the path to the specified folder (e.g., cartogram-cpp/sample_data/world_by_region_wo_antarctica)",
)

parser_gen_map = subparsers.add_parser(
    "gen_map",
    help="regenerate cartograms for the specified map in internal/static/cartdata folder "
    "(useful in case the map is already in the list but you want to update the cartogram only).",
)
parser_gen_map.add_argument(
    "map_folder",
    help="the name of a folder in cartdata (e.g., usa). "
    "Use 'all' to regenerate cartograms for all folders in cartdata.",
)


def read_csv_with_encoding(file_path: str) -> pd.DataFrame | None:
    """
    Try to read a CSV file using several common encodings.
    Returns a pandas DataFrame if successful, or None if all attempts fail.

    Args:
        file_path (str): Path to the csv file
    """
    encodings = ["utf-8", "utf-16", "latin-1", "iso-8859-1", "windows-1252"]

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error with {encoding}: {e}")
            continue

    # If all encodings fail, try with error handling
    try:
        df = pd.read_csv(file_path, encoding="utf-8", encoding_errors="replace")
        print("Read with UTF-8 encoding (replaced invalid characters)")
        return df
    except Exception as e:
        print(f"Failed to read file with any encoding: {e}")
        return None


def merge_csv_files(csv_files: list[Path], output_path: Path) -> None:
    """
    Merge multiple CSV files using the first column as the key (region names).
    Drops empty columns before merging. Handles label and inset columns if present.
    Saves the merged result to output_path.

    Args:
        csv_files (List[Path]): List of CSV file paths to merge
        output_path (Path): Path where merged CSV should be saved
    """
    if not csv_files:
        return

    try:
        # Read first CSV as base dataframe
        merged_df = read_csv_with_encoding(str(csv_files[0]))
        if merged_df is None:
            return

        # Select first two columns plus "Inset" and "ShapeName" if it exists
        selected_cols = list(merged_df.columns[:2])
        if "Inset" in merged_df.columns and not merged_df["Inset"].isna().all():
            selected_cols.append("Inset")
        if (
            merged_df.columns[0] != "ShapeName"
            and "ShapeName" in merged_df.columns
            and not merged_df["ShapeName"].isna().all()
        ):
            selected_cols.append("ShapeName")

        # Deal with labels
        if (
            "RegionLabel" in merged_df.columns
            and not merged_df["RegionLabel"].isna().all()
        ):
            selected_cols.append("RegionLabel")
        elif "Label" in merged_df.columns and not merged_df["Label"].isna().all():
            selected_cols.append("Label")

        merged_df = merged_df[selected_cols].copy()
        first_col = merged_df.columns[0]

        # Merge remaining CSVs
        if len(csv_files) > 1:
            for csv_file in csv_files[1:]:
                df = read_csv_with_encoding(str(csv_file))
                if df is None:
                    continue

                selected_cols = list(df.columns[:2])  # First two columns
                if "Inset" in df.columns and not df["Inset"].isna().all():
                    selected_cols.append("Inset")

                df = df[selected_cols].copy()
                # Drop if the data column with same values already exists
                if (
                    selected_cols[1] in merged_df.columns
                    and selected_cols[1] in df.columns
                    and df[selected_cols[1]].equals(merged_df[selected_cols[1]])
                ):
                    df = df.drop(selected_cols[1], axis=1)

                if df.columns[0] == first_col:
                    # Merge on first column
                    merged_df = pd.merge(
                        merged_df,
                        df,
                        on=first_col,
                        how="inner",
                        suffixes=("", f"_{csv_file.stem}"),
                    )

        # Save merged CSV
        merged_df.to_csv(output_path, index=False)

    except Exception as e:
        traceback.format_exc()
        print(f"Error merging CSV files: {e}")


def copy_folder(src_dir: Path, dest_dir: Path, overwrite=False) -> bool:
    """
    Copy geojson, markdown, and CSV files from src_dir to dest_dir.
    Merges CSVs and standardizes file names for cartogram processing.
    Returns True if successful, False otherwise.

    Args:
        src_dir (Path): Source directory
        dest_dir (Path): Destination directory
        overwrite (bool): Remove existing folder
    """
    print(f"Copy files from {src_dir} to cartdata...")

    if dest_dir.exists():
        if overwrite:
            try:
                shutil.rmtree(dest_dir)
            except Exception as e:
                print(f"Error deleting destination folder: {e}")
                return False
        else:
            print("Destination folder already exists. Skipping copy operation.")
            return False

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy geojson file
    geojson_files = list(src_dir.glob("*.geojson"))
    if not geojson_files:
        print("Warning: geojson file not found. Please check!")
        return False
    else:
        if len(geojson_files) > 1:
            print("Warning: found multiple geojson files. Please check!")

        source_file = geojson_files[0]
        dest_file = dest_dir / "Input.json"

        try:
            shutil.copy2(source_file, dest_file)
        except Exception as e:
            print(f"Failed to copy {geojson_files[0]}: {e}")
            return False

    # Copy all .md files
    md_files = list(src_dir.glob("*.md"))
    for source_file in md_files:
        dest_file = dest_dir / source_file.name

        try:
            shutil.copy2(source_file, dest_file)
        except Exception as e:
            print(f"Failed to copy {source_file}: {e}")

    # Identify and process CSV files
    csv_files = list(src_dir.glob("*.csv"))
    csv_path = dest_dir / "data.csv"
    merge_csv_files(csv_files, csv_path)

    return True


def add_folders(
    source_path: str,
    vis_types_str: str | None = None,
    prompt_friendly_name=False,
    overwrite=False,
) -> None:
    """
    Add all subfolders in the source_path as new maps.
    For each subfolder, copy files, merge CSVs, generate cartograms, and update handler metadata.

    Args:
        source_path (str): Source directory
        vis_types_str (str | None): Visualization configuration
        prompt_friendly_name (bool): Prompt for friendly name (otherwise, use the folder name)
        overwrite (bool): Remove existing folder
    """
    source = Path(source_path)

    # Copy and manage files in subdirectories
    for src_dir in source.iterdir():
        if not src_dir.is_dir():
            continue

        add_map(
            str(src_dir),
            vis_types_str=vis_types_str,
            prompt_friendly_name=prompt_friendly_name,
            overwrite=overwrite,
        )
        print("-" * 60)

    print("-" * 60)
    print("OPERATION COMPLETED!")
    print("-" * 60)


def add_map(
    source_path: str,
    vis_types_str: str | None = None,
    prompt_friendly_name=False,
    overwrite=False,
) -> None:
    """
    Add a single map from source_path.
    Copies files, merges CSVs, generates cartograms, and updates handler metadata.

    Args:
        source_path (str): Source directory
        vis_types_str (str | None): Visualization configuration
        prompt_friendly_name (bool): Prompt for friendly name (otherwise, use the folder name)
        overwrite (bool): Remove existing folder
    """
    print(f"Add {source_path}...")

    src_dir = Path(source_path)
    handler = src_dir.name

    destination = Path(CARTDATA_PATH)
    dest_dir = destination / handler

    if not overwrite and handler in cartogram_handlers:
        print("Skip: Handler already exists.")
        return

    user_friendly_name = handler
    if prompt_friendly_name:
        user_friendly_name = (
            input((f"Enter a user friendly name for this map ({handler}): ")) or handler
        )

    if not copy_folder(src_dir, dest_dir, overwrite=overwrite):
        return

    vis_types = gen_map(handler, vis_types_str)
    modify_handler(handler, user_friendly_name, vis_types, overwrite=overwrite)


def gen_map_wrapper(handler: str, vis_types_str: str | None = None) -> None:
    """
    Regenerate cartograms for a specific handler or for all handlers if 'all' is specified.

    Args:
        handler (str): The handler
        vis_types_str (str | None): Visualization configuration
    """
    if handler == "all":
        err = []
        for handler in cartogram_handlers:
            try:
                gen_map(handler, vis_types_str)
            except Exception as e:
                print(e)
                err = err + [handler]
        print("Done! Please check the following folder for errors:")
        print(err)
    else:
        gen_map(handler, vis_types_str)


def gen_map(handler_str: str, vis_types_str: str | None = None) -> dict[str, str]:
    """
    Generate cartogram data for a given handler (map folder).
    Preprocesses geojson, merges with CSV data, and runs the cartogram generation logic.
    Returns the visualization types used.

    Args:
        handler (str): The handler
        vis_types_str (str | None): Visualization configuration
    """
    print(f"Generate cartogram of {handler_str}...")

    handler = Path(f"{CARTDATA_PATH}/{handler_str}")
    json_input = handler / "Input.json"

    boundary.preprocess(str(json_input), "batch")

    # Move processed json to cartdata
    json_input.unlink()
    tmp_path = os.path.join(
        os.path.dirname(__file__), "../internal/tmp/batch/Input.json"
    )
    shutil.move(tmp_path, str(handler))

    # Prepare data
    data_df = read_csv_with_encoding(str(handler / "data.csv"))
    if data_df is None:
        return {}

    first_col = "Region"

    if "Region" not in data_df.columns:
        first_col = data_df.columns[0]
        data_df = data_df.rename(columns={first_col: "Region"})

    # If frindly region names exist, use them
    if "ShapeName" in data_df.columns:
        data_df = data_df.rename(columns={"Region": "RegionMap"})
        data_df = data_df.rename(columns={"ShapeName": "Region"})

    if "Label" in data_df.columns:
        data_df = data_df.rename(columns={"Label": "RegionLabel"})

    if isinstance(vis_types_str, str):
        vis_types = json.loads(vis_types_str)
    elif not vis_types_str:
        # Make all data columns contiguous cartograms
        reserved = [
            "Region",
            "RegionMap",
            "RegionLabel",
            "Color",
            "ColorGroup",
            "Inset",
            "Geographic Area (sq. km)",
        ]
        data_cols = [col for col in data_df.columns if col not in reserved]
        vis_types = {key: "contiguous" for key in data_cols}
    else:
        vis_types = {}

    input_cdf = CartoDataFrame.read_file(handler / "Input.json")
    if first_col == "Region":
        data_df = data_df.merge(
            input_cdf[["Region", "ColorGroup", "Geographic Area (sq. km)"]],
            on="Region",
            how="left",
        )
    elif "RegionMap" in data_df.columns:
        data_df = data_df.merge(
            input_cdf[[first_col, "ColorGroup", "Geographic Area (sq. km)"]],
            left_on="RegionMap",
            right_on=first_col,
            how="left",
        )
        data_df.drop(columns=[first_col], inplace=True)
    else:
        data_df = data_df.merge(
            input_cdf[[first_col, "ColorGroup", "Geographic Area (sq. km)"]],
            left_on="Region",
            right_on=first_col,
            how="left",
        )
        data_df.drop(columns=[first_col], inplace=True)

    flags = []
    if str(handler.name).lower().startswith("world"):
        flags = ["--world"]

    project.generate(
        data_df.to_csv(index=False),
        vis_types,
        str(json_input),
        "batch",
        str(handler),
        clean_by=first_col,
        flags=flags,
    )

    return vis_types


def modify_handler(
    map_name: str,
    user_friendly_name: str,
    vis_type: dict[str, str] = {},
    overwrite=False,
) -> bool:
    """
    Update the handler metadata file to add or update a map handler entry.
    Optionally formats the file using Ruff if available.
    Returns True if successful, False otherwise.
    """
    file_path = "internal/handler_metadata.py"
    try:
        print("Updating handler metadata...")
        # Execute the metadata file to get the dictionary
        with open(file_path, "r") as f:
            exec(f.read(), globals())

        # Add new handler
        if map_name not in cartogram_handlers or overwrite:
            cartogram_handlers[map_name] = {"name": user_friendly_name}
            if vis_type:
                cartogram_handlers[map_name]["types"] = vis_type  # type: ignore
        else:
            print("The handler exists. Use argument ")
            return False

        # Write back to file and format it
        try:
            import ast

            # Create an AST node for the assignment
            assignment_code = f"cartogram_handlers = {repr(cartogram_handlers)}"
            assignment = ast.parse(assignment_code).body[0]

            # Convert back to source code
            if hasattr(ast, "unparse"):  # Python 3.9+
                code = ast.unparse(assignment)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code + "\n")

        except Exception as e:
            print(f"AST unparse method failed: {e}")

        try:
            subprocess.run(
                ["ruff", "check", "--fix", str(file_path)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["ruff", "format", str(file_path)],
                check=True,
                capture_output=True,
                text=True,
            )

        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Cannot format the output. Ruff not found in PATH.")

        print("Done.")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


parser_add_folders.set_defaults(
    func=lambda args: add_folders(
        args.based_folder,
        prompt_friendly_name=args.prompt_friendly_name,
        overwrite=args.overwrite,
    )
)
parser_add_map.set_defaults(
    func=lambda args: add_map(
        args.src_map_folder,
        vis_types_str=args.vis_types,
        prompt_friendly_name=args.prompt_friendly_name,
        overwrite=args.overwrite,
    )
)
parser_gen_map.set_defaults(
    func=lambda args: gen_map_wrapper(args.map_folder, vis_types_str=args.vis_types)
)

args = parser.parse_args()

if hasattr(args, "func"):
    args.func(args)
else:
    parser.print_help()
