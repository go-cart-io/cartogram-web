import json
import os
import re
from io import StringIO

import mapclassify
import pandas as pd
import redis
import settings
import util
from carto_dataframe import CartoDataFrame
from executable import cartwrap
from shapely.geometry import shape


def preprocess(input, mapDBKey="temp_filename", based_path="/tmp"):
    # Input can be anything that is supported by geopandas.read_file
    # Standardize input to geojson file path
    file_path = os.path.join(based_path, f"{mapDBKey}.json")
    if isinstance(input, str):  # input is path
        input_path = input
    else:  # input is file object
        input.save(file_path)
        input_path = file_path

    cdf = CartoDataFrame.read_file(input_path)

    # Remove invalid geometries
    cdf = cdf[cdf.geometry.notnull()]
    cdf = cdf[cdf.geometry.type.isin(["Polygon", "MultiPolygon"])].reset_index(
        drop=True
    )

    # Get nesseary information
    unique_columns = []
    for column in cdf.columns:
        if column == "geometry":
            continue
        cdf[column] = util.convert_col_to_serializable(cdf[column])
        if cdf[column].is_unique:
            unique_columns.append(column)

    if not cdf.is_projected:
        # Temporary project it so we can calculate the area
        cdf.to_crs(
            "EPSG:6933", inplace=True
        )  # NSIDC EASE-Grid 2.0 Global https://epsg.io/6933

    if not any(cdf.columns.str.startswith("Geographic Area")):
        cdf["Geographic Area (sq. km)"] = round(cdf.area / 10**6)
        cdf["Geographic Area (sq. km)"] = cdf["Geographic Area (sq. km)"].astype(int)

    if "ColorGroup" not in cdf.columns:
        tmp_cdf = cdf.to_crs("EPSG:6933") # Forced projected file just for surprass mapclassify's warning
        cdf["ColorGroup"] = mapclassify.greedy(tmp_cdf, min_colors=6, balance="distance")
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
        equal_area_json = preprocess_geojson(mapDBKey, file_path, None, flags)
        if equal_area_json is None:
            equal_area_json = geojson
    else:
        geojson = cdf.to_carto_file(file_path)
        equal_area_json = postprocess_geojson(geojson)

    return {"geojson": equal_area_json, "unique": unique_columns}


def generate_cartogram(
    datacsv,
    input_file,
    cartogram_key,
    project_path,
    clean_by=None,
    print_progress=False,
    flags=[],
):
    datacsv, datasets, is_area_as_base, prefered_names_dict = process_data(datacsv)
    with open(f"{project_path}/data.csv", "w") as outfile:
        outfile.write(datacsv)
    data_length = len(datasets)

    # Process the boundary file
    cdf = CartoDataFrame.read_file(input_file)
    is_projected = cdf.is_projected
    if cdf.is_world:
        flags = flags + ["--world"]
    if clean_by is not None and clean_by != "":
        cdf.clean_and_sort(
            clean_by or "Region", prefered_names_dict=prefered_names_dict
        )
        cdf.to_carto_file(input_file)

    if is_projected:
        equal_area_json = preprocess_geojson(
            cartogram_key,
            input_file,
            datasets[0],
            flags + ["--output_shifted_insets", "--skip_projection"],
        )
    else:
        equal_area_json = preprocess_geojson(
            cartogram_key, input_file, datasets[0], flags + ["--output_equal_area_map"]
        )

    if equal_area_json is not None:
        equal_area_json = util.add_attributes(equal_area_json, is_projected=True)
        with open(f"{project_path}/Geographic Area.json", "w") as outfile:
            outfile.write(json.dumps(equal_area_json))
    else:
        raise "Error while projecting the boundary file."

    gen_file = f"{project_path}/Geographic Area.json"

    # Generate cartograms
    for i, dataset in enumerate(datasets):
        datastring = dataset["datastring"]
        name = dataset["label"]

        lambda_event = {
            "gen_file": gen_file,
            "area_data": datastring,
            "key": cartogram_key,
            "flags": flags + ["--skip_projection"],
        }

        cartogram_result = call_binary(lambda_event, i, data_length, print_progress)

        if cartogram_result["stdout"] == "":
            raise RuntimeError(
                f"Cannot generate cartogram for {name} - {cartogram_result['error_msg']}"
            )

        cartogram_gen_output = cartogram_result["stdout"]
        cartogram_gen_output_json = json.loads(cartogram_gen_output)

        cartogram_json = cartogram_gen_output_json["Original"]
        cartogram_json = postprocess_geojson(cartogram_json)
        with open(f"{project_path}/{name}.json", "w") as outfile:
            cartogram_json = util.add_attributes(cartogram_json, is_projected=True)
            outfile.write(json.dumps(cartogram_json))

        with open(f"{project_path}/{name}_simplified.json", "w") as outfile:
            cartogram_json_simplified = cartogram_gen_output_json["Simplified"]
            cartogram_json_simplified = util.add_attributes(
                cartogram_json_simplified, is_projected=True
            )
            outfile.write(json.dumps(cartogram_json_simplified))

        if not is_area_as_base and i == 0:
            gen_file = "{}/{}.json".format(project_path, name)

    return


def process_data(csv_string):
    df = pd.read_csv(StringIO(csv_string))
    df.columns = [util.sanitize_filename(col) for col in df.columns]
    df["Color"] = df["Color"] if "Color" in df else None
    df["Inset"] = df["Inset"] if "Inset" in df else None
    is_empty_color = df["Color"].isna().all()
    is_empty_inset = df["Inset"].isna().all()

    prefered_names_dict = {}
    if "PreferedName" in df.columns:
        prefered_names_dict = dict(zip(df["Region"], df["PreferedName"]))
        df["Region"] = df["PreferedName"]
        df = df.drop(columns=["PreferedName"])

    datasets = []
    cols_order = ["Region", "RegionLabel", "Color", "ColorGroup", "Inset"]
    is_area_as_base = False
    for column in df.columns:
        if column.startswith("Geographic Area"):
            cols_order.insert(5, column)
            is_area_as_base = True

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
            dataset = df[["Region", column, "Color", "Inset"]]
            datasets.append(
                {
                    "label": name,
                    "datastring": "Region,Data,Color,Inset\n{}".format(
                        dataset.to_csv(header=False, index=False)
                    ),
                }
            )

    df = df.sort_values(by="Region")
    df = df.reindex(columns=cols_order)

    if "ColorGroup" not in df:
        df["ColorGroup"] = (
            ""  # Just to make sure ColorGroup column exists. Color assignment sould be done during geojson processing
        )

    if is_empty_color:
        df.drop(columns="Color", inplace=True)

    if is_empty_inset:
        df.drop(columns="Inset", inplace=True)

    return df.to_csv(index=False), datasets, is_area_as_base, prefered_names_dict


def preprocess_geojson(mapDBKey, file_path, dataset=None, flags=[]):
    result = call_binary(
        {
            "gen_file": file_path,
            "area_data": dataset["datastring"] if dataset else None,
            "key": mapDBKey,
            "flags": flags,
        }
    )
    if result["error_msg"] != "":
        raise RuntimeError(result["error_msg"])
    elif result["stdout"] == "":
        return None

    return postprocess_geojson(json.loads(result["stdout"]))


def postprocess_geojson(json_data):
    for feature in json_data["features"]:
        geom = shape(feature["geometry"])
        point = geom.representative_point()
        feature["properties"]["label"] = {"x": point.x, "y": point.y}

    # TODO This should be done in cpp - just change the format of divider_points
    if "dividers" in json_data:
        json_data["dividers"] = [json_data["dividers"]]

    return json_data


def call_binary(params, data_index=0, data_length=1, print_progress=False):
    stdout = ""
    stderr = "Dataset {}/{}\n".format(data_index + 1, data_length)
    error_msg = ""
    order = 0

    cartogram_exec = os.path.join(os.path.dirname(__file__), "executable/cartogram")
    cartogram_key = params["key"]

    if "area_data" in params.keys() and params["area_data"] is not None:
        area_data_path = "/tmp/{}.csv".format(cartogram_key)
        with open(area_data_path, "w") as areas_file:
            areas_file.write(params["area_data"])
    else:
        area_data_path = None

    if "flags" in params.keys():
        flags = params["flags"]
    else:
        flags = []

    for source, line in cartwrap.generate_cartogram(
        area_data_path, params["gen_file"], cartogram_exec, flags
    ):
        if source == "stdout":
            stdout += line.decode()
        else:
            # stderr_line = line.decode()
            stderr += line.decode()

            # From C++ executable, we directly get cartogram generation progress in percentage; whereas, for C executable
            # we get maximum absolute area error which we translate into progress percentage.

            s = re.search(r"Progress: (.+)", line.decode())

            if s is not None:
                current_progress = float(s.groups(1)[0])

                if (
                    current_progress == 1 and data_index == data_length - 1
                ):  # To prevent stucking at 0.99999
                    current_progress = 1
                else:
                    current_progress = (current_progress / data_length) + (
                        data_index / data_length
                    )

                if print_progress:
                    print("{}%".format(current_progress * 100))

                setprogress(
                    {
                        "key": cartogram_key,
                        "progress": current_progress,
                        "stderr": stderr,
                        "order": order,
                    }
                )

                order += 1

            else:
                e = re.search(r"ERROR: (.+)", line.decode())
                if e is not None:
                    error_msg = e.groups(1)[0]

    if os.path.exists("/tmp/{}.csv".format(cartogram_key)):
        os.remove("/tmp/{}.csv".format(cartogram_key))

    return {"stderr": stderr, "stdout": stdout, "error_msg": error_msg}


def setprogress(params):
    redis_conn = redis.Redis(
        host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0
    )
    current_progress = redis_conn.get("cartprogress-{}".format(params["key"]))

    if current_progress is None:
        current_progress = {
            "order": params["order"],
            "stderr": params["stderr"],
            "progress": params["progress"],
        }
    else:
        current_progress = json.loads(current_progress.decode())

        if current_progress["order"] < params["order"]:
            current_progress = {
                "order": params["order"],
                "stderr": params["stderr"],
                "progress": params["progress"],
            }

    redis_conn.set(
        "cartprogress-{}".format(params["key"]), json.dumps(current_progress)
    )
    redis_conn.expire("cartprogress-{}".format(params["key"]), 300)


def getprogress(key):
    redis_conn = redis.Redis(
        host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0
    )
    current_progress = redis_conn.get("cartprogress-{}".format(key))

    if current_progress is None:
        return {"progress": None, "stderr": ""}
    else:
        current_progress = json.loads(current_progress.decode())
        return {
            "progress": current_progress["progress"],
            "stderr": current_progress["stderr"],
        }
