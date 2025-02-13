import subprocess
import threading
from queue import Queue

def reader(pipe, pipe_name, queue):
    try:
        with pipe:
            for line in iter(pipe.readline, b''):
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
# cartogram_executable: A string containg the path to the C code executable
def generate_cartogram(area_data, gen_file, cartogram_executable, custom_flags=[]):
    args = [cartogram_executable, '--redirect_exports_to_stdout']
    
    if custom_flags != []:
        args = args + custom_flags

    args = args + [gen_file]
    if not area_data == None:
        args.append(area_data)

    cartogram_process = subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    q = Queue()
    threading.Thread(target=reader,args=[cartogram_process.stdout, "stdout", q]).start()
    threading.Thread(target=reader,args=[cartogram_process.stderr, "stderr", q]).start()

    timer = threading.Timer(300, cartogram_process.terminate)  # Terminate after 300 seconds
    timer.start()
    try:
        for _ in range(2):
            for source, line in iter(q.get, None):
                yield source,line
    finally:
        timer.cancel()

    #output, errors = cartogram_process.communicate(bytes(area_data, 'UTF-8'))

    #return io.StringIO(output.decode())
