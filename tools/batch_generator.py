# Script to regenerate cartograms in a folder or folders
# Also include utility script to update cartdata folder with sample_data

import sys
import os
import shutil
import uuid
import pandas
import geopandas

sys.path.append(os.path.join(os.path.dirname(__file__), "../internal"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../internal/executable"))

from handler_metadata import cartogram_handlers
from carto_dataframe import CartoDataFrame
import cartogram

CARTDATA_PATH = "../internal/static/cartdata"
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


def add_handler(handler, original_json_input="Input.json", original_csv="data.csv"):
    if handler in cartogram_handlers:
        print("Error: Handler already exists.")
        return

    cartdata_handler_path = f"{CARTDATA_PATH}/{handler}"
    cartdata_csv_path = f"{cartdata_handler_path}/data.csv"
    cartdata_json_input_path = f"{cartdata_handler_path}/Input.json"
    original_csv_path = f"{cartdata_handler_path}/{original_csv}"
    original_json_input_path = f"{cartdata_handler_path}/{original_json_input}"

    user_friendly_name = (
        input((f"Enter a user friendly name for this map ({handler}): ")) or handler
    )

    data_df = pandas.read_csv(original_csv_path)
    region_col = data_df.columns[0]
    data_df = data_df.rename(columns={region_col: "Region"})
    data_df.to_csv(cartdata_csv_path, index=False)

    cartogram.preprocess(original_json_input_path, "Input", cartdata_handler_path)
    update_area_in_csv(cartdata_csv_path, cartdata_json_input_path, region_col)
    gen_cartograms(handler, clean_by=region_col)

    gdf = geopandas.read_file(cartdata_json_input_path)
    regions = dict(zip(gdf["Region"], gdf["cartogram_id"]))
    modify_handler(handler, user_friendly_name, regions)


def gen_cartograms(handler, clean_by="Region"):
    print(f"Generate cartogram of {handler}....")
    cartdata_csv_path = f"{CARTDATA_PATH}/{handler}/data.csv"
    with open(cartdata_csv_path, "r") as file:
        datacsv = file.read()
    cartogram.generate_cartogram(
        datacsv,
        f"{CARTDATA_PATH}/{handler}/Input.json",
        str(uuid.uuid4()),
        f"{CARTDATA_PATH}/{handler}",
        clean_by=clean_by,
        print_progress=True,
    )
    print("*******************************************")


def update_area_in_csv(csv_file, geo_file, region_col):
    gdf = CartoDataFrame.read_file(geo_file)
    data_df = pandas.read_csv(csv_file)
    merged_df = data_df.merge(
        gdf[[region_col, "ColorGroup", "Geographic Area (sq. km)"]],
        right_on=region_col,
        left_on="Region",
        suffixes=["", "_gdf"],
    )

    if not gdf.is_projected:
        if "Geographic Area (sq. km)_gdf" in merged_df.columns:
            data_df["Geographic Area (sq. km)"] = merged_df[
                "Geographic Area (sq. km)_gdf"
            ]
        else:
            data_df["Geographic Area (sq. km)"] = merged_df["Geographic Area (sq. km)"]

    if "ColorGroup_gdf" in merged_df.columns:
        data_df["ColorGroup"] = merged_df["ColorGroup_gdf"]
    else:
        data_df["ColorGroup"] = merged_df["ColorGroup"]

    data_df.to_csv(csv_file, index=False)


def modify_handler(map_name, user_friendly_name, region_name_id_dict):
    with open("../internal/handler_metadata.py", "r") as handler_metadata_py_file:
        handler_metadata_py_contents = handler_metadata_py_file.read()

        print()
        print(
            "I will now modify handler_metadata.py to add your new map. Before I do this, I will back up the current version of handler_metadata.py to handler_metadata.py.bak."
        )
        print()

        print("Backing up handler_metadata.py...")
        shutil.copy(
            "../internal/handler_metadata.py", "../internal/handler_metadata.py.bak"
        )

        web_py_lines = handler_metadata_py_contents.split("\n")
        web_py_new_lines = []
        found_header = False
        for line in web_py_lines:
            if line.strip() == "# ---addmap.py header marker---":
                web_py_new_lines.append("# ---addmap.py header marker---")
                web_py_new_lines.append(
                    "'"
                    + map_name
                    + "': {'name':'"
                    + user_friendly_name
                    + "', 'regions':"
                    + str(region_name_id_dict)
                    + "},"
                )
                found_header = True
            else:
                web_py_new_lines.append(line)

        if not found_header:
            print(
                "I was not able to find the appropriate markers that allow me to modify the handler_metadata.py file."
            )
            return

        with open("../internal/handler_metadata.py", "w") as handler_metadata_py_file:
            handler_metadata_py_file.write("\n".join(web_py_new_lines))


if len(sys.argv) < 2:
    print_usage()
    sys.exit(1)

if sys.argv[1] == "add":
    add_handler(sys.argv[2], sys.argv[3] or "Input.json", sys.argv[4] or "data.csv")
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
