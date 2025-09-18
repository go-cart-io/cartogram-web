import numpy as np
import pandas as pd
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

    # Compute mean spatial density
    area_col = "Geographic Area (sq. km)"
    dens_col = "Calculated Density"
    if "Geographic Area (sq. km)" not in merged_cdf.columns:
        area_col = "Calculated Area"
        merged_cdf[area_col] = round(merged_cdf.area / 10**6)
    merged_cdf[area_col] = pd.to_numeric(merged_cdf[area_col], errors="coerce")
    merged_cdf[data_col] = pd.to_numeric(merged_cdf[data_col], errors="coerce")
    observed = merged_cdf.copy().dropna(subset=[data_col])
    total_area = observed[area_col].sum()
    total_value = observed[data_col].sum()
    rho_bar = total_value / total_area

    # Fill in missing value
    merged_cdf[data_col] = merged_cdf[data_col].fillna(merged_cdf[area_col] * rho_bar)

    # Calculate scaling factors
    # Values are normalized to 0-1 range based on the maximum value
    merged_cdf[dens_col] = merged_cdf[data_col] / merged_cdf[area_col]
    max = merged_cdf[dens_col].max()
    scale_values = np.sqrt(merged_cdf[dens_col].values / max)
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
