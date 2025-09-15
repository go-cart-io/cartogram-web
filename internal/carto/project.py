import json

from carto import boundary
from carto.datacsv import CartoCsv
from carto.dataframe import CartoDataFrame
from carto.generators import generator_contiguous
from carto.progress import CartoProgress
from utils import file_utils


def generate(
    csv_string,
    vis_types,
    input_file,
    cartogram_key,
    project_path,
    clean_by=None,
    flags=[],
):
    datacsv = CartoCsv(csv_string, vis_types)
    area_data_path = datacsv.save(project_path, "data.csv")

    # Process the boundary file
    cdf = CartoDataFrame.read_file(input_file)

    if (clean_by is not None and clean_by != "") or datacsv.map_regions_dict != {}:
        cdf.clean_properties(
            clean_by or "Region", map_names_dict=datacsv.map_regions_dict
        )

    equal_area_json = boundary.generate_equal_area(
        cdf, input_file, area_data_path, flags
    )
    equal_area_file = equal_area_json.save(project_path, "Geographic Area.json")
    final_bbox = equal_area_json.geoms_info["bbox"].copy()

    # Set up progress reporter
    progress = CartoProgress(cartogram_key)
    progress.setData(vis_types.get("cartogram", []))

    # Generate cartograms
    generator_contiguous.generate_all(
        project_path,
        equal_area_file,
        equal_area_json.geoms_info["area"],
        equal_area_json.geoms_info["centroid"],
        area_data_path,
        vis_types.get("cartogram", []),
        datacsv.data_names,
        final_bbox,
        flags,
        progress,
    )

    # Update bbox so all visualized geojson have the same bounding box
    for data_col in ["Geographic Area"] + vis_types.get("cartogram", []):
        file_path = file_utils.get_safepath(
            project_path, f"{datacsv.data_names[data_col]}.json"
        )
        with open(file_path, "r") as f:
            geo_json = json.load(f)
        geo_json["bbox"] = final_bbox
        with open(file_path, "w") as outfile:
            outfile.write(json.dumps(geo_json))

    return
