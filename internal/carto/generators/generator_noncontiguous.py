import numpy as np
import shapely
from carto.dataframe import CartoDataFrame
from carto.datajson import CartoJson


def generate(
    project_path: str,
    equal_area_cdf: CartoDataFrame,
    merged_cdf: CartoDataFrame,
    data_col: str,
    data_name: str,
    final_bbox: list[float],
    scale_factor: float = 0.9,
):
    """
    Generate cartograms for all specified data columns and save them as JSON files.

    This function creates non-contiguous cartograms where regions are scaled based on
    data values, with larger values resulting in larger region representations.

    Args:
        project_path: Directory path where output files will be saved
        equal_area_cdf: CartoDataFrame of the equal area map
        merged_cdf: CartoDataFrame containing the equal area map merged with the data values to visualize
        data_col: Column name in merged_cdf to create cartogram for
        data_name: Output file name
        final_bbox: Bounding box coordinates [min_x, min_y, max_x, max_y] for the output
        scale_factor : Overall scaling factor to apply, default 0.9
    """
    # Create a copy to avoid modifying original data
    scaled_cdf = equal_area_cdf.copy()

    # Calculate scaling factors
    # Values are normalized to 0-1 range based on the maximum value
    max = merged_cdf[data_col].max()
    scale_values = np.sqrt(merged_cdf[data_col].values / max)
    scale_values = scale_values * scale_factor

    scaled_geoms = []
    for geom, factor in zip(scaled_cdf.geometry, scale_values):
        # Scale geometry relative to its centroid
        scaled_geom = shapely.affinity.scale(
            geom, xfact=factor, yfact=factor, origin=geom.centroid
        )
        scaled_geoms.append(scaled_geom)

    scaled_cdf["geometry"] = scaled_geoms

    # Save the cartogram to a JSON file
    cartogram_json = CartoJson(scaled_cdf.to_json_obj())
    cartogram_json.json_data["bbox"] = final_bbox
    cartogram_json.postprocess()
    cartogram_json.save(project_path, f"{data_name}.json", is_projected=True)
