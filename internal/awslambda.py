import requests
import json
import os
import re
import redis
import settings
import uuid
from math import log
from lambda_package import cartwrap

def generate_cartogram(area_data, gen_file, lambda_url, lambda_api_key, cartogram_key, flags=''):

    headers = {
        'x-api-key': lambda_api_key
    }

    with open(gen_file, 'r') as gen_fp:
        gen_file_contents = gen_fp.read()

    lambda_event = {
        'gen_file': gen_file_contents,
        'area_data': area_data,
        'key': cartogram_key,
        'flags': flags
    }

    # Be careful, lambda function may not work anymore
    if lambda_url != None and lambda_url != '':
        r = requests.post(lambda_url, headers=headers, json=lambda_event)
        return r.json()
    
    else:        
        return local_function(lambda_event)
    
# similar to lambda_function.lambda_handler, but no overhead like json dump
def local_function(params):
    stdout = ""
    stderr = ""
    order = 0

    # We run C++ executable for most maps and old C excutable (named "cartogram_c") only for the World Map
    cartogram_exec = "cartogram"
    temp_filename = str(uuid.uuid4())
    map_data_filename = temp_filename + ".json"

    # The C code deduces from the map data file extension whether we have GeoJSON or .gen
    world = False
    try:
        conventional_json = json.loads(params["gen_file"])
        if "extent" in conventional_json.keys():
            if conventional_json['extent'] == "world":
                world = True
                cartogram_exec = "cartogram_c"
    except json.JSONDecodeError:
        map_data_filename = temp_filename + ".gen"

    with open("/tmp/{}".format(map_data_filename), "w") as conventional_map_file:
        conventional_map_file.write(params["gen_file"])

    if cartogram_exec == "cartogram":
        area_data_path = "/tmp/{}.csv".format(temp_filename)
        with open(area_data_path, "w") as areas_file:
            areas_file.write(params["area_data"])        
    else:
        area_data_path = params["area_data"]

    if "flags" in params.keys():
        flags = params["flags"]
    else:
        flags = ''

    for source, line in cartwrap.generate_cartogram(area_data_path, "/tmp/{}".format(map_data_filename), "{}/{}".format(os.environ['LAMBDA_TASK_ROOT'], cartogram_exec), world, flags):

        if source == "stdout":
            stdout += line.decode()
        else:

            stderr_line = line.decode()
            stderr += line.decode()

            # From C++ executable, we directly get cartogram generation progress in percentage; whereas, for C executable
            # we get maximum absolute area error which we translate into progress percentage.
            
            s = re.search(r'Progress: (.+)', line.decode())

            if cartogram_exec == "cartogram_c":
                s = re.search(r'max\. abs\. area error: (.+)', line.decode())

            if s != None:
                current_progress = float(s.groups(1)[0])

                if cartogram_exec == "cartogram_c":
                    current_progress = 1 / max(1 , log((current_progress/0.01), 5))
                
                # Prevents the progress bar from getting stuck at 100%
                if current_progress == 1.0:
                    current_progress = 0.95
                    
                setprogress({
                    'secret': os.environ['CARTOGRAM_PROGRESS_SECRET'],
                    'key': params['key'],
                    'progress': current_progress,
                    'stderr': stderr,
                    'order': order
                })

                order += 1
    
    if os.path.exists("/tmp/{}".format(map_data_filename)):
        os.remove("/tmp/{}".format(map_data_filename))
    if os.path.exists("/tmp/{}.csv".format(temp_filename)):
        os.remove("/tmp/{}.csv".format(temp_filename))

    return {"stderr": stderr, "stdout": stdout}

def setprogress(params):
    redis_conn = redis.Redis(host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0)
    current_progress = redis_conn.get('cartprogress-{}'.format(params['key']))

    if current_progress is None:
        current_progress = {
            'order': params['order'],
            'stderr': params['stderr'],
            'progress': params['progress']
        }
    else:
        current_progress = json.loads(current_progress.decode())

        if current_progress['order'] < params['order']:
            current_progress = {
                'order': params['order'],
                'stderr': params['stderr'],
                'progress': params['progress']
            }

    redis_conn.set('cartprogress-{}'.format(params['key']), json.dumps(current_progress))
    redis_conn.expire('cartprogress-{}'.format(params['key']), 300)

def getprogress(key):
    redis_conn = redis.Redis(host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0)
    current_progress = redis_conn.get('cartprogress-{}'.format(key))

    if current_progress == None:
        return {'progress': None, 'stderr': ''}
    else:
        current_progress = json.loads(current_progress.decode())
        return {'progress': current_progress['progress'], 'stderr': current_progress['stderr']}