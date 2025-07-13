import json
import re
from io import StringIO

import mapclassify
import pandas as pd
import redis
import settings
import util
from carto_dataframe import CartoDataFrame
from errors import CartogramError
from executable import cartwrap
from shapely.geometry import shape


def preprocess(input, mapDBKey="temp_filename", based_path="tmp"):
    # Input can be anything that is supported by geopandas.read_file
    # Standardize input to geojson file path
    file_path = util.get_safepath(based_path, f"{mapDBKey}.json")
    if isinstance(input, str):  # input is path
        input_path = input
    else:  # input is file object
        input_path = util.get_safepath("tmp", input.filename)
        input.save(input_path)

    cdf = CartoDataFrame.read_file(input_path)
    cdf.to_carto_file(file_path)

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
        # NSIDC EASE-Grid 2.0 Global https://epsg.io/6933
        cdf.to_crs("EPSG:6933", inplace=True)

    tmp_cdf = cdf

    if not any(cdf.columns.str.startswith("Geographic Area")):
        cdf["Geographic Area (sq. km)"] = round(tmp_cdf.area / 10**6)
        cdf["Geographic Area (sq. km)"] = cdf["Geographic Area (sq. km)"].astype(int)

    if "ColorGroup" not in cdf.columns:
        cdf["ColorGroup"] = mapclassify.greedy(
            tmp_cdf, min_colors=6, balance="distance"
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
    datacsv, data_cols, prefered_names_dict = process_data(datacsv)
    area_data_path = util.get_safepath(project_path, "data.csv")
    with open(area_data_path, "w") as outfile:
        outfile.write(datacsv)
    data_length = len(data_cols)

    if data_length == 0:
        raise CartogramError("Cannot find data column.")

    # Process the boundary file
    cdf = CartoDataFrame.read_file(input_file)
    is_projected = cdf.is_projected
    if cdf.is_world:
        flags = flags + ["--world"]
    if clean_by is not None and clean_by != "":
        cdf.clean_properties(
            clean_by or "Region", prefered_names_dict=prefered_names_dict
        )
        cdf.to_carto_file(input_file)

    if is_projected:
        equal_area_json = preprocess_geojson(
            cartogram_key,
            input_file,
            area_data_path,
            flags
            + [
                "--output_shifted_insets",
                "--skip_projection",
                "--area",
                data_cols[0]["column_name"],
            ],
        )
    else:
        equal_area_json = preprocess_geojson(
            cartogram_key,
            input_file,
            area_data_path,
            flags + ["--output_equal_area_map", "--area", data_cols[0]["column_name"]],
        )

    if equal_area_json is not None:
        equal_area_json = util.add_attributes(equal_area_json, is_projected=True)
        gen_file = util.get_safepath(project_path, "Geographic Area.json")
        with open(gen_file, "w") as outfile:
            outfile.write(json.dumps(equal_area_json))
    else:
        raise CartogramError("Error while projecting the boundary file.")

    # Generate cartograms
    for i, data_col in enumerate(data_cols):
        progress_options = {
            "data_name": f"{data_col['column_name']} ({i + 1}/{data_length})",
            "data_index": i,
            "data_length": data_length,
            "print": print_progress,
        }
        cartogram_result = call_binary(
            cartogram_key,
            gen_file,
            area_data_path,
            flags + ["--skip_projection", "--area", data_col["column_name"]],
            progress_options,
        )

        if cartogram_result["error_msg"] != "":
            raise CartogramError(
                f"Cannot generate cartogram for {data_col['name']}. {cartogram_result['error_msg']}"
            )
        elif cartogram_result["stdout"] == "":
            raise CartogramError(f"Cannot generate cartogram for {data_col['name']}.")

        cartogram_gen_output = cartogram_result["stdout"]
        cartogram_gen_output_json = json.loads(cartogram_gen_output)

        cartogram_json = cartogram_gen_output_json["Original"]
        cartogram_json = postprocess_geojson(cartogram_json)
        with open(
            util.get_safepath(project_path, f"{data_col['name']}.json"), "w"
        ) as outfile:
            cartogram_json = util.add_attributes(cartogram_json, is_projected=True)
            outfile.write(json.dumps(cartogram_json))

        with open(
            util.get_safepath(project_path, f"{data_col['name']}_simplified.json"), "w"
        ) as outfile:
            cartogram_json_simplified = cartogram_gen_output_json["Simplified"]
            cartogram_json_simplified = util.add_attributes(
                cartogram_json_simplified, is_projected=True
            )
            outfile.write(json.dumps(cartogram_json_simplified))

    return


def process_data(csv_string):
    df = pd.read_csv(StringIO(csv_string), keep_default_na=False, na_values=[""])
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
            data_cols.append({"name": name, "column_name": column})

    df = df.reindex(columns=cols_order)

    # Just to make sure ColorGroup column exists. Color assignment should be done during geojson processing
    if "ColorGroup" not in df:
        df["ColorGroup"] = ""

    if is_empty_color:
        df.drop(columns="Color", inplace=True)

    if is_empty_inset:
        df.drop(columns="Inset", inplace=True)

    return df.to_csv(index=False), data_cols, prefered_names_dict


def preprocess_geojson(mapDBKey, file_path, area_data_path=None, flags=[]):
    result = call_binary(mapDBKey, file_path, area_data_path, flags)
    if result["error_msg"] != "":
        raise CartogramError(result["error_msg"])
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


def call_binary(mapDBKey, gen_path, area_data_path, flags=[], progress_options={}):
    data_name = progress_options.get("data_name", "")
    data_index = progress_options.get("data_index", 0)
    data_length = progress_options.get("data_length", 1)
    stdout = ""
    stderr = "Dataset {}/{}\n".format(data_index + 1, data_length)
    error_msg = ""
    order = 0

    for source, line in cartwrap.run_binary(gen_path, area_data_path, flags):
        if source == "stdout":
            stdout += line.decode()
        else:
            stderr += line.decode()

            # From C++ executable, we directly get cartogram generation progress in percentage; whereas, for C executable
            # we get maximum absolute area error which we translate into progress percentage.

            s = re.search(r"Progress: (.+)", line.decode())

            if s is not None:
                current_progress = float(s.groups(1)[0])

                # To prevent stucking at 0.99999
                if current_progress == 1 and data_index == data_length - 1:
                    current_progress = 1
                else:
                    current_progress = (current_progress / data_length) + (
                        data_index / data_length
                    )

                if progress_options.get("print", False):
                    print("{}%".format(current_progress * 100))

                setprogress(
                    {
                        "key": mapDBKey,
                        "name": data_name,
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
            "name": params["name"],
            "progress": params["progress"],
        }
    else:
        current_progress = json.loads(current_progress.decode())

        if current_progress["order"] < params["order"]:
            current_progress = {
                "order": params["order"],
                "stderr": params["stderr"],
                "name": params["name"],
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
            "name": current_progress["name"],
            "progress": current_progress["progress"],
            "stderr": current_progress["stderr"],
        }
