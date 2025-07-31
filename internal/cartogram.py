import json
import math
import re
import warnings
from io import StringIO

import mapclassify
import pandas as pd
import redis
import settings
import shapely
import util
from carto_dataframe import CartoDataFrame
from errors import CartogramError
from executable import cartwrap


def preprocess(input, mapDBKey="temp_filename", based_path="tmp"):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = preprocess_boundary(input, mapDBKey, based_path)

        result["warnings"] = []
        for warning_message in w:
            if (
                "Geometry is in a geographic CRS. Results from 'area' are likely incorrect."
                in str(warning_message.message)
            ):
                result["warnings"].append(
                    "Geometry is in a geographic CRS. The geographic area calculation (in sq. km) is likely incorrect, but your cartogram will still render accurately."
                )

            elif "More than one layer found" in str(warning_message.message):
                result["warnings"].append(
                    "Multiple map layers found. If the preview isn't what you expected, please remove unwanted map layers and re-upload your boundary file."
                )

    return result


def preprocess_boundary(input, mapDBKey="temp_filename", based_path="tmp"):
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
        equal_area_json = preprocess_geojson(mapDBKey, file_path, None, flags)
        if equal_area_json is None:
            equal_area_json = geojson
    else:
        geojson = cdf.to_carto_file(file_path)
        equal_area_json = postprocess_geojson(geojson)

    return {"geojson": equal_area_json, "unique": unique_columns}


def generate_cartogram(
    datacsv,
    vis_types,
    input_file,
    cartogram_key,
    project_path,
    clean_by=None,
    print_progress=False,
    flags=[],
):
    datacsv, data_cols, prefered_names_dict = process_data(datacsv, vis_types)
    area_data_path = util.get_safepath(project_path, "data.csv")
    with open(area_data_path, "w") as outfile:
        outfile.write(datacsv)
    data_length = len(data_cols)

    if data_length == 0:
        raise CartogramError(
            "Missing data. Please add at least one data column to the table."
        )

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

        # Prepare area and bounding box of the equal area map for cartogram visualization
        geometries = [
            shapely.geometry.shape(feature["geometry"])
            for feature in equal_area_json["features"]
        ]
        geoms_info = util.get_geoms_info(geometries)
        equal_area_area = geoms_info["area"]
        equal_area_centroid = geoms_info["centroid"]
        final_bbox = geoms_info["bbox"]

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
        cartogram_json = postprocess_geojson(
            cartogram_json, equal_area_area, equal_area_centroid
        )
        final_bbox = util.union_bounding_boxes(final_bbox, cartogram_json["bbox"])

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

    # Update bbox so all visualized geojson have the same bounding box
    for data_col in [{"name": "Geographic Area"}] + data_cols:
        file_path = util.get_safepath(project_path, f"{data_col['name']}.json")
        with open(file_path, "r") as f:
            geo_json = json.load(f)
        geo_json["bbox"] = final_bbox
        with open(file_path, "w") as outfile:
            outfile.write(json.dumps(geo_json))

    return


def process_data(csv_string, vis_types):
    df = pd.read_csv(StringIO(csv_string), keep_default_na=False, na_values=[""])
    for col in df.columns:
        util.validate_filename(col)

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

            if name == "":
                raise CartogramError(
                    "Missing data name. Please ensure each data column has a name in its header."
                )

            if df[column].isna().all():
                raise CartogramError(
                    f"Cannot process {column}: All rows are empty. Please enter some numeric values or remove the column."
                )

            sum = df[column].sum()
            if column in vis_types["cartogram"] and sum == 0:
                raise CartogramError(
                    f"Cannot process {column}: Sum is zero. Please ensure the sum of data is not zero."
                )

            if column in vis_types.get("cartogram", []):
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


def postprocess_geojson(json_data, target_area=None, target_centroid=None):
    geometries = [
        shapely.geometry.shape(feature["geometry"]) for feature in json_data["features"]
    ]
    geoms_info = util.get_geoms_info(geometries)

    # Scale and translate to match with the target area and centroid
    if target_area and target_centroid:
        scale_factor = math.sqrt(target_area / geoms_info["area"])
        origin_x = geoms_info["centroid"]["x"]
        origin_y = geoms_info["centroid"]["y"]
        diff_x = target_centroid["x"] - origin_x
        diff_y = target_centroid["y"] - origin_y

        for index, feature in enumerate(json_data["features"]):
            geometries[index] = shapely.affinity.scale(
                geometries[index],
                xfact=scale_factor,
                yfact=scale_factor,
                origin=(origin_x, origin_y),
            )
            geometries[index] = shapely.affinity.translate(
                geometries[index],
                xoff=diff_x,
                yoff=diff_y,
            )
            feature["geometry"] = shapely.geometry.mapping(geometries[index])

        if "dividers" in json_data:
            adjusted_dividers = shapely.affinity.scale(
                shapely.geometry.shape(json_data["dividers"]["geometry"]),
                xfact=scale_factor,
                yfact=scale_factor,
                origin=(origin_x, origin_y),
            )
            adjusted_dividers = shapely.affinity.translate(
                adjusted_dividers,
                xoff=diff_x,
                yoff=diff_y,
            )
            json_data["dividers"]["geometry"] = shapely.geometry.mapping(
                adjusted_dividers
            )

        geoms_info["bbox"][0] = (
            origin_x + (geoms_info["bbox"][0] - origin_x) * scale_factor
        ) + diff_x
        geoms_info["bbox"][1] = (
            origin_y + (geoms_info["bbox"][1] - origin_y) * scale_factor
        ) + diff_y
        geoms_info["bbox"][2] = (
            origin_x + (geoms_info["bbox"][2] - origin_x) * scale_factor
        ) + diff_x
        geoms_info["bbox"][3] = (
            origin_y + (geoms_info["bbox"][3] - origin_y) * scale_factor
        ) + diff_y

    # Get point to place the label
    for index, feature in enumerate(json_data["features"]):
        point = geometries[index].representative_point()
        feature["properties"]["label"] = {"x": point.x, "y": point.y}

    # Fix format of dividers
    if "dividers" in json_data:
        json_data["dividers"] = [json_data["dividers"]]

    # Make sure that json file have bbox
    json_data["bbox"] = geoms_info["bbox"]

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
