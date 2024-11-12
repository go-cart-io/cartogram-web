import json
import os
import re
import redis
import uuid
import geopandas
import mapclassify
import pandas as pd
from math import log
from io import StringIO

import settings
import util
from executable import cartwrap
from shapely.geometry import shape

def get_representative_point(geometry):
    point = geometry.representative_point()
    return {'x': point.x, 'y': point.y}

def preprocess(file):
    if isinstance(file, str):
        gdf = geopandas.read_file(file)    
    else:
        file_path = os.path.join('/tmp', file.filename)
        file.save(file_path)
        gdf = geopandas.read_file(file_path)    
        os.remove(file_path)

    unique_columns = []
    gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    for column in gdf.columns:
        if column == 'geometry':
            continue
        gdf[column] = util.convert_col_to_serializable(gdf[column])
        if gdf[column].is_unique:
            unique_columns.append(column)

    minx, miny, maxx, maxy = gdf.total_bounds
    # The map is not projected so project it
    if minx >= -180.0 and maxx <= 180.0 and miny >= -90.0 and maxy <= 90.0:
        gdf = gdf.to_crs("epsg:6933")
        gdf['Land Area (sq.km.)'] = gdf.area
    
    gdf['ColorGroup'] = mapclassify.greedy(gdf, min_colors=6)
    gdf['cartogram_id'] = range(1, len(gdf) + 1)
    gdf['label'] = gdf.geometry.apply(get_representative_point)

    return { 'geojson': gdf.to_json(), 'unique': unique_columns }


def generate_cartogram(data, gen_file, cartogram_key, folder, print_progress = False, flags = ''):
    if 'csv' in data:
        datacsv = data['csv']
    else:
        datacsv = util.get_csv(data)

    util.sort_geojson(gen_file, data.get('geojson', None))

    datacsv, datasets, is_area_as_base = process_data(datacsv, gen_file)
    data_length = len(datasets)

    world = False
    with open(gen_file, 'r') as gen_fp:
        gen_file_contents = gen_fp.read()       
        conventional_json = json.loads(gen_file_contents)        
        if 'extent' in conventional_json and conventional_json['extent'] == 'world':
            world = True

    if 'persist' in data:
        with open('{}/data.csv'.format(folder), 'w') as outfile:
            outfile.write(datacsv)

    for i, dataset in enumerate(datasets):
        datastring = dataset['datastring']
        name = dataset['label']
        data_flags = flags        
            
        lambda_event = {
            'gen_file': gen_file,
            'area_data': datastring,
            'key': cartogram_key,
            'flags': data_flags,
            'world': world
        }

        lambda_result = local_function(lambda_event, i, data_length, print_progress)
        
        cartogram_gen_output = lambda_result['stdout']
        cartogram_json = json.loads(cartogram_gen_output)

        cartogram_json = cartogram_json["Original"]

        for feature in cartogram_json["features"]:
            geom = shape(feature["geometry"])
            point = geom.representative_point()
            feature['properties']['label'] = {'x': point.x, 'y': point.y}

        if 'persist' in data:
            with open('{}/{}.json'.format(folder, name), 'w') as outfile:
                outfile.write(json.dumps(cartogram_json))

        if is_area_as_base == False and i == 0:
            gen_file = '{}/{}.json'.format(folder, name)

    return

def process_data(csv_string, geojson_file):
    df = pd.read_csv(StringIO(csv_string))
    df.columns = [util.sanitize_filename(col) for col in df.columns]
    df['Color'] = df['Color'] if 'Color' in df else None
    df['Inset'] = df['Inset'] if 'Inset' in df else None
    is_empty_color = df['Color'].isna().all()

    df = df.sort_values(by='Region')    

    datasets = []
    is_area_as_base = False
    for column in df.columns:
        if column.startswith('Land Area'):
            is_area_as_base = True
        if column not in ['Region', 'Abbreviation', 'Color', 'ColorGroup', 'Inset'] and not column.startswith('Land Area'):
            m = re.match(r'(.+)\s?\((.+)\)$', column)
            if m:
                name = m.group(1).strip()      
            else:
                name = column.strip()
            
            df[column] = pd.to_numeric(df[column], errors='coerce')
            dataset = df[["Region", column, "Color", "Inset"]]
            datasets.append({'label': name, 'datastring': 'name,Data,Color,Inset\n{}'.format(dataset.to_csv(header=False, index=False))})

    if is_empty_color and not 'ColorGroup' in df:
        geo_data = geopandas.read_file(geojson_file)
        geo_data = geo_data.to_crs("epsg:6933")
        df.rename(columns={"Color": "ColorGroup"}, inplace=True)
        df["ColorGroup"] = mapclassify.greedy(geo_data, min_colors=6, balance="distance")
    elif not is_empty_color:
        df['Color'] = df['Color'].fillna('#fff')

    return df.to_csv(index=False), datasets, is_area_as_base
   
def local_function(params, data_index = 0, data_length = 1, print_progress = False):
    stdout = ''
    stderr = 'Dataset {}/{}\n'.format(data_index + 1, data_length)
    order = 0

    cartogram_exec = 'cartogram'
    temp_filename = str(uuid.uuid4())
   
    area_data_path = '/tmp/{}.csv'.format(temp_filename)
    with open(area_data_path, 'w') as areas_file:
        areas_file.write(params['area_data'])

    if 'flags' in params.keys():
        flags = params['flags']
    else:
        flags = ''

    for source, line in cartwrap.generate_cartogram(area_data_path, params['gen_file'], 'executable/{}'.format(cartogram_exec), params['world'], flags):

        if source == 'stdout':
            stdout += line.decode()
        else:

            stderr_line = line.decode()
            stderr += line.decode()

            # From C++ executable, we directly get cartogram generation progress in percentage; whereas, for C executable
            # we get maximum absolute area error which we translate into progress percentage.
            
            s = re.search(r'Progress: (.+)', line.decode())

            if s != None:
                current_progress = float(s.groups(1)[0])

                if current_progress == 1 and data_index == data_length - 1: # To prevent stucking at 0.99999
                    current_progress = 1
                else:
                    current_progress = (current_progress / data_length) + (data_index / data_length)

                if print_progress:
                    print('{}%'.format(current_progress * 100))
                                    
                setprogress({
                    'key': params['key'],
                    'progress': current_progress,
                    'stderr': stderr,
                    'order': order
                })

                order += 1
    
    if os.path.exists('/tmp/{}.csv'.format(temp_filename)):
        os.remove('/tmp/{}.csv'.format(temp_filename))

    return {'stderr': stderr, 'stdout': stdout}

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