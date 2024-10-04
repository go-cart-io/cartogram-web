import requests
import json
import os
import re
import redis
import settings
import uuid
import util
from math import log
from lambda_package import cartwrap
from shapely.geometry import shape

def generate_cartogram(data, gen_file, lambda_url, lambda_api_key, cartogram_key, flags=''):
    datacsv = util.get_csv(data)
    datasets = util.get_data_string(data)
    data_length = len(datasets)

    with open(gen_file, 'r') as gen_fp:
        gen_file_contents = gen_fp.read()
        
    # TODO cleanup if fail
    if 'persist' in data:
        os.mkdir('static/userdata/{}'.format(cartogram_key))
        with open('static/userdata/{}/data.csv'.format(cartogram_key), 'w') as outfile:
            outfile.write(datacsv)

    for i, dataset in enumerate(datasets):
        datastring = dataset['datastring']
        name = dataset['label']

        lambda_event = {
            'gen_file': gen_file_contents,
            'area_data': datastring,
            'key': cartogram_key,
            'flags': flags
        }

        lambda_result = local_function(lambda_event, i, data_length)

        cartogram_gen_output = lambda_result['stdout']
        cartogram_json = json.loads(cartogram_gen_output)

        if lambda_result['world'] == False:
            cartogram_json = cartogram_json['Original']

        for feature in cartogram_json["features"]:
            geom = shape(feature["geometry"])
            point = geom.representative_point()
            feature['properties']['label'] = {'x': point.x, 'y': point.y}

        if 'persist' in data:
            with open('static/userdata/{}/{}.json'.format(cartogram_key, name), 'w') as outfile:
                outfile.write(json.dumps(cartogram_json))

    return
   
# similar to lambda_function.lambda_handler, but no overhead like json dump
def local_function(params, data_index = 0, data_length = 1):
    stdout = ''
    stderr = 'Dataset {}/{}\n'.format(data_index + 1, data_length)
    order = 0

    # We run C++ executable for most maps and old C excutable (named 'cartogram_c') only for the World Map
    cartogram_exec = 'cartogram'
    temp_filename = str(uuid.uuid4())
    map_data_filename = temp_filename + '.json'

    # The C code deduces from the map data file extension whether we have GeoJSON or .gen
    world = False
    try:
        conventional_json = json.loads(params['gen_file'])
        if 'extent' in conventional_json.keys():
            if conventional_json['extent'] == 'world':
                world = True
                cartogram_exec = 'cartogram_c'
    except json.JSONDecodeError:
        map_data_filename = temp_filename + '.gen'

    with open('/tmp/{}'.format(map_data_filename), 'w') as conventional_map_file:
        conventional_map_file.write(params['gen_file'])

    if cartogram_exec == 'cartogram':
        area_data_path = '/tmp/{}.csv'.format(temp_filename)
        with open(area_data_path, 'w') as areas_file:
            areas_file.write(params['area_data'])        
    else:
        area_data_path = params['area_data']

    if 'flags' in params.keys():
        flags = params['flags']
    else:
        flags = ''

    for source, line in cartwrap.generate_cartogram(area_data_path, '/tmp/{}'.format(map_data_filename), '{}/{}'.format(os.environ['LAMBDA_TASK_ROOT'], cartogram_exec), world, flags):

        if source == 'stdout':
            stdout += line.decode()
        else:

            stderr_line = line.decode()
            stderr += line.decode()

            # From C++ executable, we directly get cartogram generation progress in percentage; whereas, for C executable
            # we get maximum absolute area error which we translate into progress percentage.
            
            s = re.search(r'Progress: (.+)', line.decode())

            if cartogram_exec == 'cartogram_c':
                s = re.search(r'max\. abs\. area error: (.+)', line.decode())

            if s != None:
                current_progress = float(s.groups(1)[0])

                if cartogram_exec == 'cartogram_c':
                    current_progress = 1 / max(1 , log((current_progress/0.01), 5))

                if current_progress == 1 and data_index == data_length - 1: # To prevent stucking at 0.99999
                    current_progress = 1
                else:
                    current_progress = (current_progress / data_length) + (data_index / data_length)
                                    
                setprogress({
                    'secret': os.environ['CARTOGRAM_PROGRESS_SECRET'],
                    'key': params['key'],
                    'progress': current_progress,
                    'stderr': stderr,
                    'order': order
                })

                order += 1
    
    if os.path.exists('/tmp/{}'.format(map_data_filename)):
        os.remove('/tmp/{}'.format(map_data_filename))
    if os.path.exists('/tmp/{}.csv'.format(temp_filename)):
        os.remove('/tmp/{}.csv'.format(temp_filename))

    return {'stderr': stderr, 'stdout': stdout, 'world': world}

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