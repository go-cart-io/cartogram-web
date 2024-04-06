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
        return '{}/{}'.format(settings.CARTOGRAM_DATA_DIR, cartogram_handlers[handler]['file'])  
    
    def remove_holes(self):
        return False
    
    def expect_geojson_output(self):
        return True
        
    # This function takes a CSVReader and returns a tuple containing:
    #   
    #   1. The areas string
    #   2. Color values for each region
    #   3. Tooltip data for each region
    def get_area_string_and_colors(self, handler, data):
        if handler not in cartogram_handlers:
            raise KeyError('The handler was invaild.')

        with open(self.get_gen_file(handler), 'r') as openfile: 
            handler_data = json.load(openfile)    

        colName = 0
        colColor = 1
        colValue = 2 # Starting column of data

        datastring = 'cartogram_id,Region Data,Region Name,Inset\n'
        colorJson = {}
        tooltip = {'data':{}}

        for rowId, region in data['values']['items'].items():
            # Validate values
            region[colName] = region[colName].replace(',', '')
            if region[colValue] is not None:
                float(region[colValue])
            else:
                region[colValue] = 'NA',
            if region[colColor] != '' and not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', region[colColor]):
                raise ValueError('The color data was invaild.')
                   
            regionId = cartogram_handlers[handler]['regions'][region[colName]]
            datastring = datastring + '{0},{1},{2},\n'.format(regionId, region[colValue], region[colName])
            colorJson['id_' + regionId] = region[colColor]
            tooltip['data']['id_' + regionId] = {'name': region[colName], 'value': region[colValue]}

        m = re.match(r'(.+)\s?\((.+)\)$', data['values']['fields'][colValue]['label'])
        if m:
            tooltip['label'] = m.group(1)
            tooltip['unit'] = m.group(2)
        else:
            tooltip['label'] = data['values']['fields'][colValue]['label']
        
        return datastring, colorJson, tooltip
    
