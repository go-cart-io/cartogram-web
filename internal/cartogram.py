import json
import os
import re
import redis
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

def preprocess(input, mapDBKey='temp_filename'):    
    # Input can be anything that is supported by geopandas.read_file
    # Standardize input to geojson file path
    file_path = os.path.join("/tmp", f"{mapDBKey}.json")
    if isinstance(input, str): # input is path
        gdf = geopandas.read_file(input)    
    else: # input is file object
        input.save(file_path)
        gdf = geopandas.read_file(file_path)

    gdf = gdf[gdf.is_valid]
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])].reset_index(drop=True)

    # Get nesseary information
    unique_columns = []
    for column in gdf.columns:
        if column == 'geometry':
            continue
        gdf[column] = util.convert_col_to_serializable(gdf[column])
        if gdf[column].is_unique:
            unique_columns.append(column)

    # TODO - Project before preview and add Geographic Area calculation
    # gdf.to_crs("EPSG:6933", inplace=True) # NSIDC EASE-Grid 2.0 Global https://epsg.io/6933
    if not any(gdf.columns.str.startswith('Geographic Area')):
        gdf['Geographic Area (sq. km)'] = 0 #gdf.area / 10**6
    
    gdf['ColorGroup'] = mapclassify.greedy(gdf, min_colors=6, balance="distance")
    gdf['cartogram_id'] = range(1, len(gdf) + 1)
    gdf['label'] = gdf.geometry.apply(get_representative_point)
    geojson = gdf.to_json()

    with open(file_path, 'w') as outfile:
        outfile.write(geojson)

    return { 'geojson': geojson, 'unique': unique_columns }


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

        if is_area_as_base is True:
            equal_area_json = get_equal_area_map(cartogram_key, gen_file, datasets[0])
            if equal_area_json is not None:
                with open('{}/Geographic Area.json'.format(folder), 'w') as outfile:
                    outfile.write(json.dumps(equal_area_json))
    
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

        cartogram_result = local_function(lambda_event, i, data_length, print_progress)

        if (cartogram_result['stdout'] == ''):
            raise RuntimeError(f'Cannot generate cartogram for {name} - {cartogram_result['error_msg']}')
        
        cartogram_gen_output = cartogram_result['stdout']
        cartogram_gen_output_json = json.loads(cartogram_gen_output)
        cartogram_json = cartogram_gen_output_json["Original"]
        cartogram_json = postprocess_geojson(cartogram_json)

        if 'persist' in data:
            with open('{}/{}.json'.format(folder, name), 'w') as outfile:
                outfile.write(json.dumps(cartogram_json))

        # TODO check whether the code works properly if persist is false
        if is_area_as_base == False and i == 0:
            gen_file = '{}/{}.json'.format(folder, name)

    return

def process_data(csv_string, geojson_file):
    df = pd.read_csv(StringIO(csv_string))
    df.columns = [util.sanitize_filename(col) for col in df.columns]
    df['Color'] = df['Color'] if 'Color' in df else None
    df['Inset'] = df['Inset'] if 'Inset' in df else None
    is_empty_color = df['Color'].isna().all()
    is_empty_inset = df['Inset'].isna().all()

    datasets = []
    cols_order = ['Region', 'RegionLabel', 'Color', 'ColorGroup', 'Inset']
    is_area_as_base = False
    for column in df.columns:
        if column.startswith('Geographic Area'):
            cols_order.insert(5, column)
            is_area_as_base = True

        elif column not in ['Region', 'RegionLabel', 'Color', 'ColorGroup', 'Inset'] and not column.startswith('Geographic Area'):
            cols_order.append(column)
            m = re.match(r'(.+)\s?\((.+)\)$', column)
            if m:
                name = m.group(1).strip()      
            else:
                name = column.strip()
            
            df[column] = pd.to_numeric(df[column], errors='coerce')
            dataset = df[["Region", column, "Color", "Inset"]]
            datasets.append({'label': name, 'datastring': 'name,Data,Color,Inset\n{}'.format(dataset.to_csv(header=False, index=False))})

    if not 'ColorGroup' in df:
        geo_data = geopandas.read_file(geojson_file)
        geo_data = geo_data.to_crs("epsg:6933")
        df["ColorGroup"] = mapclassify.greedy(geo_data, min_colors=6, balance="distance")
    
    df = df.sort_values(by='Region')
    df = df.reindex(columns=cols_order)

    if is_empty_color:
        df.drop(columns = 'Color', inplace=True)
    
    if is_empty_inset:
        df.drop(columns = 'Inset', inplace=True)

    return df.to_csv(index=False), datasets, is_area_as_base

def get_equal_area_map(mapDBKey, file_path, dataset = None):
    result = local_function({
        'gen_file': file_path,
        'area_data': dataset['datastring'] if dataset else None,
        'key': mapDBKey,
        'flags': '--output_equal_area',
        'world': False
    })
    if result['error_msg'] != '' and result['error_msg'] != 'Input GeoJSON is not a longitude-latitude map. Therefore, it is not possible to produce an equal-area map.':
        raise RuntimeError(result['error_msg'])
    elif result['stdout'] == '':
        return None
    
    return postprocess_geojson(json.loads(result['stdout']))    

def postprocess_geojson(json_data):
    for feature in json_data["features"]:
        geom = shape(feature["geometry"])
        point = geom.representative_point()
        feature['properties']['label'] = {'x': point.x, 'y': point.y}

    if 'divider_points' in json_data:
        linestring = {
            "geometry": {
                "type": "MultiLineString",
                "coordinates": []
            },
            "properties": { "name": "Dividers" },
            "type": "Feature"
        }
        for line in json_data["divider_points"]:
            linestring["geometry"]["coordinates"].append([[line[0], line[1]], [line[2], line[3]]])
        json_data["features"].append(linestring)

    return json_data
   
def local_function(params, data_index = 0, data_length = 1, print_progress = False):
    stdout = ''
    stderr = 'Dataset {}/{}\n'.format(data_index + 1, data_length)
    error_msg = ''
    order = 0

    cartogram_exec = os.path.join(os.path.dirname(__file__), 'executable/cartogram')
    cartogram_key = params['key']
   
    if 'area_data' in params.keys() and params['area_data'] != None:
        area_data_path = '/tmp/{}.csv'.format(cartogram_key)
        with open(area_data_path, 'w') as areas_file:
            areas_file.write(params['area_data'])
    else:
        area_data_path = None

    if 'flags' in params.keys():
        flags = params['flags']
    else:
        flags = ''

    for source, line in cartwrap.generate_cartogram(area_data_path, params['gen_file'], cartogram_exec, params['world'], flags):

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
                    'key': cartogram_key,
                    'progress': current_progress,
                    'stderr': stderr,
                    'order': order
                })

                order += 1

            else:
                e = re.search(r'ERROR: (.+)', line.decode())
                if e != None:
                    error_msg = e.groups(1)[0]
    
    if os.path.exists('/tmp/{}.csv'.format(cartogram_key)):
        os.remove('/tmp/{}.csv'.format(cartogram_key))

    return {'stderr': stderr, 'stdout': stdout, 'error_msg': error_msg}

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