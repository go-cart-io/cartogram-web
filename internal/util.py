import re
import json
import os

def sanitize_filename(filename):    
    invalid_chars = r'[\\/:*?"<>|]'
    sanitized_filename = re.sub(invalid_chars, '_', filename)
    return sanitized_filename

def get_csv(data):
    fields = data['values']['fields']
    items = data['values']['items']
    
    header = ','.join([field['label'] for field in fields])

    rows = []
    for key, item in items.items():
        row = ','.join(str(value) for value in item)
        rows.append(row)

    return f'{header}\n' + '\n'.join(rows)

def sort_geojson(path, geojson_data = None):
    if os.path.isfile(path):
        with open(path, 'r') as geojson_file:
            geojson_data = json.load(geojson_file)
        
    sorted_geojson_features = sorted(geojson_data['features'], key=lambda x: x['properties']['name'])

    with open(path, 'w') as sorted_geojson_file:
        geojson_data['features'] = sorted_geojson_features
        json.dump(geojson_data, sorted_geojson_file)