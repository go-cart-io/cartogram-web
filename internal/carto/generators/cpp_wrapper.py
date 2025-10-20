import json
import os
import subprocess
import threading
from pathlib import Path
from queue import Queue
from typing import IO, Generator

import settings
from carto.progress import CartoProgress
from errors import CartoError
from utils import file_utils


def run_binary(
    gen_path: str,
    area_data_path: str | None,
    data_name: str = "",
    flags: list[str] = [],
    progress: CartoProgress | None = None,
) -> dict | None:
    """
    Run cartogram-cpp binary and track the progress.

    Args:
        gen_path: Path to the boundary/geometry file for cartogram generation
        area_data_path: Path to the area data file containing population/data values
        data_name: Human-readable name for the data column
        flags: List of command-line flags to pass to the cartogram executable
        progress: Progress object to display generation progress

    Returns:
        dict: JSON-parsed output from cartogram generation, or None if no output

    Raises:
        CartoError: If an error occurs during cartogram generation
    """

    # Initialize output capture variables
    stdout = ""
    stderr = f"Process {data_name} ****************\n"
    warning_msg_array = []
    error_msg = ""
    last_factor = None
    last_geo_div = ""
    order = 0  # Counter for progress update ordering

    # Run the cartogram binary and process its output line by line
    for source, line in execute(gen_path, area_data_path, flags):
        if source == "stdout":
            # Accumulate standard output (contains JSON result)
            stdout += line.decode()
        else:
            # Process stderr for progress updates and error messages
            line_str = line.decode()
            line_arr = line_str.split(":")
            stderr += line_str

            try:
                match line_arr[0]:
                    case "Progress":
                        # Update progress in database/tracking system
                        if progress:
                            progress.set(order, stderr, data_name, float(line_arr[1]))

                        order += 1  # Increment order counter for next progress update

                    case "Max. area err":
                        # Max. area err: 0.00994953, GeoDiv: New Hampshire
                        last_factor = float(line_arr[1].replace(", GeoDiv", ""))
                        last_geo_div = line_arr[2]

                    case "WARNING":
                        warning_msg = line_arr[1].strip()
                        warning_msg_array.append(data_name + ": " + warning_msg)

                    case "ERROR":
                        error_msg = line_arr[1].strip()

                    case _:
                        pass

            except:  # noqa: E722
                pass

    # Handle processing results
    if error_msg != "":
        raise CartoError(error_msg)
    elif stdout == "":
        return None

    # Parse and return JSON output from successful cartogram generation
    json_output = json.loads(stdout)

    if warning_msg_array:
        if last_factor is not None and last_factor > 0.01:
            last_factor = round(last_factor * 100, 2)
            warning_msg_array.append(
                f"{data_name}: The resulting cartogram contains areas that deviate from their ideal size. \
                    {last_geo_div} is the most distorted, appearing at {last_factor}% of its expected area."
            )

        json_output["Warnings"] = warning_msg_array

    return json_output


def execute(
    input_path: str, area_data_path: str | None, custom_flags: list[str] = []
) -> Generator[tuple[str, bytes], None, None]:
    """
    Execute the cartogram binary with specified parameters and stream its output.

    Args:
        input_path: Path to the boundary/geometry file
        area_data_path: Path to the area data file (can be None)
        custom_flags: List of additional command-line flags for the executable

    Yields:
        tuple: (source, line) where source is "stdout" or "stderr" and line is bytes

    Raises:
        CartoError: If the boundary file path is invalid
    """
    # Construct path to the cartogram executable
    uname = os.uname()
    system = uname.sysname.lower()
    machine = uname.machine.lower()
    binary_name = "cartogram-linux-amd64"
    if system == "linux" and ("aarch64" in machine or "arm64" in machine):
        binary_name = "cartogram-linux-arm64"

    current_file = Path(__file__).resolve()
    cartogram_path = current_file.parent.parent.parent / "executable" / binary_name

    # Validate the custom flags before proceeding
    validate_options(custom_flags)

    # Sanitize and validate the geometry file path
    input_path = file_utils.get_safepath(input_path)
    if not os.path.isfile(input_path):
        raise CartoError(f"Invalid boundary file path: {input_path}")

    # Build command line arguments
    args = [
        str(cartogram_path),
        input_path,
        "--redirect_exports_to_stdout",
    ] + custom_flags

    if settings.CARTOGRAM_TIME_LIMIT:
        args = args + ["--timeout", settings.CARTOGRAM_TIME_LIMIT]

    area_data_path = (
        file_utils.get_safepath(area_data_path) if area_data_path is not None else ""
    )
    if os.path.isfile(area_data_path):
        args.append(area_data_path)

    # Start the cartogram process with pipes for communication
    cartogram_process = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Set up threaded readers for stdout and stderr to prevent blocking
    q = Queue()
    threading.Thread(
        target=reader, args=[cartogram_process.stdout, "stdout", q]
    ).start()
    threading.Thread(
        target=reader, args=[cartogram_process.stderr, "stderr", q]
    ).start()

    # Set up a 300-second timeout to prevent hanging processes
    timer = threading.Timer(300, cartogram_process.terminate)
    timer.start()

    try:
        # Read from both stdout and stderr streams until both threads finish
        # The range(2) accounts for the two reader threads
        for _ in range(2):
            for source, line in iter(q.get, None):
                yield source, line
    finally:
        # Ensure timer is cancelled to prevent resource leaks
        timer.cancel()


def reader(
    pipe: IO[bytes], pipe_name: str, queue: Queue[tuple[str, bytes] | None]
) -> None:
    """
    Thread worker function to read from a pipe and put lines into a queue.

    This function runs in a separate thread to prevent blocking when reading
    from subprocess stdout/stderr pipes.

    Args:
        pipe: The pipe object (stdout or stderr) to read from
        pipe_name: String identifier ("stdout" or "stderr") for the pipe
        queue: Queue object to put the read lines into
    """
    try:
        # Read lines from the pipe until EOF
        with pipe:
            for line in iter(pipe.readline, b""):
                # Put each line into the queue with its source identifier
                queue.put((pipe_name, line))
    finally:
        # Signal completion by putting None into the queue
        queue.put(None)


def validate_options(options: list[str]) -> None:
    """Validate that an array contains only allowed options.

    Args:
        options: List of strings to validate

    Returns:
        bool: True if all options are valid, False otherwise
    """
    allowed_options = {
        "--output_equal_area_map",
        "--world",
        "--output_shifted_insets",
        "--skip_projection",
        "--area",
        "--do_not_fail_on_intersections",
        "--timeout",
    }

    i = 0
    n = len(options)

    while i < n:
        option = options[i]

        # Check if the option is one of the allowed ones
        if option not in allowed_options:
            raise CartoError(f"Invalid cartogram option: {option}")

        # If the option is --area, the next element can be arbitrary text that is safe for filename
        if option == "--area" and i + 1 < n:
            if not options[i + 1] == file_utils.sanitize_filename(options[i + 1]):
                raise CartoError(f"Invalid cartogram option: {options[i + 1]}")
            i += 1

        # If the option is --timeout, the next element can be arbitrary number
        if option == "--timeout" and i + 1 < n:
            if not (options[i + 1]).isdigit():
                raise CartoError(f"Invalid cartogram option: {options[i + 1]}")
            i += 1

        i += 1
