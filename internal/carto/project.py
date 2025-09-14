import json

import shapely
from carto import boundary, datacsv
from carto.dataframe import CartoDataFrame
from carto.generators import generator_contiguous
from carto.progress import CartoProgress
from utils import file_utils, geojson_utils


def generate(
    csv_string,
    vis_types,
    input_file,
    cartogram_key,
    project_path,
    clean_by=None,
    flags=[],
):
    area_data_path = file_utils.get_safepath(project_path, "data.csv")
    map_regions_dict, data_names = datacsv.process_data(
        csv_string, vis_types, area_data_path
    )

    # Process the boundary file
    cdf = CartoDataFrame.read_file(input_file)

    if (clean_by is not None and clean_by != "") or map_regions_dict != {}:
        cdf.clean_properties(clean_by or "Region", map_names_dict=map_regions_dict)

    equal_area_file = file_utils.get_safepath(project_path, "Geographic Area.json")
    equal_area_json = boundary.generate_equal_area(
        cdf,
        input_file,
        area_data_path,
        equal_area_file,
        flags,
    )

    # Prepare area and bounding box of the equal area map for cartogram visualization
    geometries = [
        shapely.geometry.shape(feature["geometry"])
        for feature in equal_area_json["features"]
    ]
    geoms_info = geojson_utils.get_geoms_info(geometries)
    equal_area_area = geoms_info["area"]
    equal_area_centroid = geoms_info["centroid"]
    final_bbox = geoms_info["bbox"]

    # Set up progress reporter
    progress = CartoProgress(cartogram_key)
    progress.setData(vis_types.get("cartogram", []))

    # Generate cartograms
    generator_contiguous.generate_all(
        project_path,
        equal_area_file,
        equal_area_area,
        equal_area_centroid,
        area_data_path,
        vis_types.get("cartogram", []),
        data_names,
        final_bbox,
        flags,
        progress,
    )

    # Update bbox so all visualized geojson have the same bounding box
    data_names["Geographic Area"] = "Geographic Area"
    for data_col in ["Geographic Area"] + vis_types.get("cartogram", []):
        file_path = file_utils.get_safepath(
            project_path, f"{data_names[data_col]}.json"
        )
        with open(file_path, "r") as f:
            geo_json = json.load(f)
        geo_json["bbox"] = final_bbox
        with open(file_path, "w") as outfile:
            outfile.write(json.dumps(geo_json))

    return
