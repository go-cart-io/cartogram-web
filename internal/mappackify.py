import sys
import json
import os

def mappackify(map_name, name_array = ['original', 'population']):

    mappack = {}

    with open("static/cartdata/{}/abbreviations.json".format(map_name), "r") as abbreviations_json:
        mappack['abbreviations'] = json.load(abbreviations_json)

    with open("static/cartdata/{}/colors.json".format(map_name), "r") as colors_json:
        mappack['colors'] = json.load(colors_json)

    with open("static/cartdata/{}/config.json".format(map_name), "r") as config_json:
        mappack['config'] = json.load(config_json)

    if os.path.exists("static/cartdata/{}/labels.json".format(map_name)):
        with open("static/cartdata/{}/labels.json".format(map_name), "r") as labels_json:
            mappack['labels'] = json.load(labels_json)

    for data_name in name_array:
        with open("static/cartdata/{}/{}.json".format(map_name, data_name), "r") as data_json:
            mappack[data_name] = json.load(data_json)
    
    with open("static/cartdata/{}/mappack.json".format(map_name), "w") as mappack_file:
        json.dump(mappack, mappack_file)

if __name__ == "__main__":

    mappackify(sys.argv[1])