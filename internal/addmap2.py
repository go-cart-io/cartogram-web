import sys
import os
import csv
import json
import shutil
import geojson_extrema
import cartwrap
import mappackify
import random
import string
import redis
import settings
import awslambda
import threading
import queue


def get_random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(length))


def print_welcome():

    print("Welcome to the Add Map Wizard!")
    print()


def print_usage():

    print("Usage: ")
    print()
    print("init [map-name]\t\tStart the process of adding a new map")

def cleanup(map_name):
    try:
        with open("web.py", "r") as web_py_file:
            include_str = "from handlers import {}".format(map_name)
            handlers_str = "'{0}': {0}.CartogramHandler(),".format(map_name)
            web_py_contents = web_py_file.read()
            web_py_contents.replace(include_str, "")
            web_py_contents.replace(handlers_str, "")

        if os.path.exists("handlers/{}.py".format(map_name)):
            os.remove("handlers/{}.py".format(map_name))

        if os.path.exists("{}.svg".format(map_name)): 
            os.remove("{}.svg".format(map_name))            
        
        with open("web.py", "w") as web_py_file:
            web_py_file.write(web_py_contents)
            
    except OSError:
        pass

    if os.path.exists("static/cartdata/{}".format(map_name)):
        shutil.rmtree("static/cartdata/{}".format(map_name), ignore_errors=True)
    
def init(map_name):  

    if os.path.exists("handlers/{}.py".format(map_name)) or os.path.exists("static/cartdata/{}".format(map_name)):
        is_overwrite = input(("It looks like a map with the name '{}' already exists. Do you want to overwrite (y/N): ").format(map_name))
        if (is_overwrite != 'y' and is_overwrite != 'Y'):
            print('End the process.')
            return

    user_friendly_name = input(("Enter a user friendly name for this map ({}): ").format(map_name)) or map_name

    print()
    print("Now I need to know where the .json and .csv files for this map are located. These files should be located in the CARTOGRAM_DATA_DIR directory. You should supply me with a path relative to CARTOGRAM_DATA_DIR.")
    print("E.G: The .json file for this map is located at CARTOGRAM_DATA_DIR/map.json. Enter \"map.json\".")
    print()

    map_gen_path = input(("Enter the location of the .json file for this map ({}.geojson): ").format(map_name)) or user_friendly_name + ".geojson"
    map_dat_path = input(("Enter the location of the .csv file for this map ({}.csv): ").format(map_name)) or user_friendly_name + ".csv"

    if not os.path.exists("{}/{}".format(os.environ["CARTOGRAM_DATA_DIR"], map_gen_path)):
        print("Error: It looks like the file {}/{} does not exist.".format(
            os.environ["CARTOGRAM_DATA_DIR"], map_gen_path))
        return

    if not os.path.exists("{}/{}".format(os.environ["CARTOGRAM_DATA_DIR"], map_dat_path)):
        print("Error: It looks like the file {}/{} does not exist.".format(
            os.environ["CARTOGRAM_DATA_DIR"], map_dat_path))
        return

    if not os.path.exists("static/cartdata/{}".format(map_name)):
        os.mkdir("static/cartdata/{}".format(map_name))

    region_identifier = input("What are the regions of this map called (e.g. State, Province) (Region)? ") or "Region"
    dataset_names = input("What is the name of datasets. Note that only letter with no space is allowed and "
                          "it should match collumn name is .csv file. Use comma to separate each dataset (Area,Population)? ") or "Area,Population"
    name_array = dataset_names.split(",")
    unit_names = input("What is unit of each dataset, in order (km.sq.,people)? ") or "km.sq.,people"
    unit_array = unit_names.split(",")    

    regions = []
    with open("{}/{}".format(os.environ["CARTOGRAM_DATA_DIR"], map_dat_path), newline='') as dat_file:
        reader = csv.DictReader(dat_file)
        for row in reader:
            region = {
                "id": row["Id"],
                "name": row["Name"],
                "abbreviation": row["Abbreviation"],
                "color": row["Color"],
                "labelX": float(row["Label.X"]),
                "labelY": float(row["Label.Y"])
            }
            for name in name_array:
                region[name] = float(row[name])
            regions.append(region)

    write_handler(map_name, user_friendly_name, map_gen_path, regions, region_identifier)
    write_config(map_name, name_array)
    write_abbr(map_name, regions)
    write_colors(map_name, regions)
    write_template(map_name, regions, region_identifier, name_array[0])
    write_labels(map_name, regions)
    write_grid(map_name, user_friendly_name, regions, region_identifier, name_array[0])

    print()
    print("I will now generate the map and cartogram. This may take a moment.")
    print()

    for i in range(len(name_array)):
        if (name_array[i] == "Area"):
            write_area(map_gen_path, map_name, regions, name_array[i], unit_array[i])
        else:
            write_cartogram(map_gen_path, map_name, regions, name_array[i], unit_array[i])

    print("Generating map pack in static/cartdata/{}/mappack.json...".format(map_name))
    mappackify.mappackify(map_name, name_array)    

    modify_webpy(map_name)

    print()
    print("All done!")
    print()

def write_handler(map_name, user_friendly_name, map_gen_path, regions, region_identifier):
    handler_py_template = '''import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "{0}"

    def get_gen_file(self):
        return "{{}}/{1}".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != {2}:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
{3}""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "{4}", 0, 1, 2, 3, [{5}], [0.0 for i in range(0,{2})], {{{6}}})
'''

    area_data_template = "\n".join(list(map(lambda region: "{},{{}},{},{}".format(
        region["id"], region["name"], ""), regions)))
    region_names = ",".join(
        list(map(lambda region: '"{}"'.format(region["name"]), regions)))
    region_name_id_dict = ",".join(list(
        map(lambda region: '"{}":"{}"'.format(region["name"], region["id"]), regions)))

    handler_py = handler_py_template.format(user_friendly_name, map_gen_path, len(
        regions), area_data_template, region_identifier, region_names, region_name_id_dict)

    print("Writing handlers/{}.py...".format(map_name))

    with open("handlers/{}.py".format(map_name), "w") as handler_file:
        handler_file.write(handler_py)  

def write_config(map_name, dataname_array):
    print("Writing static/cartdata/{}/config.json...".format(map_name))
    with open("static/cartdata/{}/config.json".format(map_name), "w") as config_json_file:
        config = {
            "dont_draw": [],
            "elevate": [],
            "data_names": dataname_array
        }
        json.dump(config, config_json_file)
                               
def write_abbr(map_name, regions):
    print("Writing static/cartdata/{}/abbreviations.json...".format(map_name))
    with open("static/cartdata/{}/abbreviations.json".format(map_name), "w") as abbreviations_json_file:
        abbreviations_json_file.write("{\n")
        abbreviations_json_file.write(",\n".join(list(map(
            lambda region: '"{}":"{}"'.format(region["name"], region["abbreviation"]), regions))))
        abbreviations_json_file.write("\n}")

def write_colors(map_name, regions):
    print("Writing static/cartdata/{}/colors.json...".format(map_name))
    with open("static/cartdata/{}/colors.json".format(map_name), "w") as colors_json_file:
            colors_json_file.write("{\n")
            colors_json_file.write(",\n".join(
                list(map(lambda region: '"id_{}":"{}"'.format(region["id"], region["color"]), regions))))
            colors_json_file.write("\n}")

def write_template(map_name, regions, region_identifier, base_region_name):
    print("Writing static/cartdata/{}/template.csv...".format(map_name))
    with open("static/cartdata/{}/template.csv".format(map_name), "w") as template_csv_file:
        template_csv_file.write('"{}","{}","Data","Colour"\n'.format(
            region_identifier, base_region_name))
        template_csv_file.write("\n".join(list(map(
            lambda region: '"{}","{}","","{}"'.format(region["name"], region[base_region_name], region["color"]), regions))))

def write_labels(map_name, regions,):
    print("Writing static/cartdata/{}/labels.json...".format(map_name))
    with open("static/cartdata/{}/labels.json".format(map_name), "w") as labels_json_file:
            labels_json_file.write('{"scale_x": 1, "scale_y": 1, "skipSVG": true, "labels": [')
            labels_json_file.write(",\n".join(list(map(
                lambda region: '{{"text": "{}", "x": {}, "y": {}}}'.format(region["abbreviation"], region["labelX"], region["labelY"]), regions))))
            labels_json_file.write('\n], "lines": []}')

def write_grid(map_name, user_friendly_name, regions, region_identifier, base_region_name):
    print("Writing static/cartdata/{}/griddocument.json...".format(map_name))
    with open("static/cartdata/{}/griddocument.json".format(map_name), "w") as griddocument_json_file:
        grid_document = {
            'name': user_friendly_name, 
            'width': 4, 
            'height': len(regions), 
            'edit_mask': [{'row': None, 'col': 0, 'editable': False}, {'row': None, 'col': 1, 'editable': False}, {'row': 0, 'col': None, 'editable': False}, {'row': None, 'col': 3, 'type': 'color'}, {'row': None, 'col': 2, 'type': 'number', 'min': 0, 'max': None}, {'row': 0, 'col': None, 'type': 'text'}, {'row': 0, 'col': 2, 'editable': True}], 
            'contents': [region_identifier, base_region_name, 'User Data', 'Colour']}
        
        for row in regions:
            grid_document['contents'].extend([row["name"], row[base_region_name], "", row["color"]])

        json.dump(grid_document, griddocument_json_file)

def write_area(map_gen_path, map_name, regions, data_name, data_unit):
    print("Generating conventional map...")
    with open("{}/{}".format(os.environ["CARTOGRAM_DATA_DIR"], map_gen_path), "r") as map_gen_file:
        original_json = json.load(map_gen_file)
        original_json['tooltip'] = {
            "label": data_name,
            "unit": data_unit,
            "data": {}
        }

        for row in regions:
            id_key = 'id_{}'.format(row["id"])
            tooltip_data = {
                "name": row["name"], 
                "value": row[data_name]
            }
            original_json['tooltip']['data'][id_key] = tooltip_data
    
    print("Writing static/cartdata/{}/{}.json...".format(map_name, data_name))
    with open("static/cartdata/{}/{}.json".format(map_name, data_name), "w") as original_json_file:
            json.dump(original_json, original_json_file)

def write_cartogram(map_gen_path, map_name, regions, data_name, data_unit):
    print(("Generating {} map...").format(data_name))
    print("Making request to AWS Lambda function at {}.".format(settings.CARTOGRAM_LAMBDA_URL))
    cartogram_data = 'name,Data,Color\n' + ("\n".join(list(map(
        lambda region: '{},{},{}'.format(region["name"], region[data_name], region["color"]), regions))))  

    map_gen_file_path = "{}/{}".format(os.environ["CARTOGRAM_DATA_DIR"], map_gen_path)

    def serverless_generate():

        redis_conn = redis.Redis(
            host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0)
        q = queue.Queue()
        unique_key = get_random_string(50)

        def downloader_worker():
            lambda_result = awslambda.generate_cartogram(cartogram_data,
                                                        map_gen_file_path, settings.CARTOGRAM_LAMBDA_URL,
                                                        settings.CARTOGRAM_LAMDA_API_KEY, unique_key)
            print(lambda_result)
            cartogram_gen_output = lambda_result['stdout']

            q.put(cartogram_gen_output)

        threading.Thread(target=downloader_worker(), daemon=True).start()

        current_stderr = ""
        current_progress_level = None
        gen_output = ""

        while True:
            current_progress = redis_conn.get(
                "cartprogress-{}".format(unique_key))

            if current_progress == None:
                pass
            else:
                current_progress = json.loads(current_progress.decode())
                if current_progress['progress'] != current_progress_level:
                    to_print = current_progress['stderr'].replace(
                        current_stderr, "")
                    for line in to_print.split("\n"):
                        print("Generating {} map: {}".format(
                            data_name, line), flush=True)
                    current_stderr = current_progress['stderr']
                    current_progress_level = current_progress['progress']

            try:
                gen_output = q.get(False, timeout=0.1)
                break
            except queue.Empty:
                pass

        current_progress = redis_conn.get(
            "cartprogress-{}".format(unique_key))

        if current_progress == None:
            pass
        else:
            current_progress = json.loads(current_progress.decode())
            if current_progress['progress'] != current_progress_level:
                to_print = current_progress['stderr'].replace(
                    current_stderr, "")
                for line in to_print.split("\n"):
                    print("Generating {} map: {}".format(
                        data_name, line), flush=True)
        
        return json.loads(gen_output)

    def self_generate():

        gen_output_lines = []

        for source, line in cartwrap.generate_cartogram(cartogram_data, map_gen_file_path, os.environ["CARTOGRAM_EXE"]):

            if source == "stdout":
                gen_output_lines.append(line.decode().strip())
            else:
                print("Generating {} map: {}".format(
                    data_name, line.decode().strip()))

        gen_output = "\n".join(gen_output_lines)
        return json.loads(gen_output)

    cartogram_json = serverless_generate(
    ) if settings.CARTOGRAM_LOCAL_DOCKERIZED else self_generate()

    # Calculate the bounding box if necessary
    if "bbox" not in cartogram_json:
        cartogram_json["bbox"] = geojson_extrema.get_extrema_from_geojson(
            cartogram_json)

    cartogram_json['tooltip'] = {
        "label": data_name,
        "unit": data_unit,
        "data": {}
    }

    for row in regions:
        id_key = 'id_{}'.format(row["id"])
        tooltip_data = {
            "name": row["abbreviation"], 
            "value": row[data_name]
        }
        cartogram_json['tooltip']['data'][id_key] = tooltip_data

    print()
    print("I will now finish up writing the map data files.")
    print()

    print("Writing static/cartdata/{}/{}.json...".format(map_name, data_name))
    with open("static/cartdata/{}/{}.json".format(map_name, data_name), "w") as original_json_file:
        json.dump(cartogram_json, original_json_file)

def modify_webpy(map_name):
    with open("web.py", "r") as web_py_file:
        include_str = "from handlers import {}".format(map_name)
        web_py_contents = web_py_file.read()
        if include_str in web_py_contents:
            print("There is already the handler in web.py, skip modifying web.py.")
        else:
            print()
            print("I will now modify web.py to add your new map. Before I do this, I will back up the current version of web.py to web.py.bak.")
            print()

            print("Backing up web.py...")
            shutil.copy("web.py", "web.py.bak")

            web_py_lines = web_py_contents.split("\n")
            web_py_new_lines = []
            found_header = False
            found_body = False
            for line in web_py_lines:

                if line.strip() == "# ---addmap.py header marker---":

                    web_py_new_lines.append(
                        "from handlers import {}".format(map_name))
                    web_py_new_lines.append("# ---addmap.py header marker---")
                    found_header = True
                elif line.strip() == "# ---addmap.py body marker---":

                    web_py_new_lines.append(
                        "'{0}': {0}.CartogramHandler(),".format(map_name))
                    web_py_new_lines.append("# ---addmap.py body marker---")
                    found_body = True
                else:
                    web_py_new_lines.append(line)

            if not found_header or not found_body:
                print(
                    "I was not able to find the appropriate markers that allow me to modify the web.py file.")
                return

            with open("web.py", "w") as web_py_file:
                web_py_file.write("\n".join(web_py_new_lines))

print_welcome()

if len(sys.argv) < 3:
    print_usage()
    sys.exit(1)

if sys.argv[1] == "init":
    init(sys.argv[2])
elif sys.argv[1] == "cleanup":
    cleanup(sys.argv[2])
else:
    print_usage()
    sys.exit(1)
