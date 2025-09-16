import numpy as np
import pandas as pd
import shapely
from carto.dataframe import CartoDataFrame
from carto.datajson import CartoJson
from carto.progress import CartoProgress


def generate_all(
    project_path: str,
    equal_area_path: str,
    data_df: pd.DataFrame,
    data_cols: list[str],
    data_names: dict[str, str],
    final_bbox: list[float],
    progress: CartoProgress,
):
    """
    Generate cartograms for all specified data columns and save them as JSON files.

    This function creates non-contiguous cartograms where regions are scaled based on
    data values, with larger values resulting in larger region representations.

    Args:
        project_path: Directory path where output files will be saved
        equal_area_path: Path to the equal area projection data
        data_df: DataFrame containing the data values to visualize
        data_cols: List of column names in data_df to create cartograms for
        data_names: Dictionary mapping column names to human-readable names for output files
        final_bbox: Bounding box coordinates [min_x, min_y, max_x, max_y] for the output
        progress: Progress tracker object for monitoring completion status
    """
    cdf = CartoDataFrame.read_file(equal_area_path)

    # Merge the geographic data with the statistical data on the "Region" column
    # Uses left join to preserve all geographic regions even if no data exists
    merged_cdf = cdf.merge(data_df, on="Region", how="left")

    # Generate a cartogram for each specified data column
    for data_col in data_cols:
        # Mark this cartogram as start in the progress tracker
        progress.start(data_col)

        # Calculate scaling factors
        # Values are normalized to 0-1 range based on the maximum value
        max = merged_cdf[data_col].max()
        scale_values = np.sqrt(merged_cdf[data_col].values / max)

        # Generate the non-contiguous cartogram by scaling regions according to data values
        # Regions with higher values will appear larger in the visualization
        scaled_cdf = generate_noncontiguous(cdf, scale_values)

        # Save the cartogram to a JSON file
        cartogram_json = CartoJson(scaled_cdf.to_json_obj())
        cartogram_json.json_data["bbox"] = final_bbox
        cartogram_json.postprocess()
        cartogram_json.save(
            project_path, f"{data_names[data_col]}.json", is_projected=True
        )

        progress.set(1, "", data_col, 1)


def generate_noncontiguous(
    cdf: CartoDataFrame, scale_values: np.ndarray, scale_factor: float = 0.9
):
    """
    Create a non-contiguous cartogram by scaling each polygon about its centroid.

    Parameters:
    -----------
    cdf : CartoDataFrame
        Input geodataframe with polygon geometries
    scale_values : numpy.ndarray
        Values to scale by
    scale_factor : float, default 0.9
        Overall scaling factor to apply

    Returns:
    --------
    CartoDataFrame with scaled geometries
    """
    # Create a copy to avoid modifying original data
    scaled_cdf = cdf.copy()
    scale_values = scale_values * scale_factor

    scaled_geoms = []
    for geom, factor in zip(scaled_cdf.geometry, scale_values):
        # Scale geometry relative to its centroid
        scaled_geom = shapely.affinity.scale(
            geom, xfact=factor, yfact=factor, origin=geom.centroid
        )
        scaled_geoms.append(scaled_geom)

    scaled_cdf["geometry"] = scaled_geoms

    return scaled_cdf
