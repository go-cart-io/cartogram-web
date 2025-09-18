import json
import os

from carto import boundary
from carto.datacsv import CartoCsv
from carto.dataframe import CartoDataFrame
from carto.generators import generator_contiguous, generator_noncontiguous
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
    progress.setData(datacsv.data_cols)

    # Prepare data for noncontiguous
    # Merge the geographic data with the statistical data on the "Region" column
    # Uses left join to preserve all geographic regions
    # For columns with the same names, use data from the csv
    equal_area_cdf = CartoDataFrame.read_file(equal_area_file)
    merged_cdf = equal_area_cdf.merge(
        datacsv.df, on="Region", how="left", suffixes=("_drop", None)
    )
    merged_cdf = merged_cdf.loc[:, ~merged_cdf.columns.str.endswith("_drop")]

    for data_col in datacsv.data_cols:
        progress.start(data_col)

        if vis_types.get(data_col) == "contiguous":
            # Generate contiguous cartograms
            final_bbox = generator_contiguous.generate(
                project_path,
                equal_area_file,
                equal_area_json.geoms_info.get("area", 1),
                equal_area_json.geoms_info.get("centroid", {"x": 0, "y": 0}),
                area_data_path,
                data_col,
                datacsv.data_names.get(data_col, "Data"),
                final_bbox,
                flags,
                progress,
            )
        elif vis_types.get(data_col) == "noncontiguous":
            # Generate non-contiguous cartograms
            generator_noncontiguous.generate(
                project_path,
                equal_area_cdf,
                merged_cdf,
                data_col,
                datacsv.data_names.get(data_col, "Data"),
                final_bbox,
            )

        progress.set(1, "", data_col, 1)

    # Update bbox so all visualized geojson have the same bounding box
    for data_col in ["Geographic Area"] + datacsv.data_cols:
        file_path = file_utils.get_safepath(
            project_path, f"{datacsv.data_names.get(data_col, 'Data')}.json"
        )

        if not os.path.exists(file_path):
            continue

        with open(file_path, "r") as f:
            geo_json = json.load(f)
        geo_json["bbox"] = final_bbox
        with open(file_path, "w") as outfile:
            outfile.write(json.dumps(geo_json))

    return
