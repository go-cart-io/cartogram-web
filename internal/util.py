import re
import json
import geopandas

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

def clean_geojson(json_path, region_col, inplace=False):
    gdf = geopandas.read_file(json_path)

    if region_col != 'Region':
        if 'Region' in gdf.columns:
            gdf = gdf.drop(columns=['Region'])
        gdf = gdf.rename(columns={region_col: 'Region'})

    gdf = gdf.sort_values(by='Region')
    area_columns = [col for col in gdf.columns if col.startswith('Geographic Area')]
    columns_to_keep = ['Region', 'label', 'cartogram_id', 'geometry'] + area_columns
    existing_columns = [col for col in columns_to_keep if col in gdf.columns]
    gdf = gdf[existing_columns]

    if 'label' in gdf.columns:
        gdf['label'] = gdf['label'].apply(json.loads)

    geojson = json.loads(gdf.to_json())
    geojson['crs'] = {
        "type": "name",
        "properties": {
        "name": "EPSG:cartesian"
        }
    }

    if inplace:
        with open(json_path, 'w') as outfile:
            outfile.write(json.dumps(geojson))

    return geojson

def convert_col_to_serializable(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, OverflowError):
        return value.astype(str)