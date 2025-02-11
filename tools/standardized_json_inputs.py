# To add EPSG:cartesian to all projected maps
# Hard code since it should be run only once

import sys
import os
import json
import shutil
import geopandas

sys.path.append(os.path.join(os.path.dirname(__file__), '../internal'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../internal/executable'))

import util

directory = "../internal/static/cartdata/"
WGS84_files = ['algeria', 'angola', 'arab_league', 'asean', 'cambodia', 'colombia', 
            'domrep', 'ethiopia', 'indonesia', 'israel3', 'laos', 'libya', 'malaysia', 
            'mexico', 'myanmar', 'nepal', 'newZealand', 'phl', 'saudiArabia', 'singaporePA', 
            'southAfrica', 'sudan', 'thailand', 'vietnam', 'world', 'yemen']
WGS84_files_same_geographic = ['algeria', 'angola', 'arab_league', 'cambodia', 'colombia', 
            'domrep', 'ethiopia', 'indonesia', 'israel3', 'laos', 'libya', 'malaysia', 
            'mexico', 'myanmar', 'nepal', 'newZealand', 'phl', 'saudiArabia', 'singaporePA', 
            'southAfrica', 'sudan', 'thailand', 'vietnam', 'yemen']
# Just 'asean', 'world' that need spacial processing

for root, dirs, files in os.walk(directory):
    for dir_name in dirs:
        dir_path = os.path.join(root, dir_name)
        print(dir_name)
        if not dir_name in WGS84_files:
            geojson = util.clean_and_sort_geojson(f"{dir_path}/Geographic Area.json", 'Region')
            geojson['crs'] = {
                "type": "name",
                "properties": {
                    "name": "EPSG:cartesian"
                }
            }
            geojson['properties'] = {
                "note": "Created from go-cart.io with custom projection, not in EPSG:4326."
            }
            with open(f"{dir_path}/Input.json", "w") as file:
                file.write(json.dumps(geojson))
        
        elif dir_name in WGS84_files_same_geographic:
            shutil.copy(f"{dir_path}/Geographic Area.json", f"{dir_path}/Input.json")
            util.clean_and_sort_geojson(f"{dir_path}/Input.json", 'Region', True)
            gdf = geopandas.read_file(f"{dir_path}/Input.json")
            if 'label' in  gdf.columns:
                gdf['label'] = gdf['label'].apply(json.loads)                
            geojson = gdf.to_json(show_bbox = True, to_wgs84 = True)
            with open(f"{dir_path}/Input.json", 'w') as outfile:
                outfile.write(geojson)

        elif dir_name == 'asean':
            gdf = geopandas.read_file(f"{dir_path}/Input.json")
            util.clean_and_sort_geojson(f"{dir_path}/Input.json", 'NAME_0', True)

        elif dir_name == 'world':
            gdf = geopandas.read_file(f"{dir_path}/Input.json")
            util.clean_and_sort_geojson(f"{dir_path}/Input.json", 'name_1', True)