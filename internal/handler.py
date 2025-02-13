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
            sub_cartogram_handlers[key] = {'name': value['name'], 'regions': value['regions']}

        return dict(sorted(sub_cartogram_handlers.items(), key=lambda item: item[1]['name']))

    def get_name(self, handler):
        return cartogram_handlers[handler]['name']

    def get_gen_file(self, handler, string_key = ''):
        if handler == 'custom':
            return f"./static/userdata/{string_key}/Input.json"
        else:
            return f'./static/cartdata/{handler}/Input.json'
    
    def remove_holes(self):
        return False
    
    def expect_geojson_output(self):
        return True