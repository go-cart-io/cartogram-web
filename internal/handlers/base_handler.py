import re

class BaseCartogramHandler:

    def get_name(self):
        raise NotImplementedError("This function must be implemented.")

    def get_gen_file(self):
        raise NotImplementedError("This function must be implemented.")
    
    def get_region_id(self, name):
        raise NotImplementedError("This function must be implemented.")
    
    def remove_holes(self):
        return False
    
    def expect_geojson_output(self):
        return False

    def selector_names(self):
        return [self.get_name()]

    
    # This function takes a CSVReader and returns a tuple containing:
    #   
    #   1. The areas string
    #   2. Color values for each region
    #   3. Tooltip data for each region
    def get_area_string_and_colors(self, data):
        colName = 0
        colColor = 1
        colValue = 2 # Starting column of data

        datastring = "cartogram_id,Region Data,Region Name,Inset\n"
        colorJson = {}
        tooltip = {"data":{}}

        for rowId, region in data["values"]["items"].items():
            # Validate values
            region[colName] = region[colName].replace(",", "")
            if region[colValue] is not None:
                float(region[colValue])
            else:
                region[colValue] = "NA"
            if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', region[colColor]):
                raise ValueError("The color data was invaild.")
                   
            regionId = self.get_region_id(region[colName])
            datastring = datastring + '{},{},{},\n'.format(regionId, region[colValue], region[colName])
            colorJson['id_' + regionId] = region[colColor]
            tooltip['data']['id_' + regionId] = {'name': region[colName], 'value': region[colValue]}

        m = re.match(r'(.+)\s?\((.+)\)$', data["values"]["fields"][colValue]["label"])
        if m:
            tooltip['label'] = m.group(1)
            tooltip['unit'] = m.group(2)
        else:
            tooltip['label'] = data['values']['fields'][colValue]['label']
        
        return datastring, colorJson, tooltip


    
