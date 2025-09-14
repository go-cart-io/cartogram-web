import json

from carto.formatter import postprocess_geojson
from carto.generators.cpp_wrapper import run_binary
from carto.progress import CartoProgress
from errors import CartoError
from utils import file_utils, geojson_utils


def generate_all(
    project_path: str,
    equal_area_path: str,
    equal_area_area: float,
    equal_area_centroid: dict[str, float],
    area_data_path: str,
    data_cols: list[str],
    data_names: dict[str, str],
    final_bbox: list[float],
    flags: list[str],
    progress: CartoProgress,
):
    """
    Generate cartograms for multiple data columns and save them to JSON files.

    This function iterates through data columns to create cartograms using an external
    binary tool, post-processes the results, and saves both original and simplified
    versions to the project directory.

    Args:
        project_path: Directory path where output files will be saved
        equal_area_path: Path to the equal area map to be used as an input
        equal_area_area: Area value for the equal area projection (for adjusting the scale)
        equal_area_centroid: Dictionary containing x,y coordinates of the centroid (for adjusting the scale)
        area_data_path: Path to the csv input data file containing area information
        data_cols: List of column names in the csv to generate cartograms for
        data_names: Dictionary mapping column names to file names
        final_bbox: Initial bounding box that will be expanded to include all cartograms
        flags: List of command-line flags to pass to the cartogram generation binary
        progress: Progress tracking object for monitoring generation status

    Returns:
        list[float]: Updated bounding box that encompasses all generated cartograms

    Raises:
        CartoError: If cartogram generation fails for any data column
        Exception: Re-raises any other unexpected exceptions
    """

    # Process each data column to generate its corresponding cartogram
    for data_col in data_cols:
        cartogram_gen_output_json = None

        try:
            # Run the cartogram generation binary with specified parameters
            # Skip projection since we're working with equal area data
            cartogram_gen_output_json = run_binary(
                equal_area_path,
                area_data_path,
                data_col,
                flags + ["--skip_projection", "--area", data_col],
                progress,
            )
            progress.done()

        except CartoError as e:
            raise CartoError(f"Cannot generate cartogram for {data_col}. {e.message}")
        except Exception:
            raise

        # Verify that the cartogram generation was successful
        if cartogram_gen_output_json is None:
            raise CartoError(f"Cannot generate cartogram for {data_col}.")

        # Extract and post-process the original cartogram data
        cartogram_json = cartogram_gen_output_json["Original"]
        cartogram_json = postprocess_geojson(
            cartogram_json, equal_area_area, equal_area_centroid
        )

        # Update the final bounding box to include this cartogram's extent
        final_bbox = geojson_utils.union_bounding_boxes(
            final_bbox, cartogram_json["bbox"]
        )

        # Save the original cartogram to a JSON file
        out_path = file_utils.get_safepath(project_path, f"{data_names[data_col]}.json")
        with open(out_path, "w") as outfile:
            cartogram_json = geojson_utils.add_attributes(
                cartogram_json, is_projected=True
            )
            outfile.write(json.dumps(cartogram_json))

        # Save the simplified version of the cartogram to a separate JSON file
        out_path = file_utils.get_safepath(
            project_path, f"{data_names[data_col]}_simplified.json"
        )
        with open(out_path, "w") as outfile:
            cartogram_json_simplified = cartogram_gen_output_json["Simplified"]
            cartogram_json_simplified = geojson_utils.add_attributes(
                cartogram_json_simplified, is_projected=True
            )
            outfile.write(json.dumps(cartogram_json_simplified))

    # Return the updated bounding box that encompasses all generated cartograms
    return final_bbox
