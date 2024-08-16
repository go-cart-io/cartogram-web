import re
import json
import settings
from handler_metadata import cartogram_handlers 

class CartogramHandler:
    def has_handler(self, handler):
        return handler in cartogram_handlers
    
    def get_sorted_handler_names(self):
        sub_cartogram_handlers = {}
        for key, value in cartogram_handlers.items():
            sub_cartogram_handlers[key] = {'name': value['name'], 'region_identifier': value['region_identifier']}

        return dict(sorted(sub_cartogram_handlers.items(), key=lambda item: item[1]['name']))

    def get_name(self, handler):
        return cartogram_handlers[handler]['name']

    def get_gen_file(self, handler):
        return './static/cartdata/{}/original.json'.format(handler)  
    
    def remove_holes(self):
        return False
    
    def expect_geojson_output(self):
        return True
        
    # This function takes a CSVReader and returns a tuple containing:
    #   
    #   1. The areas string
    #   2. Color values for each region
    #   3. Tooltip data for each region
    def get_area_string_and_colors(self, data):
        colName = 0
        colColor = 2
        colValue = 4 # Starting column of data
       
        datacsv = 'Region,Abbreviation,Color,Land Area (km sq.),'
        m = re.match(r'(.+)\s?\((.+)\)$', data['values']['fields'][colValue]['label'])
        if m:
            name = m.group(1).strip()
            label = "{} ({})".format(name, m.group(2).strip())            
        else:
            name = label = data['values']['fields'][colValue]['label'].strip()
        datacsv = datacsv + label + '\n'

        datastring = 'name,Data,Color\n'
        for rowId, region in data['values']['items'].items():
            # Validate values
            region[colName] = region[colName].replace(',', '')
            if region[colValue] is not None:
                float(region[colValue])
            else:
                region[colValue] = 'NA',
            if region[colColor] != '' and not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', region[colColor]):
                raise ValueError('The color data was invaild.')
                   
            datastring = datastring + '{0},{1},{2}\n'.format(region[colName], region[colValue], region[colColor])
            datacsv = datacsv + '{0},{1},{2},{3},{4}\n'.format(region[0], region[1], region[2],region[3],region[4])        
        
        return datastring, datacsv, name
    
