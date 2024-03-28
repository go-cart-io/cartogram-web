import json
import settings
import handler

def migrate():
    handler_metadata = {}
    for key in handler.cartogram_handlers:    
        gen_file = '{}/{}'.format(settings.CARTOGRAM_DATA_DIR, handler.cartogram_handlers[key]['file'])     
        with open(gen_file, 'r') as openfile: 
            handler_data = json.load(openfile)    
        
        handler_metadata = handler.cartogram_handlers[key]
        handler_metadata['regions'] = handler_data['regions']

        del handler_data['regions']
        with open(gen_file, 'w') as openfile:
            json.dump(handler_data, openfile)

        print("'" + key + "': " + str(handler_metadata) + ",")

migrate()