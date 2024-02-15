import re
import json
import settings

cartogram_handlers = {
'singaporePA': {'name':'Singapore (by Planning Area)', 'region_identifier':'Planning Area', 'file':'singaporePA_processedmap.json'},
'test4': {'name': 'test04-Demo', 'region_identifier':'Area', 'file':''},
'test6': {'name': 'test06-Train', 'region_identifier':'Area', 'file':''},
'test13': {'name': 'test13', 'region_identifier':'Area', 'file':''},
'test14': {'name': 'test14', 'region_identifier':'Area', 'file':''},
'test15': {'name': 'test15', 'region_identifier':'Area', 'file':''},
'test16': {'name': 'test16', 'region_identifier':'Area', 'file':''},
'test18': {'name': 'test18', 'region_identifier':'Area', 'file':''},
'test20': {'name': 'test20', 'region_identifier':'Area', 'file':''},
'test21': {'name': 'test21', 'region_identifier':'Area', 'file':''},
'test22': {'name': 'test22', 'region_identifier':'Area', 'file':''},
'test23': {'name': 'test23', 'region_identifier':'Area', 'file':''},
'test24': {'name': 'test24', 'region_identifier':'Area', 'file':''},
'test26': {'name': 'test26', 'region_identifier':'Area', 'file':''},
'test28': {'name': 'test28', 'region_identifier':'Area', 'file':''},
'test29': {'name': 'test29', 'region_identifier':'Area', 'file':''},
'test30': {'name': 'test30', 'region_identifier':'Area', 'file':''},
'test32': {'name': 'test32', 'region_identifier':'Area', 'file':''},
'test34': {'name': 'test34', 'region_identifier':'Area', 'file':''},
'test37': {'name': 'test37', 'region_identifier':'Area', 'file':''},
'test38': {'name': 'test38', 'region_identifier':'Area', 'file':''},
'test39': {'name': 'test39', 'region_identifier':'Area', 'file':''},
'test41': {'name': 'test41', 'region_identifier':'Area', 'file':''},
'test42': {'name': 'test42', 'region_identifier':'Area', 'file':''},
'test44': {'name': 'test44', 'region_identifier':'Area', 'file':''},
'test45': {'name': 'test45', 'region_identifier':'Area', 'file':''},
'test47': {'name': 'test47', 'region_identifier':'Area', 'file':''},
'test52': {'name': 'test52', 'region_identifier':'Area', 'file':''},
'test54': {'name': 'test54', 'region_identifier':'Area', 'file':''},
'test55': {'name': 'test55', 'region_identifier':'Area', 'file':''},
'test58': {'name': 'test58', 'region_identifier':'Area', 'file':''},
'test64': {'name': 'test64', 'region_identifier':'Area', 'file':''},
'test75': {'name': 'test75', 'region_identifier':'Area', 'file':''},
'test105': {'name': 'test105', 'region_identifier':'Area', 'file':''},
'test109': {'name': 'test109', 'region_identifier':'Area', 'file':''},
'test115': {'name': 'test115', 'region_identifier':'Area', 'file':''},
'test117': {'name': 'test117', 'region_identifier':'Area', 'file':''},
'test130': {'name': 'test130', 'region_identifier':'Area', 'file':''},
'test132': {'name': 'test132', 'region_identifier':'Area', 'file':''},
'test138': {'name': 'test138', 'region_identifier':'Area', 'file':''},
'test147': {'name': 'test147', 'region_identifier':'Area', 'file':''},
# DONOT remove or modify the below comment
# ---addmap.py header marker---
}

class CartogramHandler:
    def has_handler(self, handler):
        return handler in cartogram_handlers
    
    def get_sorted_handler_names(self):
        return cartogram_handlers

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
            if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', region[colColor]):
                raise ValueError('The color data was invaild.')
                   
            regionId = handler_data['regions'][region[colName]]
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
    
