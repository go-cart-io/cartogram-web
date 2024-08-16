import json
import handler
import os
import pandas as pd
from shapely.geometry import shape

def migrate_geojson(handler_key, in_path, out_path=None):
    output_data = {}
    with open(in_path, 'r') as file:
        json_data = json.load(file)

        for feature in json_data["features"]:
            geom = shape(feature["geometry"])
            point = geom.representative_point()
            feature['properties']['label'] = {'x': point.x, 'y': point.y}

        if 'tooltip' in json_data:
            if out_path is None:
                if (json_data['tooltip']['label'] == "Land Area"):
                    out_path = 'static/cartdata/{}/original.json'.format(handler_key)
                else:
                    out_path = 'static/cartdata/{}/{}.json'.format(handler_key, json_data['tooltip']['label'])
            label_with_unit = json_data['tooltip']['label'] + ' (' + json_data['tooltip']['unit'] + ')'

            for feature in json_data['features']:
                feature["id"] = feature['properties']['cartogram_id']
                feature['properties']['name'] = json_data['tooltip']['data']["id_{}".format(feature["id"])]["name"]

            for key, value in json_data['tooltip']['data'].items():
                state_name = value["name"]
                state_value = value["value"]
                output_data[state_name] = state_value

            del json_data['tooltip']
        else:
            print("Cann't find tooltip for {}".format(handler_key))
            return


    if out_path is not None:
        with open(out_path, 'w') as openfile:
            json.dump(json_data, openfile)

    return label_with_unit, output_data

def migrate():    
    for handler_key in handler.cartogram_handlers:    
    #     print("Migrate geojson and csv data....")
    #     with open('static/cartdata/{}/abbreviations.json'.format(handler_key), 'r') as file:
    #         abbr_data = json.load(file)

    #     input_file = 'static/cartdata/{}/template.csv'.format(handler_key)
    #     df = pd.read_csv(input_file)
        
    #     land_label, land_data = migrate_geojson(handler_key, 'static/cartdata/{}/original.json'.format(handler_key))
    #     pop_label, pop_data = migrate_geojson(handler_key, 'static/cartdata/{}/population.json'.format(handler_key))

    #     newdf = pd.DataFrame(columns=["Region", "Abbreviation", "Color", land_label, pop_label])
    #     for index, row in df.iterrows():
    #         name = row.iloc[0]
    #         newdf.loc[len(newdf.index)] = [name, abbr_data[name], row.iloc[1], land_data[name], pop_data[name]] 

    #     output_file = 'static/cartdata/{}/data.csv'.format(handler_key)
    #     newdf.to_csv(output_file, index=False)

        # print("Migrate gen files....")
        # gen_path = cartogram_handler.get_gen_file(handler_key)
        # migrate_geojson(handler_key, gen_path, gen_path)

        print("Delete unused files....")
        for file in ['abbreviations', 'colors', 'config', 'griddocument', 'mappack', 'labels']:
            file_path = 'static/cartdata/{}/{}.json'.format(handler_key, file)
            if os.path.exists(file_path):
                os.remove(file_path)

        file_path = 'static/cartdata/{}/template.csv'.format(handler_key)
        if os.path.exists(file_path):
            os.remove(file_path)

        print(handler_key)

migrate()