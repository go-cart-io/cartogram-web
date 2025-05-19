import os
import subprocess
import threading
from queue import Queue

import util
from errors import CartogramError


def reader(pipe, pipe_name, queue):
    try:
        with pipe:
            for line in iter(pipe.readline, b""):
                queue.put((pipe_name, line))
    finally:
        queue.put(None)


# This function invokes the C code to calculate a cartogram for a given gen and area input.
# It returns a generator that yields its output on stdout and stderr in the format:
#
#   source, line
#
# where source is a string (either 'stdout' or 'stderr'), and line is a string.
#
# It takes as input:
#
# area_data:            A string containing appropriately formated area data
# gen_file:             A string containing the path to the appropriate .gen file
def run_binary(gen_path, area_data_path, custom_flags=[]):
    cartogram_exec = os.path.join(os.path.dirname(__file__), "cartogram")
    validate_options(custom_flags)

    gen_path = util.get_safepath(gen_path)
    if not os.path.isfile(gen_path):
        raise CartogramError(f"Invalid boundary file path: {gen_path}")

    args = [cartogram_exec, gen_path, "--redirect_exports_to_stdout"] + custom_flags

    area_data_path = (
        util.get_safepath(area_data_path) if area_data_path is not None else ""
    )
    if os.path.isfile(area_data_path):
        args.append(area_data_path)

    cartogram_process = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    q = Queue()
    threading.Thread(
        target=reader, args=[cartogram_process.stdout, "stdout", q]
    ).start()
    threading.Thread(
        target=reader, args=[cartogram_process.stderr, "stderr", q]
    ).start()

    # Terminate after 300 seconds
    timer = threading.Timer(300, cartogram_process.terminate)
    timer.start()
    try:
        for _ in range(2):
            for source, line in iter(q.get, None):
                yield source, line
    finally:
        timer.cancel()

    # output, errors = cartogram_process.communicate(bytes(area_data, 'UTF-8'))

    # return io.StringIO(output.decode())


def validate_options(options):
    """Validate that an array contains only allowed options.

    Args:
        options: List of strings to validate

    Returns:
        bool: True if all options are valid, False otherwise
    """
    allowed_options = {
        "--output_equal_area_map",
        "--world",
        "--output_shifted_insets",  # Note: There might be a typo here ("shifted" vs "shifted")
        "--skip_projection",
        "--area",
    }

    i = 0
    n = len(options)

    while i < n:
        option = options[i]

        # Check if the option is one of the allowed ones
        if option not in allowed_options:
            raise CartogramError(f"Invalid cartogram option: {option}")

        # If the option is --area, the next element can be arbitrary text that is safe for filename
        if option == "--area" and i + 1 < n:
            if not options[i + 1] == util.sanitize_filename(options[i + 1]):
                raise CartogramError(f"Invalid cartogram option: {options[i + 1]}")
            i += 1

        i += 1
