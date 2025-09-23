# Script to regenerate cartograms in a folder or folders
# Also include utility script to update cartdata folder with sample_data

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
from handler_metadata import cartogram_handlers

CARTDATA_PATH = os.path.join(os.path.dirname(__file__), "../internal/static/cartdata")
KEY_COL = 0
DATA_COL = 1


def print_usage():
    usage = """Usage: python batch_generator.py <command> [options]

Commands:
  add        Add a new map in our handler.
  gen        Generate cartograms for the specified handler.
  gen-all    Generate cartograms for all maps in our handler.

Examples:
  batch_generator.py add handler-name [Input.json] [data.csv]
  batch_generator.py gen handler-name
  batch_generator.py gen-all
"""
    print(usage)


def read_csv_with_encoding(file_path):
    """Try to read CSV with different encodings"""
    encodings = [
        "utf-8",
        "utf-8-sig",
        "latin-1",
        "iso-8859-1",
        "windows-1252",
        "cp1252",
    ]

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


def merge_csv_files(csv_files: list[Path], output_path: Path) -> list[str]:
    """
    Merge multiple CSV files using the first column as key.
    Drops empty columns before merging.

    Assumption:
        The first column contains region names. The second columns contains data.

    Args:
        csv_files (List[Path]): List of CSV file paths to merge
        output_path (Path): Path where merged CSV should be saved

    Returns:
        list[str]: List of data column names
    """
    if not csv_files:
        return []

    try:
        data_cols = []

        # Read first CSV as base dataframe
        merged_df = read_csv_with_encoding(csv_files[0])
        if merged_df is None:
            return []

        # Select first two columns plus "Inset" if it exists
        selected_cols = list(merged_df.columns[:2])
        if "Inset" in merged_df.columns and not merged_df["Inset"].isna().all():
            selected_cols.append("Inset")

        merged_df = merged_df[selected_cols].copy()
        first_col = merged_df.columns[0]

        # Merge remaining CSVs
        if len(csv_files) > 1:
            for csv_file in csv_files[1:]:
                df = read_csv_with_encoding(csv_file)
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

        # Find data columns
        priority = [first_col, "Inset", "Population (people)"]
        priority = [col for col in priority if col in merged_df.columns]
        data_cols = [col for col in merged_df.columns if col not in priority]
        merged_df = merged_df[priority + data_cols]
        data_cols = ["Population (people)"] + data_cols

        print(f"CSV columns: {merged_df.columns}")
        print(f"Data columns: {data_cols}")

        return data_cols

    except Exception as e:
        traceback.format_exc()
        print(f"Error merging CSV files: {e}")
        return []


def process_folders(source_path, override=True):
    """
    Copy directory structure and all .md files from source to destination.
    Also merge CSV files in each subdirectory.

    Args:
        source_path (str): Path to the source folder
        override (bool): If True, delete existing destination folder before copying
    """
    source = Path(source_path)
    destination = Path(CARTDATA_PATH)

    # Check if source exists
    if not source.exists() or not source.is_dir():
        print(
            f"Error: Source path '{source_path}' does not exist or is not a directory."
        )
        return

    print(f"Copying from: {source}")
    print(f"Copying to: {destination}")
    print(f"Override mode: {override}")
    print("-" * 60)

    # Walk through all directories and subdirectories
    for src_dir in source.iterdir():
        if not src_dir.is_dir():
            continue

        # Create corresponding directory structure in destination
        dest_dir = destination / src_dir.name

        print(dest_dir)

        if dest_dir.exists():
            if override:
                try:
                    shutil.rmtree(dest_dir)
                    print("Existing destination folder cleared.")
                except Exception as e:
                    print(f"Error deleting destination folder: {e}")
                    continue
            else:
                print("Destination folder already exists. Skipping copy operation.")
                continue

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy geojson file
        geojson_files = list(src_dir.glob("*.geojson"))
        if not geojson_files:
            print("Warning: geojson file not found. Please check!")
            continue
        else:
            if len(geojson_files) > 1:
                print("Warning: found multiple geojson files. Please check!")

            source_file = geojson_files[0]
            dest_file = dest_dir / "Input.json"

            try:
                shutil.copy2(source_file, dest_file)
            except Exception as e:
                print(f"Failed to copy {geojson_files[0]}: {e}")
                continue

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
        data_cols = merge_csv_files(csv_files, csv_path)
        vis_types = {key: "contiguous" for key in data_cols}

        # Start processing
        add_handler(src_dir.name, vis_types, skip_prompt=True, override=override)
        print("-" * 60)

        break

    print("-" * 60)
    print("OPERATION COMPLETED!")
    print("-" * 60)


def add_handler(handler, vis_types={}, skip_prompt=False, override=True):
    if not override and handler in cartogram_handlers:
        print("Error: Handler already exists.")
        return

    user_friendly_name = handler
    if not skip_prompt:
        user_friendly_name = (
            input((f"Enter a user friendly name for this map ({handler}): ")) or handler
        )

    gen_cartograms(handler, vis_types)
    modify_handler(handler, user_friendly_name, vis_types, override=override)


def gen_cartograms(handler, vis_types={}):
    print(f"Generate cartogram of {handler}...")

    handler = Path(f"{CARTDATA_PATH}/{handler}")
    json_input = handler / "Input.json"

    boundary.preprocess(str(json_input), "batch")

    # Move processed json to cartdata
    json_input.unlink()
    tmp_path = os.path.join(
        os.path.dirname(__file__), "../internal/tmp/batch/Input.json"
    )
    shutil.move(tmp_path, str(handler))

    # Prepare data
    data_df = pd.read_csv(handler / "data.csv")
    region_col = data_df.columns[0]
    data_df = data_df.rename(columns={region_col: "Region"})
    input_cdf = CartoDataFrame.read_file(handler / "Input.json")
    data_df["ColorGroup"] = input_cdf["ColorGroup"]
    data_df["Geographic Area (sq. km)"] = input_cdf["Geographic Area (sq. km)"]

    project.generate(
        data_df.to_csv(index=False),
        vis_types,
        str(json_input),
        "batch",
        str(handler),
        clean_by=region_col,
    )

    print("Done.")


def modify_handler(map_name, user_friendly_name, vis_type={}, override=True):
    file_path = "internal/handler_metadata.py"
    try:
        print("Updating handler metadata...")
        # Execute the metadata file to get the dictionary
        with open(file_path, "r") as f:
            exec(f.read(), globals())

        # Now cartogram_handlers is available in global scope
        # Add new handler
        if map_name not in cartogram_handlers or override:
            cartogram_handlers[map_name] = {"name": user_friendly_name}
            if vis_type:
                cartogram_handlers[map_name]["types"] = vis_type

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


if len(sys.argv) < 2:
    print_usage()
    sys.exit(1)

if sys.argv[1] == "process":
    process_folders(sys.argv[2])
elif sys.argv[1] == "add":
    add_handler(sys.argv[2])
elif sys.argv[1] == "gen":
    gen_cartograms(sys.argv[2])
elif sys.argv[1] == "gen-all":
    err = []
    for handler in cartogram_handlers:
        try:
            gen_cartograms(handler)
        except Exception as e:
            print(e)
            err = err + [handler]
    print("Done! Please check the following folder for errors:")
    print(err)
else:
    print_usage()
    sys.exit(1)
