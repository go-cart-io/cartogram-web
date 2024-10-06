import sys
import os
import csv
import json
import shutil
import random
import string
import uuid
import settings
import awslambda
from shapely.geometry import shape


def get_random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(length))


def print_welcome():

    print("Welcome to the Add Map Wizard! Please refer to docs/addmap/addmap.md for the proper format of required files.")
    print()


def print_usage():

    print("Usage: ")
    print()
    print("init [map-name]\t\tStart the process of adding a new map")


def init(map_name):
    print()
    folder = f"static/cartdata/{map_name}"
    if not os.path.exists(folder):
        os.mkdir(folder)
        print("We create the folder {} for you. Please put original.json and data.csv files in the folder.".format(folder))

    map_gen_path = "{}/original.json".format(folder)
    map_dat_path = "{}/data.csv".format(folder)

    if not os.path.exists(map_gen_path):
        print("Error: It looks like the file {} does not exist.".format(map_gen_path))
        return

    if not os.path.exists(map_dat_path):
        print("Error: It looks like the file {} does not exist.".format(map_dat_path))
        return  

    print()
    print("I will now generate the cartograms. This may take a moment.")
    print()

    with open(map_dat_path, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        data = {
            "values": {
                "fields": [{"key": str(i), "label": header} for i, header in enumerate(headers)],
                "items": {}
            },
            "persist": "true"
        }
        for i, row in enumerate(reader, start=1):
            data["values"]["items"][str(i)] = row

    awslambda.generate_cartogram(data, map_gen_path, str(uuid.uuid4()), folder, True)

    print()
    print("Suscessfully generated cartograms.")
    print()

    user_friendly_name = input(("Enter a user friendly name for this map ({}): ").format(map_name)) or map_name
    region_identifier = input("What are the regions of this map called (e.g. State, Province) (Region)? ") or "Region"
    regions = get_regions_from_file(map_gen_path)
    
    modify_handler(map_name, user_friendly_name, map_gen_path, region_identifier, regions)

    print()
    print("All done!")
    print()

def get_regions_from_file(map_gen_path):
    regions = {}
    with open(map_gen_path, 'r') as file:
        geojson_data = json.load(file)
        for feature in geojson_data['features']:
            regions[feature['properties']['name']] = str(feature['properties']['cartogram_id'])

    return regions

def modify_handler(map_name, user_friendly_name, map_gen_path, region_identifier, region_name_id_dict):
    with open("handler_metadata.py", "r") as handler_metadata_py_file:
        handler_metadata_py_contents = handler_metadata_py_file.read()

        print()
        print("I will now modify handler_metadata.py to add your new map. Before I do this, I will back up the current version of handler_metadata.py to handler_metadata.py.bak.")
        print()

        print("Backing up handler_metadata.py...")
        shutil.copy("handler_metadata.py", "handler_metadata.py.bak")

        web_py_lines = handler_metadata_py_contents.split("\n")
        web_py_new_lines = []
        found_header = False
        for line in web_py_lines:

            if line.strip() == "# ---addmap.py header marker---":
                web_py_new_lines.append("# ---addmap.py header marker---")
                web_py_new_lines.append(
                    "'" + map_name + "': {'name':'" + user_friendly_name + 
                    "', 'region_identifier':'" + region_identifier +
                    "', 'file':'" + map_gen_path +
                    "', 'regions':" + str(region_name_id_dict) + "},")                
                found_header = True
            else:
                web_py_new_lines.append(line)

        if not found_header:
            print(
                "I was not able to find the appropriate markers that allow me to modify the handler_metadata.py file.")
            return

        with open("handler_metadata.py", "w") as handler_metadata_py_file:
            handler_metadata_py_file.write("\n".join(web_py_new_lines))

print_welcome()

if len(sys.argv) < 3:
    print_usage()
    sys.exit(1)

if sys.argv[1] == "init":
    init(sys.argv[2])
else:
    print_usage()
    sys.exit(1)
