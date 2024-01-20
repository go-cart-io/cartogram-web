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
import svg2color
import svg2labels
import svg2config
from shapely.geometry import shape


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
        if os.path.exists("{}.svg".format(map_name)): 
            os.remove("{}.svg".format(map_name))  
    
        with open("handler.py", "r") as handler_py_file:
            handlers_str = "'" + map_name + "': {'name':"
            web_py_contents = handler_py_file.read()
            web_py_lines = web_py_contents.split("\n")
            web_py_new_lines = []
            for line in web_py_lines:
                if not line.startswith(handlers_str):
                    web_py_new_lines.append(line)     
        
        with open("handler.py", "w") as handler_py_file:
            handler_py_file.write("\n".join(web_py_new_lines))
            
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

    map_gen_path = input(("Enter the location of the .json file for this map ({}.geojson): ").format(map_name)) or map_name + ".geojson"
    map_dat_path = input(("Enter the location of the .csv file for this map ({}.csv): ").format(map_name)) or map_name + ".csv"

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
    dataset_names = input("What is the name of datasets. Note that only letter with no space is allowed and it should match collumn name is .csv file. Use comma to separate each dataset (Area,Population)? ") or "Area,Population"
    name_array = dataset_names.split(",")
    unit_names = input("What is unit of each dataset, in order (km.sq.,people)? ") or "km.sq.,people"
    unit_array = unit_names.split(",")    
    labeling_scheme = input("What is the labelling scheme (1):\n 1. Auto labelling\n 2. Manual labelling\n 3. No label\n ? ") or "1"

    regions = get_regions_from_file(map_dat_path, name_array)
    map_gen_file_path = "{}/{}".format(os.environ["CARTOGRAM_DATA_DIR"], map_gen_path)

    write_config(map_name, name_array)
    write_abbr(map_name, regions)
    write_colors(map_name, regions)
    write_template(map_name, regions, region_identifier, name_array[len(name_array) - 1], unit_array[len(name_array) - 1])
    
    is_gen_label = False
    if os.path.exists("static/cartdata/{}/labels.json".format(map_name)): 
        os.remove("static/cartdata/{}/labels.json".format(map_name))
    if labeling_scheme == "1":    
        is_gen_label = True
    elif labeling_scheme == "2":
        gen_svg(map_gen_file_path, map_name, regions)
        

    print()
    print("I will now generate the map and cartogram. This may take a moment.")
    print()
    
    if (name_array[0] == "Area" or name_array[0] == "Land Area"):
        write_area(map_gen_file_path, map_name, regions, name_array[0], unit_array[0], is_gen_label)
    else:        
        write_cartogram(map_gen_file_path, map_name, regions, name_array[0], unit_array[0], is_gen_label, 'ts')

    new_map_gen_file_path = "static/cartdata/{}/{}.json".format(map_name, name_array[0])
    if len(name_array) > 1:
        for i in range(len(name_array))[1:]:
            write_cartogram(new_map_gen_file_path, map_name, regions, name_array[i], unit_array[i], is_gen_label)

    print("Generating map pack in static/cartdata/{}/mappack.json...".format(map_name))
    mappackify.mappackify(map_name, name_array)    

    modify_basejson(map_gen_file_path, regions)
    modify_handler(map_name, user_friendly_name, map_gen_path, region_identifier)

    print()
    print("All done!")
    print()


def get_regions_from_file(map_dat_path, name_array):
    regions = []
    with open("{}/{}".format(os.environ["CARTOGRAM_DATA_DIR"], map_dat_path), newline='') as dat_file:
        reader = csv.DictReader(dat_file)
        for row in reader:
            region = {
                "id": row["Id"],
                "name": row["Name"],
                "abbreviation": row["Abbreviation"],
                "color": row["Color"]
            }
            if "Label.X" in row and "Label.Y" in row:
                region["labelX"] = float(row["Label.X"])
                region["labelY"] = float(row["Label.Y"])
            for name in name_array:
                region[name] = float(row[name])
            regions.append(region)
    return regions


def find_region_by_id(regions, i):
    for region in regions:
        if region["id"] == i:
            return region
    
    return None


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


def write_template(map_name, regions, region_identifier, region_name, unit):
    print("Writing static/cartdata/{}/template.csv...".format(map_name))
    with open("static/cartdata/{}/template.csv".format(map_name), "w") as template_csv_file:
        template_csv_file.write('"{}","Colour","{} ({})"\n'.format(
            region_identifier, region_name, unit))
        template_csv_file.write("\n".join(list(map(
            lambda region: '"{}","{}","{}"'.format(region["name"], region["color"], region[region_name]), regions))))


def write_area(map_gen_file_path, map_name, regions, data_name, data_unit, is_gen_label):
    print("Generating conventional map...")
    with open(map_gen_file_path, "r") as map_gen_file:
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

        if is_gen_label:
            for feature in original_json["features"]:
                geom = shape(feature["geometry"])
                point = geom.representative_point()
                feature['properties']['repPt'] = [point.x, point.y]
    
    print("Writing static/cartdata/{}/{}.json...".format(map_name, data_name))
    with open("static/cartdata/{}/{}.json".format(map_name, data_name), "w") as original_json_file:
            json.dump(original_json, original_json_file)


def write_cartogram(map_gen_file_path, map_name, regions, data_name, data_unit, is_gen_label=False, flags=''):
    print(("Generating {} map...").format(data_name))
    print("Making request to AWS Lambda function at {}.".format(settings.CARTOGRAM_LAMBDA_URL))
    cartogram_data = 'cartogram_id,Region Data,Region Name,Inset\n' + ("\n".join(list(map(
        lambda region: '{},{},{},'.format(region["id"], region[data_name], region["name"]), regions))))   

    def serverless_generate():

        redis_conn = redis.Redis(
            host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0)
        q = queue.Queue()
        unique_key = get_random_string(50)

        def downloader_worker():
            lambda_result = awslambda.generate_cartogram(cartogram_data,
                                                        map_gen_file_path, settings.CARTOGRAM_LAMBDA_URL,
                                                        settings.CARTOGRAM_LAMDA_API_KEY, unique_key, flags)
            cartogram_gen_output = lambda_result['stdout']
            print("************")
            print(lambda_result['stderr'])
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
                    
        print("serverless")
        # print(gen_output)
        return json.loads(gen_output)

    def self_generate():

        gen_output_lines = []

        for source, line in cartwrap.generate_cartogram(cartogram_data, map_gen_file_path, os.environ["CARTOGRAM_EXE"], False, flags):

            if source == "stdout":
                gen_output_lines.append(line.decode().strip())
            else:
                print("Generating {} map: {}".format(
                    data_name, line.decode().strip()))

        gen_output = "\n".join(gen_output_lines)

        print("self")
        # print(gen_output)
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

    if is_gen_label:
        for feature in cartogram_json["features"]:
            geom = shape(feature["geometry"])
            point = geom.representative_point()
            feature['properties']['repPt'] = [point.x, point.y]

    print()
    print("I will now finish up writing the map data files.")
    print()

    print("Writing static/cartdata/{}/{}.json...".format(map_name, data_name))
    with open("static/cartdata/{}/{}.json".format(map_name, data_name), "w") as original_json_file:
        json.dump(cartogram_json, original_json_file)


def modify_basejson(map_gen_file_path, regions):
    print(("Updating {}...").format(map_gen_file_path))
    region_name_id_dict = {}
    for region in regions:
        region_name_id_dict[region["name"]] = region["id"]

    with open(map_gen_file_path, 'r') as openfile: 
        json_obj = json.load(openfile)
    json_obj['regions'] = region_name_id_dict
    with open(map_gen_file_path, "w") as outfile:
        outfile.write(json.dumps(json_obj))


def modify_handler(map_name, user_friendly_name, map_gen_path, region_identifier):
    with open("handler.py", "r") as handler_py_file:
        web_py_contents = handler_py_file.read()

        print()
        print("I will now modify handler.py to add your new map. Before I do this, I will back up the current version of handler.py to handler.py.bak.")
        print()

        print("Backing up handler.py...")
        shutil.copy("handler.py", "handler.py.bak")

        web_py_lines = web_py_contents.split("\n")
        web_py_new_lines = []
        found_header = False
        for line in web_py_lines:

            if line.strip() == "# ---addmap.py header marker---":
                web_py_new_lines.append("# ---addmap.py header marker---")
                web_py_new_lines.append(
                    "'" + map_name + "': {'name':'" + user_friendly_name + 
                    "', 'region_identifier':'" + region_identifier +
                    "', 'file':'" + map_gen_path + "'},")                
                found_header = True
            else:
                web_py_new_lines.append(line)

        if not found_header:
            print(
                "I was not able to find the appropriate markers that allow me to modify the handler.py file.")
            return

        with open("handler.py", "w") as handler_py_file:
            handler_py_file.write("\n".join(web_py_new_lines))


def gen_svg(map_gen_file_path, map_name, regions):
    print()
    print("I will now create {}.svg. You should edit this file to specify the default color and add labels for each region.".format(map_name))
    print("DO NOT RESIZE OR RESCALE THE CONTENTS OF THIS FILE! Accurate label placement depends on the scale calculated by this wizard.")
    print()

    try:
        with open(map_gen_file_path, "r") as map_gen_file:
            geo_json = json.load(map_gen_file)

    except Exception as e:
        print(repr(e))
        cleanup(map_name)
        return

    print("Writing {}.svg...".format(map_name))
    try:
        with open("{}/{}.svg".format(os.environ["CARTOGRAM_DATA_DIR"], map_name), "w") as svg_file:
            try:
                max_x = geo_json["bbox"][2]
                min_x = geo_json["bbox"][0]
                max_y = geo_json["bbox"][3]
                min_y = geo_json["bbox"][1]

                width = max_x - min_x
                height = max_y - min_y

                scale = 750.0/width
                
                width *= scale
                height *= scale
                
                def x_transform(x):
                    return (x - min_x)*scale
                
                def y_transform(y):
                    return (max_y - y)*scale
                
                svg_file.write("""<svg version="1.1"
     baseProfile="full"
     width="{}" height="{}"
     xmlns="http://www.w3.org/2000/svg"
     xmlns:gocart="https://go-cart.io">
""".format(round(width,2), round(height, 2)))

                next_polygon_id = 1

                for feature in geo_json["features"]:
                    if feature["geometry"]["type"] == "Polygon":
                        polygon_path = None
                        hole_paths = []
                        polygon_id = next_polygon_id

                        for path in feature["geometry"]["coordinates"]:
                            next_polygon_id += 1

                            if polygon_path == None:
                                polygon_path = " ".join(list(map(lambda coord: "{} {}".format(round(x_transform(coord[0]), 3), round(y_transform(coord[1]), 3)), path)))                                
                            else:
                                hole_path = " ".join(list(map(lambda coord: "{} {}".format(round(x_transform(coord[0]), 3), round(y_transform(coord[1]), 3)), path)))
                                hole_paths.append("M {} z".format(hole_path))
                        
                        path = "M {} z {}".format(polygon_path, " ".join(hole_paths))
                        region = find_region_by_id(regions, feature["properties"]["cartogram_id"])
                        svg_file.write(
                            '<path gocart:regionname="{}" d="{}" id="polygon-{}" class="region-{}" fill="#aaaaaa" stroke="#000000" stroke-width="1"/>\n'.format(
                                region["name"], path, polygon_id, feature["properties"]["cartogram_id"]))
                        
                    elif feature["geometry"]["type"] == "MultiPolygon":
                        for polygon in feature["geometry"]["coordinates"]:
                            polygon_path = None
                            hole_paths = []
                            polygon_id = next_polygon_id

                            for path in polygon:
                                next_polygon_id += 1

                                if polygon_path == None:
                                    polygon_path = " ".join(list(map(lambda coord: "{} {}".format(round(x_transform(coord[0]), 3), round(y_transform(coord[1]), 3)), path)))  
                                else:
                                    hole_path = " ".join(list(map(lambda coord: "{} {}".format(round(x_transform(coord[0]), 3), round(y_transform(coord[1]), 3)), path)))
                                    hole_paths.append("M {} z".format(hole_path))
                            
                            path = "M {} z {}".format(polygon_path, " ".join(hole_paths))
                            print(feature["properties"]["cartogram_id"])
                            region = find_region_by_id(regions, feature["properties"]["cartogram_id"])
                            print(repr(region))
                            svg_file.write('<path gocart:regionname="{}" d="{}" id="polygon-{}" class="region-{}" fill="#aaaaaa" stroke="#000000" stroke-width="1"/>\n'.format(region["name"], path, polygon_id, feature["properties"]["cartogram_id"]))

                    else:
                        raise Exception("Unsupported feature type {}.".format(feature["geometry"]["type"]))
                
                svg_file.write("</svg>")
            
            except Exception as e:
                print(repr(e))
                cleanup(map_name)
                return
    except Exception as e:
        print(repr(e))
        cleanup(map_name)
        return
    
    print("Writing static/cartdata/{}/labels.json...".format(map_name))
    try:
        with open("static/cartdata/{}/labels.json".format(map_name), "w") as labels_json_file:
            try:
                labels_json_file.write('{{"scale_x": {0}, "scale_y": {0}, "labels": [], "lines": []}}'.format(scale))
            except Exception as e:
                print(repr(e))
                cleanup(map_name)
                return
    except Exception as e:
        print(repr(e))
        cleanup(map_name)
        return

def update_by_svg(map_name):   
    if not os.path.exists("static/cartdata/{}".format(map_name)):
        print("Error: It looks like a map with the name '{}' doesn't exist (I didn't find static/cartdata/{}).".format(map_name, map_name))
        return
    
    svg_file_path = "{}/{}.svg".format(os.environ["CARTOGRAM_DATA_DIR"], map_name)
    if not os.path.exists(svg_file_path):
        print("Error: It looks like {}.svg doesn't exist. I need this file to add color information to your new map.")
        return

    try:
        print()
        print("I will now parse {}.svg to learn each map region's default color.".format(map_name))
        new_colors, colors_by_name = svg2color.convert(svg_file_path, "static/cartdata/{}/colors.json".format(map_name))
        print("Writing static/cartdata/{}/colors.json...".format(map_name))
        with open("static/cartdata/{}/colors.json".format(map_name), "w") as colors_json_file:
            json.dump(new_colors, colors_json_file)
        # print(repr(new_colors))
        # print(repr(colors_by_name))
    
        print()
        print("I will now parse {}.svg for label information.".format(map_name))
        with open("static/cartdata/{}/labels.json".format(map_name), "r") as labels_json_file:
            labels_json = json.load(labels_json_file)
            labels_scale_x = labels_json['scale_x']
            labels_scale_y = labels_json['scale_y']    
        labels = svg2labels.convert(svg_file_path, labels_scale_x, labels_scale_y)
        print("Writing static/cartdata/{}/labels.json...".format(map_name))
        with open("static/cartdata/{}/labels.json".format(map_name), "w") as labels_json_file:
            json.dump(labels, labels_json_file)
    
        print()
        print("I will now parse {}.svg for configuration information.".format(map_name))        
        config = svg2config.convert(svg_file_path)
        print("Writing static/cartdata/{}/config.json...".format(map_name))
        with open("static/cartdata/{}/config.json".format(map_name), "w") as colors_json_file:
            json.dump(config, colors_json_file)
    
        print("Updating map pack in static/cartdata/{}/mappack.json...".format(map_name))
        with open("static/cartdata/{}/mappack.json".format(map_name), "r") as mappack_json_file:
            mappack_json = json.load(mappack_json_file)
        mappack_json["colors"] = new_colors
        mappack_json["labels"] = labels
        mappack_json["config"]["dont_draw"] = config["dont_draw"]
        mappack_json["config"]["elevate"] = config["elevate"]
        with open("static/cartdata/{}/mappack.json".format(map_name), "w") as mappack_json_file:
            json.dump(mappack_json, mappack_json_file)


    except Exception as e:
        print(repr(e))
        return
    
    print()
    print("All done!")
    print()


print_welcome()

if len(sys.argv) < 3:
    print_usage()
    sys.exit(1)

if sys.argv[1] == "init":
    init(sys.argv[2])
elif sys.argv[1] == "batch":
    ids = sys.argv[2].split(":")
    for x in range(int(ids[0]), int(ids[1]) + 1):
        try:
            init("test" + str(x))
        except Exception as e:
            print(e)
elif sys.argv[1] == "update":
    update_by_svg(sys.argv[2])            
elif sys.argv[1] == "cleanup":
    cleanup(sys.argv[2])
else:
    print_usage()
    sys.exit(1)
