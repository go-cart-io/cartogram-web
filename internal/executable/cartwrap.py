import os
import subprocess
import threading
from queue import Queue

import util


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
def generate_cartogram(area_data, gen_file, custom_flags=[]):
    cartogram_exec = os.path.join(os.path.dirname(__file__), "cartogram")
    allowed_flags = {
        "--output_equal_area_map",
        "--world",
        "--output_shifted_insets",
        "--skip_projection",
    }
    validated_flags = [flag for flag in custom_flags if flag in allowed_flags]

    gen_file = util.get_safepath(gen_file)
    if not os.path.isfile(gen_file):
        raise ValueError(f"Invalid boundary file path: {gen_file}")

    args = (
        [cartogram_exec, "--redirect_exports_to_stdout"] + validated_flags + [gen_file]
    )

    area_data = util.get_safepath(area_data)
    if area_data is not None and os.path.isfile(area_data):
        args.append(area_data)

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

    timer = threading.Timer(
        300, cartogram_process.terminate
    )  # Terminate after 300 seconds
    timer.start()
    try:
        for _ in range(2):
            for source, line in iter(q.get, None):
                yield source, line
    finally:
        timer.cancel()

    # output, errors = cartogram_process.communicate(bytes(area_data, 'UTF-8'))

    # return io.StringIO(output.decode())
