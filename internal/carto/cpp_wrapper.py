import json
import os
import re
import subprocess
import threading
from queue import Queue

from errors import CartoError
from utils import file_utils

from .progress import setprogress


def call_binary(mapDBKey, gen_path, area_data_path, flags=[], progress_options={}):
    data_name = progress_options.get("data_name", "")
    data_index = progress_options.get("data_index", 0)
    data_length = progress_options.get("data_length", 1)
    error_prefix = progress_options.get("error_prefix", "")
    stdout = ""
    stderr = "Dataset {}/{}\n".format(data_index + 1, data_length)
    error_msg = ""
    order = 0

    for source, line in run_binary(gen_path, area_data_path, flags):
        if source == "stdout":
            stdout += line.decode()
        else:
            stderr += line.decode()

            # From C++ executable, we directly get cartogram generation progress in percentage; whereas, for C executable
            # we get maximum absolute area error which we translate into progress percentage.

            s = re.search(r"Progress: (.+)", line.decode())

            if s is not None:
                current_progress = float(s.groups(1)[0])

                # To prevent stucking at 0.99999
                if current_progress == 1 and data_index == data_length - 1:
                    current_progress = 1
                else:
                    current_progress = (current_progress / data_length) + (
                        data_index / data_length
                    )

                if progress_options.get("print", False):
                    print("{}%".format(current_progress * 100))

                setprogress(
                    {
                        "key": mapDBKey,
                        "name": data_name,
                        "progress": current_progress,
                        "stderr": stderr,
                        "order": order,
                    }
                )

                order += 1

            else:
                e = re.search(r"ERROR: (.+)", line.decode())
                if e is not None:
                    error_msg = e.groups(1)[0]

    if error_msg != "":
        raise CartoError(f"{error_prefix} {error_msg}".strip())
    elif stdout == "":
        return None

    return json.loads(stdout)


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
    cartogram_exec = os.path.join(
        os.path.dirname(__file__), "..", "executable", "cartogram"
    )
    validate_options(custom_flags)

    gen_path = file_utils.get_safepath(gen_path)
    if not os.path.isfile(gen_path):
        raise CartoError(f"Invalid boundary file path: {gen_path}")

    args = [cartogram_exec, gen_path, "--redirect_exports_to_stdout"] + custom_flags

    area_data_path = (
        file_utils.get_safepath(area_data_path) if area_data_path is not None else ""
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


def reader(pipe, pipe_name, queue):
    try:
        with pipe:
            for line in iter(pipe.readline, b""):
                queue.put((pipe_name, line))
    finally:
        queue.put(None)


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
            raise CartoError(f"Invalid cartogram option: {option}")

        # If the option is --area, the next element can be arbitrary text that is safe for filename
        if option == "--area" and i + 1 < n:
            if not options[i + 1] == file_utils.sanitize_filename(options[i + 1]):
                raise CartoError(f"Invalid cartogram option: {options[i + 1]}")
            i += 1

        i += 1
