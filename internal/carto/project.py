import json

import shapely
from errors import CartoError
from utils import file_utils, geojson_utils

from .cpp_wrapper import call_binary
from .dataframe import CartoDataFrame
from .formatter import postprocess_geojson, process_data


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
    datacsv, data_cols, map_names_dict = process_data(datacsv, vis_types)
    area_data_path = file_utils.get_safepath(project_path, "data.csv")
    with open(area_data_path, "w") as outfile:
        outfile.write(datacsv)
    data_length = len(data_cols)

    # Process the boundary file
    cdf = CartoDataFrame.read_file(input_file)
    is_projected = cdf.is_projected
    if cdf.is_world:
        flags = flags + ["--world"]

    if (clean_by is not None and clean_by != "") or map_names_dict != {}:
        cdf.clean_properties(clean_by or "Region", map_names_dict=map_names_dict)
        cdf.to_carto_file(input_file)

    if is_projected:
        equal_area_json = call_binary(
            cartogram_key,
            input_file,
            area_data_path,
            flags
            + [
                "--output_shifted_insets",
                "--skip_projection",
                "--area",
                "Geographic Area (sq. km)",
            ],
        )
    else:
        equal_area_json = call_binary(
            cartogram_key,
            input_file,
            area_data_path,
            flags + ["--output_equal_area_map", "--area", "Geographic Area (sq. km)"],
        )

    if equal_area_json is not None:
        equal_area_json = postprocess_geojson(equal_area_json)
        equal_area_json = geojson_utils.add_attributes(
            equal_area_json, is_projected=True
        )
        gen_file = file_utils.get_safepath(project_path, "Geographic Area.json")
        with open(gen_file, "w") as outfile:
            outfile.write(json.dumps(equal_area_json))

        # Prepare area and bounding box of the equal area map for cartogram visualization
        geometries = [
            shapely.geometry.shape(feature["geometry"])
            for feature in equal_area_json["features"]
        ]
        geoms_info = geojson_utils.get_geoms_info(geometries)
        equal_area_area = geoms_info["area"]
        equal_area_centroid = geoms_info["centroid"]
        final_bbox = geoms_info["bbox"]

    else:
        raise CartoError("Error while projecting the boundary file.")

    # Generate cartograms
    for i, data_col in enumerate(data_cols):
        progress_options = {
            "data_name": f"{data_col['column_name']} ({i + 1}/{data_length})",
            "data_index": i,
            "data_length": data_length,
            "print": print_progress,
            "error_prefix": f"Cannot generate cartogram for {data_col['name']}.",
        }

        cartogram_gen_output_json = call_binary(
            cartogram_key,
            gen_file,
            area_data_path,
            flags + ["--skip_projection", "--area", data_col["column_name"]],
            progress_options,
        )
        if cartogram_gen_output_json is None:
            raise CartoError(f"Cannot generate cartogram for {data_col['name']}.")

        cartogram_json = cartogram_gen_output_json["Original"]
        cartogram_json = postprocess_geojson(
            cartogram_json, equal_area_area, equal_area_centroid
        )
        final_bbox = geojson_utils.union_bounding_boxes(
            final_bbox, cartogram_json["bbox"]
        )

        with open(
            file_utils.get_safepath(project_path, f"{data_col['name']}.json"), "w"
        ) as outfile:
            cartogram_json = geojson_utils.add_attributes(
                cartogram_json, is_projected=True
            )
            outfile.write(json.dumps(cartogram_json))

        with open(
            file_utils.get_safepath(
                project_path, f"{data_col['name']}_simplified.json"
            ),
            "w",
        ) as outfile:
            cartogram_json_simplified = cartogram_gen_output_json["Simplified"]
            cartogram_json_simplified = geojson_utils.add_attributes(
                cartogram_json_simplified, is_projected=True
            )
            outfile.write(json.dumps(cartogram_json_simplified))

    # Update bbox so all visualized geojson have the same bounding box
    for data_col in [{"name": "Geographic Area"}] + data_cols:
        file_path = file_utils.get_safepath(project_path, f"{data_col['name']}.json")
        with open(file_path, "r") as f:
            geo_json = json.load(f)
        geo_json["bbox"] = final_bbox
        with open(file_path, "w") as outfile:
            outfile.write(json.dumps(geo_json))

    return
