from carto.datajson import CartoJson
from carto.generators.cpp_wrapper import run_binary
from carto.progress import CartoProgress
from errors import CartoError
from utils import geojson_utils


def generate(
    project_path: str,
    equal_area_path: str,
    equal_area_area: float,
    equal_area_centroid: dict[str, float],
    area_data_path: str,
    data_col: str,
    data_name: str,
    final_bbox: list[float],
    flags: list[str],
    progress: CartoProgress,
):
    """
    Generate cartogram for a data column and save them to JSON file.

    This function create a cartogram using an external binary tool,
    post-processes the result, and saves both original and simplified
    versions to the project directory.

    Args:
        project_path: Directory path where output files will be saved
        equal_area_path: Path to the equal area map to be used as an input
        equal_area_area: Area value for the equal area projection (for adjusting the scale)
        equal_area_centroid: Dictionary containing x,y coordinates of the centroid (for adjusting the scale)
        area_data_path: Path to the csv input data file containing area information
        data_col: The column name in the csv to generate cartograms for
        data_name: Base file name to save cartogram to
        final_bbox: The bounding box that will be expanded to include all cartograms
        flags: List of command-line flags to pass to the cartogram generation binary
        progress: Progress tracking object for monitoring generation status

    Returns:
        list[float]: Updated bounding box that encompasses the generated cartogram

    Raises:
        CartoError: If cartogram generation fails for any data column
        Exception: Re-raises any other unexpected exceptions
    """

    # Process each data column to generate its corresponding cartogram
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

    except CartoError as e:
        raise CartoError(f"Cannot generate cartogram for {data_col}. {e.message}")
    except Exception:
        raise

    # Verify that the cartogram generation was successful
    if cartogram_gen_output_json is None:
        raise CartoError(f"Cannot generate cartogram for {data_col}.")

    is_world = True if "--world" in flags else False

    # Extract and post-process the original cartogram data, save it to a file
    cartogram_json = CartoJson(cartogram_gen_output_json["Original"], is_world)
    cartogram_json.postprocess(equal_area_area, equal_area_centroid)
    cartogram_json.save(project_path, f"{data_name}.json", is_projected=True)

    # Update the final bounding box to include this cartogram's extent
    final_bbox = geojson_utils.union_bounding_boxes(
        final_bbox, cartogram_json.json_data["bbox"]
    )

    # Save the simplified version of the cartogram to a separate JSON file
    cartogram_json_simplified = CartoJson(
        cartogram_gen_output_json["Simplified"], is_world
    )
    cartogram_json_simplified.save(
        project_path,
        f"{data_name}_simplified.json.json",
        is_projected=True,
    )

    # Return the updated bounding box that encompasses the generated cartogram
    return final_bbox
